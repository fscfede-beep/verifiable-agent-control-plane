from pathlib import Path
import unittest

class TestFinalBootstrap(unittest.TestCase):
    def test_role_and_id_are_explicit(self):
        t=Path("twin/prepare-environment.ps1").read_text(encoding="utf-8")
        self.assertIn('ValidateSet("primary","twin")', t)
        self.assertIn('$env:TWIN_ENV_ROLE = $Role', t)
        self.assertIn('$env:TWIN_ENV_ID = $EnvironmentId', t)

    def test_no_secret_or_profile_copy(self):
        t=Path("twin/prepare-environment.ps1").read_text(encoding="utf-8")
        for x in ["cookies","browser profiles","OAuth tokens","session"]:
            self.assertNotIn(("Copy-Item" + ".*" + x), t)

if __name__=="__main__":
    unittest.main()
