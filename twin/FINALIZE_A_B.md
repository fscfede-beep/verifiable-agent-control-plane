# Finalize A/B

Run this only after both environments have produced attestations:

```powershell
.\twin\finalize-twin.ps1 -A .\A.attestation.json -B .\B.attestation.json
```

The script does not modify either environment. It only runs the repository's fail-closed
attestation gate against the two supplied JSON files.

A result of PASS is the only accepted final state. Any other exit code is FAIL-CLOSED.
