# Changelog

Notable public changes to the Verifiable Agent Control Plane are recorded here.

## [0.2.0] - 2026-09-03

### Added
- installable `verifiable-agent-control-plane` package using the standard setuptools build interface;
- canonical `verifiable_agent_control_plane` import plus legacy `verifiable_control_plane` compatibility shim;
- package-surface regression coverage and outside-checkout import verification;
- release wheel asset and `SHA256SUMS.txt` for the exact uploaded file.

### Verified
- release tag `v0.2.0` points to `ed3bb2684743376fdf2769ee378ca614c913e3d4`;
- Python 3.11 / 3.12 / 3.13 CI passes source installation, the 16-test suite, and outside-checkout import verification;
- uploaded wheel SHA-256 is `3632d8325c6306b60bbbfeebd43dd3153f4dce8d99c5cbcc4c57d0923a770781`.

### Boundaries
- the checksum identifies the uploaded wheel only; bit-for-bit rebuild reproducibility is not claimed;
- the package is not published to PyPI;
- no open-source license has been selected.

## [0.1.0] - 2026-09-03

Initial public reference release with fail-closed execution, deterministic revalidation, effect readback, receipt-chain verification, replay prevention, and Python 3.11 / 3.12 / 3.13 CI.