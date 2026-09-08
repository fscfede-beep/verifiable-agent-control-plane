# Live evidence pack

This is the final operator-side evidence collection path.

Run once in Environment A:

```bash
python twin/collect_attestation.py --role primary --id A --out A.attestation.json
```

Run once in Environment B:

```bash
python twin/collect_attestation.py --role twin --id B --out B.attestation.json
```

Then run:

```bash
python twin/attestation-gate.py A.attestation.json B.attestation.json
```

A PASS proves the required software/runtime attestation matches. It does not prove account
identity is the same. The account/session boundary remains independent.

Only share the two sanitized JSON files. Do not share browser profiles, cookies, tokens,
passwords, or session databases.
