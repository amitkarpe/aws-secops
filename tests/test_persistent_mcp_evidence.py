import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "agents" / "compliance-agent-v1" / "src"
sys.path.insert(0, str(SRC))

from compliance_agent_v1.evidence_provider import (  # noqa: E402
    AccountScope,
    EvidenceQuery,
    PersistentMcpEvidenceProvider,
    TransportPage,
    persistent_mcp_enabled,
)


FIXTURES = ROOT / "tests" / "fixtures" / "persistent_mcp"
NOW = "2026-09-22T12:00:00Z"


def fixture(name):
    return json.loads((FIXTURES / f"{name}.json").read_text())["items"]


class FixtureTransport:
    def __init__(self, pages):
        self.pages = list(pages)
        self.calls = []

    def read_page(self, query, *, next_token, limit):
        self.calls.append((query, next_token, limit))
        value = self.pages.pop(0)
        if isinstance(value, Exception):
            raise value
        return value


class PersistentMcpEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.account_id = "0" * 11 + "1"
        self.scope = AccountScope("lab-dev", self.account_id)

    def collect(self, query, items, **page_values):
        page = TransportPage(
            verified_account_id=self.account_id,
            collected_at=NOW,
            items=items,
            **page_values,
        )
        return PersistentMcpEvidenceProvider(FixtureTransport([page]), self.scope).collect(query)

    def assert_common(self, value, query):
        self.assertEqual(value["query"], query.value)
        self.assertEqual(value["source"]["provider"], "persistent-aws-mcp")
        self.assertEqual(value["account"]["alias"], "lab-dev")
        self.assertTrue(value["account"]["identity_verified"])
        self.assertTrue(value["account"]["public_ref"].startswith("acct-"))
        self.assertNotIn(self.account_id, json.dumps(value))
        self.assertTrue(value["read_only"])
        self.assertFalse(value["mutation"])

    def test_config_contract(self):
        value = self.collect(EvidenceQuery.CONFIG_COMPLIANCE, fixture("config"))
        self.assert_common(value, EvidenceQuery.CONFIG_COMPLIANCE)
        self.assertEqual(value["state"], "AVAILABLE")
        self.assertEqual(value["item_count"], 2)
        self.assertEqual({row["status"] for row in value["items"]}, {"COMPLIANT", "NON_COMPLIANT"})

    def test_s3_contract(self):
        value = self.collect(EvidenceQuery.S3_POSTURE, fixture("s3"))
        self.assert_common(value, EvidenceQuery.S3_POSTURE)
        self.assertEqual(sum(not row["all_public_access_blocked"] for row in value["items"]), 1)

    def test_security_group_contract(self):
        value = self.collect(EvidenceQuery.SECURITY_GROUP_EXPOSURE, fixture("security_groups"))
        self.assert_common(value, EvidenceQuery.SECURITY_GROUP_EXPOSURE)
        self.assertEqual(sum(row["unrestricted_ssh"] for row in value["items"]), 1)

    def test_inspector_contract(self):
        value = self.collect(EvidenceQuery.INSPECTOR_SUMMARY, fixture("inspector"))
        self.assert_common(value, EvidenceQuery.INSPECTOR_SUMMARY)
        self.assertEqual(value["items"][0]["finding_counts"]["HIGH"], 1)
        self.assertEqual(value["items"][0]["finding_counts"]["CRITICAL"], 0)

    def test_account_mismatch_fails_closed_without_leaking_identity(self):
        page = TransportPage("9" * 12, NOW, fixture("config"))
        value = PersistentMcpEvidenceProvider(FixtureTransport([page]), self.scope).collect(
            EvidenceQuery.CONFIG_COMPLIANCE
        )
        self.assertEqual(value["state"], "UNAVAILABLE")
        self.assertEqual(value["reason"], "ACCOUNT_MISMATCH")
        self.assertFalse(value["account"]["identity_verified"])
        self.assertEqual(value["items"], [])
        self.assertNotIn("9" * 12, json.dumps(value))
        self.assertFalse(value["mutation"])

    def test_pagination_is_bounded_and_partial_is_honest(self):
        pages = []
        for index, count in enumerate((40, 40, 20)):
            pages.append(TransportPage(
                self.account_id,
                NOW,
                [{"resource_ref": f"bucket-ref-{index}-{item}", "all_public_access_blocked": True} for item in range(count)],
                next_token=f"page-{index + 1}",
            ))
        transport = FixtureTransport(pages)
        value = PersistentMcpEvidenceProvider(transport, self.scope).collect(EvidenceQuery.S3_POSTURE)
        self.assertEqual(value["state"], "PARTIAL")
        self.assertTrue(value["partial"])
        self.assertEqual(value["item_count"], 100)
        self.assertEqual(len(transport.calls), 3)

    def test_transport_failure_and_sensitive_material_are_unavailable(self):
        failed = PersistentMcpEvidenceProvider(
            FixtureTransport([RuntimeError("private transport detail")]), self.scope
        ).collect(EvidenceQuery.INSPECTOR_SUMMARY)
        self.assertEqual(failed["reason"], "TRANSPORT_UNAVAILABLE")
        self.assertNotIn("private transport detail", json.dumps(failed))

        page = TransportPage(
            self.account_id,
            NOW,
            [{"resource_ref": "bucket-ref", "all_public_access_blocked": True, "session_token": "blocked"}],
        )
        rejected = PersistentMcpEvidenceProvider(FixtureTransport([page]), self.scope).collect(
            EvidenceQuery.S3_POSTURE
        )
        self.assertEqual(rejected["reason"], "SENSITIVE_MATERIAL_REJECTED")
        self.assertNotIn("blocked", json.dumps(rejected))

    def test_query_surface_is_fixed_and_live_gate_defaults_off(self):
        provider = PersistentMcpEvidenceProvider(FixtureTransport([]), self.scope)
        with self.assertRaisesRegex(ValueError, "unsupported evidence query"):
            provider.collect("aws___run_script")
        self.assertFalse(persistent_mcp_enabled({}))
        self.assertFalse(persistent_mcp_enabled({"SECOPS_PERSISTENT_MCP_EVIDENCE_ENABLED": "true"}))
        self.assertTrue(persistent_mcp_enabled({"SECOPS_PERSISTENT_MCP_EVIDENCE_ENABLED": "1"}))

    def test_current_v1_read_path_and_model_tool_surface_are_unchanged(self):
        agent = (SRC / "compliance_agent_v1" / "agent.py").read_text()
        mcp_server = (SRC / "compliance_agent_v1" / "mcp_server.py").read_text()
        integration = json.loads((ROOT / "integration" / "compliance-agent-v1.json").read_text())
        self.assertIn("from .config_backend import current_evidence", agent)
        self.assertNotIn("evidence_provider", agent)
        self.assertNotIn("PersistentMcpEvidenceProvider", mcp_server)
        self.assertNotIn("persistent_mcp", json.dumps(integration).lower())

    def test_machine_readable_schema_has_closed_read_only_contract(self):
        schema = json.loads(
            (ROOT / "agents" / "compliance-agent-v1" / "evidence-provider.schema.json").read_text()
        )
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["read_only"]["const"], True)
        self.assertEqual(schema["properties"]["mutation"]["const"], False)
        self.assertEqual(set(schema["properties"]["query"]["enum"]), {query.value for query in EvidenceQuery})


if __name__ == "__main__":
    unittest.main()
