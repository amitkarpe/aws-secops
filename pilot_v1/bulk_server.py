"""Isolated local bulk operator, reusing the existing HTTP/origin boundary.

No second writer for the retained SG/backlog service; no model or Gateway config
needed. New vagent credentials remain on the operator host, never copied to EC2.
"""
import argparse
from http.server import HTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from .bulk import BulkStore, OfflineProvider
from .bulk_s3 import S3Provider
from .server import Handler


class BulkService:
    def __init__(self, bulk):
        self.bulk = bulk

    def query(self, operation, arguments):
        if operation == 'list_batches' and not arguments:
            return {'version': 1, 'items': [self.bulk.summary()] if self.bulk.data else []}
        if operation == 'get_batch' and 'batch_id' in arguments and not set(arguments)-{'batch_id', 'offset', 'limit', 'state'}:
            return self.bulk.page(**arguments)
        raise ValueError('bulk read operation only')


class BulkHandler(Handler):
    def do_GET(self):
        if urlsplit(self.path).path == '/':
            self.path = '/bulk'
        if urlsplit(self.path).path not in {'/bulk', '/api/v1/list_batches', '/api/v1/get_batch', '/api/bulk/export'}:
            self._json(404, {'error': 'bulk-only service'}); return
        super().do_GET()

    def do_POST(self):
        if not self.path.startswith('/api/bulk/'):
            self._json(404, {'error': 'bulk-only service'}); return
        super().do_POST()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--manifest', type=Path)
    p.add_argument('--state', type=Path, required=True)
    p.add_argument('--port', type=int, default=4444)
    a = p.parse_args()
    if not 1024 <= a.port <= 65535:
        p.error('invalid local port')
    provider = S3Provider(a.manifest) if a.manifest else OfflineProvider(str(a.state)+'.provider.json')
    store = BulkStore(a.state, provider)
    BulkHandler.service = BulkService(store)
    try:
        with HTTPServer(('127.0.0.1', a.port), BulkHandler) as server:
            print(f'BULK_OPERATOR=http://localhost:{a.port}/bulk MODE={provider.context["mode"]}', flush=True)
            server.serve_forever()
    finally:
        store.close()


if __name__ == '__main__':
    main()
