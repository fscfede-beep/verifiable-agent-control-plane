# Live evidence pack

This is the final operator-side evidence collection path.

Run the full test suite first in Environment A:

```bash
python -m unittest discover -s tests -v
```

Then collect A:

```bash
python twin/collect_attestation.py --role primary --id A --out A.attestation.json --tests-result PASS
```

Run the full test suite first in Environment B:

```bash
python -m unittest discover -s tests -v
```

Then collect B:

```bash
python twin/collect_attestation.py --role twin --id B --out B.attestation.json --tests-result PASS
```

Then run:

```bash
python twin/attestation-gate.py A.attestation.json B.attestation.json
```

A PASS proves the required software/runtime attestation matches. It does not prove account
identity is the same. The account/session boundary remains independent.

The collector intentionally does not run the full test suite itself, because the suite can be
long-running and the evidence collector should remain deterministic and bounded. The test result
is supplied only after the suite was run separately.

Only share the two sanitized JSON files. Do not share browser profiles, cookies, tokens,
passwords, or session databases.
