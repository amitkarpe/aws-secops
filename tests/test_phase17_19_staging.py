import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class StagingPayloadTests(unittest.TestCase):
    def test_update_code_only_payloads_fit_ssm_budget(self):
        scripts = ["prepare-sg-compliance.py", "prepare-inline-bulk.py"]
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            for name in scripts:
                output = tmp / (name + ".commands")
                result = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "scripts" / name),
                        "--manifest", str(tmp / "unused-manifest.json"),
                        "--gateway-state", str(tmp / "unused-gateway.json"),
                        "--commands-file", str(output),
                        "--update-code-only",
                    ],
                    cwd=ROOT,
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self.assertLessEqual(output.stat().st_size, 80_000, name)
                commands = output.read_text()
                self.assertIn("sha256sum -c", commands)
                self.assertIn("STAGED_NOT_STARTED", commands)
                self.assertIn("SSM_COMMAND_BYTES=", result.stdout)


if __name__ == "__main__":
    unittest.main()
