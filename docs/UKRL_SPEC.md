# UKRL — Unified Knowledge Reconciliation Layer

## Objective
Reconcile claims from multiple connected environments without merging identities,
treating historical context as authority, or silently choosing between conflicting
canonical evidence.

## Current RUMBO source policy
- GitHub = canonical software source.
- Stele = canonical project-state source.
- Memco/shared memory = secondary reusable knowledge, not project-state authority.
- Chat history = context/evidence only, never authority.
- Provider identity/session/authorization remain separate.

## Claim model
Every imported fact is represented as subject + predicate + value + source +
observed_at + verification + authority + evidence_ref.

A claim without verification evidence cannot become an active canonical fact.

## Conflict policy
1. Verified canonical evidence outranks secondary evidence.
2. Two verified canonical sources that disagree produce CONFLICT.
3. CONFLICT is fail-closed; no automatic overwrite or merge.
4. Stale evidence produces STALE and cannot authorize current action.
5. A report is promotable only when all required resolutions are ACTIVE.

## Identity boundary
A claim such as "other ChatGPT account is accessible" cannot be promoted from
chat-history, memory, or a human assertion alone. It requires live provider
evidence from the appropriate connector. Knowledge reconciliation therefore
does not become credential or session reconciliation.

## Provenance
Each selected claim retains its evidence reference. The canonical digest binds
the resolved set deterministically so changes are detectable.

## Observed 2026-09-09
This account exposed GitHub, GitLab, Jira/Atlassian, Vercel, Brainbase, Stele,
Memco and ChatGPT Library surfaces. Desktop Commander had zero connected devices.
Ads Manager had no accessible accounts. OpenAI Platform exposed a personal
organization/project.

Stele KNOW-32 records a verified A/B attestation from GitHub Actions run
34199168922 for commit bdd87b12eee16561fa4c4d9af00dfde75eb79493. That evidence
supports repository/environment equivalence for A/B, not private access or
identity equality between separate ChatGPT accounts.

## Non-goals
UKRL does not copy credentials, cookies, sessions, OAuth tokens or API keys;
merge provider identities; claim access to another private ChatGPT account;
replace the existing RUMBO control plane; or claim production security certification.
