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
                args = []
                agent_output = None
                if name == "prepare-inline-bulk.py":
                    agent_output = tmp / (name + ".agent.commands")
                    args = ["--agent-commands-file", str(agent_output)]
                result = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "scripts" / name),
                        "--manifest", str(tmp / "unused-manifest.json"),
                        "--gateway-state", str(tmp / "unused-gateway.json"),
                        "--commands-file", str(output),
                        "--update-code-only",
                        *args,
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
                if name == "prepare-inline-bulk.py":
                    self.assertLessEqual(agent_output.stat().st_size, 80_000, name + " agent")
                    agent_commands = agent_output.read_text()
                    self.assertIn("ISSUE191_AGENT_INTEGRATION_STAGED_NOT_STARTED", agent_commands)
                    self.assertIn("agents/compliance-agent-v1/src/compliance_agent_v1/live_s3_ssl.py", scripts_source(name))
                    self.assertIn("integration/s3-ssl-reject-only-approval-hook.cjs", scripts_source(name))
                    self.assertIn("integration/update-compliance-v1-agent.cjs", scripts_source(name))
                    self.assertIn("integration/rollback-compliance-v1-agent.cjs", scripts_source(name))
                    self.assertIn("bulk-runtime.before.tar.gz", commands)
                    self.assertIn("/opt/aws-secops/pilot_v1/native_decision_receipt.py", commands)
                self.assertIn("SSM_COMMAND_BYTES=", result.stdout)


def scripts_source(name: str) -> str:
    return (ROOT / "scripts" / name).read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
