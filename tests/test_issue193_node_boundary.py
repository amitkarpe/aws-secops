from pathlib import Path
import subprocess
import unittest


class NativeDecisionNodeBoundaryTests(unittest.TestCase):
    def test_native_adapter_contract(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            ["node", "--test", str(root / "tests" / "issue193_native_decision_receipt.test.cjs")],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_issue191_authenticated_runner_contract(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            ["node", "--test", str(root / "tests" / "issue191_browser_e2e.test.cjs")],
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
