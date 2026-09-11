"""Regression: endpoint-wide copy must not describe every action as SSH removal."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


@unittest.skipUnless(shutil.which('node'), 'Node is required by the deployment installer')
class ApprovalCopyTest(unittest.TestCase):
    def test_shared_copy_is_neutral_and_policy_rules_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            module = root/'node_modules/js-yaml'; module.mkdir(parents=True)
            # JSON is a YAML subset; isolate the config transform, not YAML parsing.
            (module/'index.js').write_text('exports.load=JSON.parse;exports.dump=JSON.stringify;')
            policy = dict(enabled=True,mode='default',allow=['read'],ask=['sg_apply'],deny=['sg_delete'],
                          reason='ASK - Review {tool}. Fixed server-owned context: environment=dev, action=remove_unrestricted_ssh, target=demo-security-group.',
                          hooks=[dict(matcher='sg_apply',module='/existing/sg.cjs')])
            file = root/'librechat.yaml'
            file.write_text(json.dumps(dict(endpoints=dict(agents=dict(toolApproval=policy)),mcpServers={})))
            command = ['node',str(Path(__file__).resolve().parents[1]/'integration/install-bulk-executor.cjs'),str(root)]
            subprocess.run(command,check=True,capture_output=True)
            first = file.read_text(); actual = json.loads(first)['endpoints']['agents']['toolApproval']
            self.assertNotIn('ssh',actual['reason'].lower()); self.assertNotIn('s3',actual['reason'].lower())
            self.assertEqual(actual['allow'],policy['allow']); self.assertEqual(actual['deny'],policy['deny'])
            self.assertIn('sg_apply',actual['ask']); self.assertIn(policy['hooks'][0],actual['hooks'])
            subprocess.run(command,check=True,capture_output=True)
            self.assertEqual(first,file.read_text())
