"""The new bulk route must inherit the existing operator auth/origin boundary."""
import importlib.util
from pathlib import Path
import unittest


class BulkEdgeTest(unittest.TestCase):
    def test_only_exact_bulk_routes_are_added_inside_authenticated_operator(self):
        path = Path(__file__).resolve().parents[1] / 'integration/public-ui/provision.py'
        spec = importlib.util.spec_from_file_location('edge', path)
        edge = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(edge)
        plain = edge.nginx('chat.example.test', 'ops.example.test', 'old.example.test', tls=True)
        bulk = edge.nginx('chat.example.test', 'ops.example.test', 'old.example.test', tls=True, bulk=True)
        marker = '  auth_basic "AWS SecOps Operator";'
        self.assertEqual(plain.split(marker)[0], bulk.split(marker)[0])
        self.assertEqual(bulk.count('proxy_pass http://127.0.0.1:4444;'), 4)
        self.assertEqual(bulk.count('if ($secops_write_ok = 0) { return 403; }'), 5)
        self.assertEqual(bulk.count('proxy_set_header Authorization "";'), 5)
        self.assertIn('"POST:https://ops.example.test" 1;', bulk)
        self.assertIn('proxy_pass http://127.0.0.1:3340;', bulk)
