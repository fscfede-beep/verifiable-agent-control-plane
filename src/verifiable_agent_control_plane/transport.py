from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TransportCandidate:
    """Explicit non-authoritative, non-production transport candidate identity."""

    node_id: str
    status: str = field(default="CANDIDATE", init=False)
    is_authority: bool = field(default=False, init=False)
    is_production: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if not self.node_id or not self.node_id.strip():
            raise ValueError("node_id is required")
