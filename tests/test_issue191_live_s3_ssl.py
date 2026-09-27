from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "agents" / "compliance-agent-v1" / "src"))

from compliance_agent_v1.live_s3_ssl import AccountBinding, ALIASES, LiveS3SslEvidence, prepare_reject  # noqa: E402


class FakeClient:
    def __init__(self, account_id, policies):
        self.account_id = account_id
        self.policies = policies

    def caller_account(self):
        return self.account_id

    def list_bucket_names(self):
        return list(self.policies)

    def bucket_policy(self, bucket):
        value = self.policies[bucket]
        if isinstance(value, Exception):
            raise value
        return value


class LiveS3SslTests(unittest.TestCase):
    def test_exact_lab_identity_fixed_read_and_public_digest(self):
        bindings = tuple(AccountBinding(alias, str(index) * 12) for index, alias in enumerate(ALIASES, start=1))
        clients = {
            binding.alias: FakeClient(binding.account_id, {
                f"private-{binding.alias}": Exception("NoSuchBucketPolicy")
            }) for binding in bindings
        }
        value = LiveS3SslEvidence(bindings, lambda binding: clients[binding.alias]).collect()
        self.assertEqual([row["alias"] for row in value["accounts"]], list(ALIASES))
        self.assertTrue(all(row["identity_verified"] for row in value["accounts"]))
        self.assertTrue(all(row["status_counts"]["NON_COMPLIANT"] == 1 for row in value["accounts"]))
        self.assertEqual((value["control"], value["region"], value["aws_writes"], value["raw_identifiers_emitted"]), ("s3_ssl", "ap-southeast-1", 0, False))
        self.assertNotIn("private-lab-dev", str(value))

    def test_account_mismatch_fails_closed(self):
        bindings = tuple(AccountBinding(alias, str(index) * 12) for index, alias in enumerate(ALIASES, start=1))
        clients = {binding.alias: FakeClient("9" * 12, {}) for binding in bindings}
        value = LiveS3SslEvidence(bindings, lambda binding: clients[binding.alias]).collect()
        self.assertTrue(all(row["state"] == "UNAVAILABLE" for row in value["accounts"]))
        self.assertEqual(value["aws_writes"], 0)

    def test_alias_set_cannot_be_widened_or_reordered(self):
        bindings = (AccountBinding("lab-dev", "1" * 12),)
        with self.assertRaisesRegex(ValueError, "exact registered"):
            LiveS3SslEvidence(bindings, lambda _binding: FakeClient("1" * 12, {}))

    def test_exact_prepare_reject_zero_dispatch_and_audit(self):
        bindings = tuple(AccountBinding(alias, str(index) * 12) for index, alias in enumerate(ALIASES, start=1))
        clients = {binding.alias: FakeClient(binding.account_id, {f"bucket-{binding.alias}": Exception("NoSuchBucketPolicy")}) for binding in bindings}
        evidence = LiveS3SslEvidence(bindings, lambda binding: clients[binding.alias]).collect()
        proof = prepare_reject(evidence, alias="lab-dev")
        self.assertEqual((proof["control"], proof["result"]["decision"], proof["result"]["attempted"], proof["result"]["aws_mutation"], proof["aws_writes"], proof["remediation_dispatches"]), ("s3_ssl", "REJECTED", 0, False, 0, 0))
        self.assertEqual(proof["audit"]["event_types"][-2:], ["PREVIEW_FROZEN", "NATIVE_APPROVAL_DECISION"])


if __name__ == "__main__":
    unittest.main()
