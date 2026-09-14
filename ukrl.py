"""Unified Knowledge Reconciliation Layer (UKRL).
Dependency-free reference implementation for reconciling claims from multiple work
environments without conflating evidence, authority, identity, or time.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Iterable, Mapping, Sequence
import json

STATUS_ACTIVE = "active"
STATUS_CONFLICT = "conflict"
STATUS_STALE = "stale"
STATUS_UNVERIFIED = "unverified"

@dataclass(frozen=True)
class Claim:
    claim_id: str
    subject: str
    predicate: str
    value: str
    source: str
    observed_at: str
    verified: bool = False
    authority: str = "secondary"
    evidence_ref: str | None = None
    environment: str | None = None
    def observed_epoch(self) -> float:
        dt = datetime.fromisoformat(self.observed_at.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()

@dataclass(frozen=True)
class Resolution:
    subject: str
    predicate: str
    status: str
    selected: Claim | None
    conflicts: tuple[Claim, ...] = ()
    rationale: tuple[str, ...] = ()

@dataclass
class ReconciliationReport:
    generated_at: str
    resolutions: list[Resolution] = field(default_factory=list)
    anomalies: list[str] = field(default_factory=list)
    @property
    def pass_count(self) -> int:
        return sum(r.status == STATUS_ACTIVE for r in self.resolutions)
    @property
    def fail_count(self) -> int:
        return sum(r.status != STATUS_ACTIVE for r in self.resolutions)
    def canonical_digest(self) -> str:
        payload = []
        for r in sorted(self.resolutions, key=lambda x: (x.subject, x.predicate)):
            payload.append({
                "subject": r.subject,
                "predicate": r.predicate,
                "status": r.status,
                "selected": None if r.selected is None else r.selected.__dict__,
                "conflicts": [c.__dict__ for c in r.conflicts],
            })
        return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

class UKRL:
    def __init__(self, canonical_sources: Sequence[str], authority_rank: Mapping[str, int] | None = None):
        self.canonical_sources = tuple(canonical_sources)
        self.authority_rank = dict(authority_rank or {"canonical": 3, "verified": 2, "secondary": 1})

    def reconcile(self, claims: Iterable[Claim], now: str | None = None, max_age_days: int = 30) -> ReconciliationReport:
        claims = list(claims)
        generated_at = now or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        now_epoch = datetime.fromisoformat(generated_at.replace("Z", "+00:00")).timestamp()
        groups: dict[tuple[str, str], list[Claim]] = {}
        anomalies: list[str] = []
        for c in claims:
            if c.authority not in self.authority_rank:
                anomalies.append(f"unknown-authority:{c.claim_id}:{c.authority}")
            if c.verified and not c.evidence_ref:
                anomalies.append(f"verified-without-evidence:{c.claim_id}")
            age_days = max(0.0, (now_epoch - c.observed_epoch()) / 86400.0)
            if age_days > max_age_days:
                anomalies.append(f"stale:{c.claim_id}:{age_days:.1f}d")
            groups.setdefault((c.subject, c.predicate), []).append(c)

        resolutions: list[Resolution] = []
        for (subject, predicate), bucket in sorted(groups.items()):
            values = {c.value for c in bucket}
            if len(values) > 1:
                canonical_verified = [
                    c for c in bucket
                    if c.source in self.canonical_sources and c.verified and bool(c.evidence_ref)
                ]
                canonical_values = {c.value for c in canonical_verified}
                if len(canonical_values) == 1:
                    selected = max(
                        canonical_verified,
                        key=lambda c: (self.authority_rank.get(c.authority, 0), c.observed_epoch()),
                    )
                    conflicts = tuple(c for c in bucket if c.claim_id != selected.claim_id and c.value != selected.value)
                    resolutions.append(Resolution(
                        subject, predicate, STATUS_ACTIVE, selected, conflicts,
                        ("verified-canonical-source-resolves-secondary-disagreement",),
                    ))
                else:
                    resolutions.append(Resolution(
                        subject, predicate, STATUS_CONFLICT, None, tuple(bucket),
                        ("no-single-verified-canonical-value",),
                    ))
                continue

            candidate = max(
                bucket,
                key=lambda c: (self.authority_rank.get(c.authority, 0), c.verified, c.observed_epoch()),
            )
            age_days = max(0.0, (now_epoch - candidate.observed_epoch()) / 86400.0)
            if age_days > max_age_days:
                resolutions.append(Resolution(subject, predicate, STATUS_STALE, None, tuple(bucket), ("only-evidence-is-stale",)))
            elif candidate.verified and candidate.evidence_ref:
                resolutions.append(Resolution(subject, predicate, STATUS_ACTIVE, candidate, (), ("verified-evidence-selected",)))
            else:
                resolutions.append(Resolution(subject, predicate, STATUS_UNVERIFIED, None, tuple(bucket), ("claim-lacks-verification-evidence",)))

        return ReconciliationReport(generated_at, resolutions, anomalies)

def assert_fail_closed(report: ReconciliationReport) -> None:
    bad = [r for r in report.resolutions if r.status != STATUS_ACTIVE]
    if bad:
        compact = "; ".join(f"{r.subject}.{r.predicate}={r.status}" for r in bad)
        raise RuntimeError(f"UKRL_FAIL_CLOSED: {compact}")
