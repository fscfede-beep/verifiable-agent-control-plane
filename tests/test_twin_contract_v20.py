"""Adversarial checks: strict Twin JSON parsing and complete v4 evidence contract."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from test_twin_identity_failclosed import pair, verify, GATE, ROOT

def verify_bytes(a, b):
    with tempfile.TemporaryDirectory() as d:
        a_file, b_file = Path(d) / 'A.json', Path(d) / 'B.json'
        a_file.write_bytes(a)
        b_file.write_bytes(json.dumps(b).encode())
        p = subprocess.run([sys.executable, str(GATE), str(a_file), str(b_file)],
                           cwd=ROOT, capture_output=True, text=True, check=False)
        return p.returncode, p.stdout

class StrictTwinContract(unittest.TestCase):
    def test_reject_unknown_authorization_claim(self):
        a, b = pair()
        a["production_authorized"] = True
        code, output = verify(a, b)
        self.assertEqual(code, 2, output)
        self.assertIn("unexpected_fields", output)

    def test_reject_symmetric_unknown_claims(self):
        a, b = pair()
        a["signature_verified"] = b["signature_verified"] = True
        self.assertEqual(verify(a, b)[0], 2)

    def test_reject_nested_unknown_provenance(self):
        a, b = pair()
        b["provenance"] = {"verified": True}
        self.assertEqual(verify(a, b)[0], 2)

    def test_reject_numeric_overflow_in_undeclared_field(self):
        a, b = pair()
        for value in ("1e309", "-1e309"):
            with self.subTest(value=value):
                raw = json.dumps(a)[:-1] + ', "overflow": ' + value + '}'
                self.assertEqual(verify_bytes(raw.encode(), b)[0], 2)

    def test_reject_unpaired_surrogate_in_undeclared_field(self):
        a, b = pair()
        raw = json.dumps(a)[:-1] + ', "extra": "\\ud800"}'
        self.assertEqual(verify_bytes(raw.encode(), b)[0], 2)

    def test_valid_v4_contract_passes(self):
        a, b = pair()
        code, output = verify(a, b)
        self.assertEqual(code, 0, output)
        self.assertIn('"mismatches": {}', output)

    def test_duplicate_pass_rejected(self):
        a, b = pair()
        raw = json.dumps(a).replace('"tests": "PASS"', '"tests": "FAIL", "tests": "PASS"')
        self.assertEqual(verify_bytes(raw.encode(), b)[0], 2)

    def test_duplicate_nested_key_rejected(self):
        a, b = pair()
        a['unexpected'] = {'x': 1}
        raw = json.dumps(a).replace('"x": 1', '"x": 0, "x": 1')
        self.assertEqual(verify_bytes(raw.encode(), b)[0], 2)

    def test_nonstandard_json_rejected(self):
        a, b = pair()
        for invalid in ('NaN', 'Infinity', '-Infinity'):
            with self.subTest(invalid=invalid):
                raw = json.dumps(a).replace('"tests": "PASS"', '"unknown": '+invalid+', "tests": "PASS"')
                self.assertEqual(verify_bytes(raw.encode(), b)[0], 2)

    def test_omitted_fields_rejected(self):
        for field in ('branch', 'runtime_version', 'tests_command', 'twin_bridge_sha256'):
            with self.subTest(field=field):
                a, b = pair()
                a.pop(field)
                self.assertEqual(verify(a, b)[0], 2)

    def test_wrong_critical_values_rejected(self):
        bad_values = (
            ('runtime_version', '3.10.0'),
            ('tests_command', 'echo OK'),
            ('twin_spec_digest', 'INVALID'),
            ('commit', 'invalid'),
            ('platform', True),
            ('branch', 12),
        )
        for key, value in bad_values:
            with self.subTest(field=key):
                a, b = pair()
                a[key] = b[key] = value
                self.assertEqual(verify(a, b)[0], 2)

    def test_divergent_policy_rejected(self):
        a, b = pair()
        b['tool_policy_digest'] = '9' * 64
        self.assertNotEqual(verify(a, b)[0], 0)

    def test_divergent_branch_rejected(self):
        a, b = pair()
        b['branch'] = 'different'
        self.assertNotEqual(verify(a, b)[0], 0)

    def test_nonobject_json_rejected(self):
        _, b = pair()
        self.assertEqual(verify_bytes(b'[]', b)[0], 2)

    def test_failure_and_unclean_rejected(self):
        a, b = pair()
        a['tests'] = 'FAIL'
        self.assertEqual(verify(a, b)[0], 2)
        a, b = pair()
        b['working_tree_clean'] = False
        self.assertEqual(verify(a, b)[0], 2)

    def test_oversized_json_rejected(self):
        a, b = pair()
        a['pad'] = 'x' * 70000
        self.assertEqual(verify_bytes(json.dumps(a).encode(), b)[0], 2)

if __name__ == '__main__':
    unittest.main()
