"""Retained-EC2 backend entrypoint using the host role, never copied AWS keys."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path("/opt/aws-secops")
PRIVATE = ROOT / ".runtime"


def main():
    os.umask(0o077)
    state = json.loads((PRIVATE / "pilot-state.json").read_text())
    if state["region"] != "ap-southeast-1":
        raise RuntimeError("unexpected runtime Region")
    os.environ.update(HOME=str(PRIVATE), AWS_PROFILE="amit", AWS_REGION="ap-southeast-1",
                      AWS_CONFIG_FILE=str(PRIVATE / "aws-config"),
                      PILOT_BACKLOG_FILE=str(PRIVATE / "backlog.json"),
                      PILOT_HARNESS_ARN=state["harnessArn"], PILOT_GATEWAY_URL=state["gatewayUrl"],
                      PILOT_SG_READ_TOOL=state["readToolName"], PILOT_SG_REMEDIATE_TOOL=state["remediationToolName"],
                      PILOT_S3_READ_TOOL=state["s3ToolName"])
    os.environ["PATH"] = str(ROOT / "cli/node_modules/.bin") + ":" + os.environ.get("PATH", "")
    (PRIVATE / "aws-config").write_text("[profile amit]\nregion = ap-southeast-1\n")
    # With no keys/credential process configured, the SDK/CLI resolves the EC2 role.
    identity = subprocess.run(["aws", "sts", "get-caller-identity", "--profile", "amit", "--region", "ap-southeast-1", "--query", "Account", "--output", "text"], capture_output=True, text=True, timeout=30)
    if identity.returncode or identity.stdout.strip() != state["accountId"]:
        raise RuntimeError("retained host identity mismatch; backend not started")
    os.chdir(ROOT)
    os.execv(sys.executable, [sys.executable, "-m", "pilot_v1.server", "--host", "127.0.0.1", "--port", "3340"])


if __name__ == "__main__":
    main()
