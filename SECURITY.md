# Security policy

## Scope

This repository is a small public reference implementation, not a production service.

Security-relevant reports include:
- bypasses of fail-closed decision or materialization rules;
- replay, receipt-chain, or transition-verification failures;
- unintended secret, credential, network, or filesystem access;
- cases where observed effects can diverge from verified receipts;
- GitHub Actions or release-integrity issues affecting published evidence.

## Report privately

Use GitHub's **Report a vulnerability** flow under the repository Security tab. Private vulnerability reporting is enabled for this repository.

Do not open a public issue for an undisclosed vulnerability. Include the affected commit or release, reproduction steps, expected versus observed behavior, impact, and the smallest practical proof of concept.

## Supported version

Security fixes target the latest published release and current `main`.

## Boundaries

This policy does not imply security certification, production hardening, third-party audit, or suitability for consequential deployment without independent review.
