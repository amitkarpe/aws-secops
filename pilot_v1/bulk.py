"""One bounded durable batch journal and explicitly approved async worker."""
from collections import Counter
from copy import deepcopy
import csv
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
from datetime import datetime, timezone
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor

ACTION = 'set_bucket_bpa'
KEYS = ('BlockPublicAcls', 'IgnorePublicAcls', 'BlockPublicPolicy', 'RestrictPublicBuckets')
TARGET = dict.fromkeys(KEYS, True)
STATES = {'PENDING', 'APPROVED', 'RUNNING', 'COMPLETED', 'SKIPPED', 'DENIED', 'FAILED', 'UNKNOWN'}


class PolicyDenied(PermissionError):
    """Only an explicit independent Gateway Policy denial, never a generic error."""


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def bpa(value):
    if not isinstance(value, dict) or set(value) != set(KEYS) or any(type(v) is not bool for v in value.values()):
        raise ValueError('invalid exact BPA evidence')
    return dict(value)


class BulkStore:
    """Lifetime process lock + in-process lock; atomic journal before dispatch."""
    def __init__(self, path, provider):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.lease = open(str(self.path)+'.lock', 'a')
        try:
            fcntl.flock(self.lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.lease.close()
            raise RuntimeError('batch store already has a writer') from None
        self.provider = provider
        self.worker = None
        self.data = None
        if self.path.exists():
            try:
                with self.path.open('rb') as stream:
                    raw = stream.read(2_000_001)
                if len(raw) > 2_000_000:
                    raise ValueError('oversize store')
                self.data = json.loads(raw)
                self.validate()
                changed = False
                for item in self.data['items']:
                    if item['state'] == 'RUNNING':
                        item.update(state='UNKNOWN', message='Interrupted; provider reconciliation required', changed=None)
                        changed = True
                if changed:
                    self.save()
            except Exception:
                self.close()
                raise RuntimeError('batch store corrupt or unreadable; not overwritten') from None

    def close(self):
        if self.worker and self.worker.is_alive():
            self.worker.join()
        self.lease.close()

    def validate(self):
        d = self.data
        m = d['manifest']
        if m['action'] != ACTION or m['target'] != TARGET or m['context'] != self.provider.context:
            raise ValueError('provider/action mismatch')
        if d['id'] != digest(m) or not 1 <= len(m['resources']) <= 1000 or len(d['items']) != len(m['resources']):
            raise ValueError('manifest integrity')
        if d['decision'] not in {'PENDING', 'APPROVE', 'REJECT'}:
            raise ValueError('invalid decision')
        names = set()
        for resource, item in zip(m['resources'], d['items']):
            name = resource['resource']
            bpa(resource['before'])
            if not isinstance(name, str) or len(name) > 63 or name in names:
                raise ValueError('resource integrity')
            names.add(name)
            if item['id'] != digest(resource) or item['resource'] != name or item['state'] not in STATES:
                raise ValueError('item integrity')
            if d['decision'] == 'PENDING' and item['state'] != 'PENDING':
                raise ValueError('unapproved state')
            if d['decision'] == 'REJECT' and item['state'] != 'DENIED':
                raise ValueError('rejected state')
        if sorted(names) != sorted(self.provider.resources):
            raise ValueError('configured resource manifest changed')

    def save(self):
        self.validate()
        if hasattr(self.provider, 'metrics'):
            self.data['usage'] = dict(self.provider.metrics, scope='provider process cumulative; no billing inference')
        raw = json.dumps(self.data).encode()
        if len(raw) > 2_000_000:
            raise ValueError('batch size limit')
        temp = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.path.parent, delete=False) as stream:
                temp = stream.name
                stream.write(raw); stream.flush(); os.fsync(stream.fileno())
            os.replace(temp, self.path)
            directory = os.open(self.path.parent, os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            if temp and os.path.exists(temp):
                os.unlink(temp)

    def preview(self, renew=False):
        with self.lock:
            # Keep a single bounded batch; do not erase an approved/terminal audit.
            if self.data and not renew:
                return self.summary()
            revision = 1
            if self.data:
                self.validate()
                if any(i['state'] in {'PENDING', 'APPROVED', 'RUNNING', 'UNKNOWN'} for i in self.data['items']):
                    raise ValueError('resolve current batch before new preview')
                revision = self.data['manifest']['version']+1
                if revision > 10:
                    raise ValueError('ten retained previews; operator archive review required')
                archive = self.path.with_name(self.path.name+'.'+self.data['id'])
                if not archive.exists():
                    with archive.open('xb') as out:
                        out.write(self.path.read_bytes()); out.flush(); os.fsync(out.fileno())
            resources = sorted(self.provider.resources)
            if not 1 <= len(resources) <= 1000 or len(set(resources)) != len(resources):
                raise ValueError('manifest resource bounds')
            evidence = [{'resource': r, 'before': bpa(self.provider.read(r))} for r in resources]
            manifest = dict(version=revision, context=deepcopy(self.provider.context), action=ACTION, target=dict(TARGET), resources=evidence)
            self.data = dict(id=digest(manifest), manifest=manifest, decision='PENDING', created_at=datetime.now(timezone.utc).isoformat(),
                             items=[dict(id=digest(r), resource=r['resource'], state='PENDING',
                                         after=None, changed=False, message='Awaiting human decision') for r in evidence])
            self.save()
            return self.summary()

    def require(self, batch_id):
        if not self.data or batch_id != self.data['id']:
            raise ValueError('unknown batch or stale preview')
        self.validate()

    def decide(self, batch_id, approval_hash, decision):
        with self.lock:
            self.require(batch_id)
            if approval_hash != digest(self.data['manifest']) or decision not in {'APPROVE', 'REJECT'}:
                raise ValueError('approval scope mismatch')
            if self.data['decision'] != 'PENDING':
                raise ValueError('approval already consumed')
            self.data['decision'] = decision
            for item in self.data['items']:
                item.update(state='APPROVED' if decision == 'APPROVE' else 'DENIED',
                            message='Approved exact preview' if decision == 'APPROVE' else 'Rejected: zero dispatch')
            self.save()
            return self.summary()

    def step(self, batch_id):
        """Claim durably under the lock; provider I/O must not block progress reads."""
        with self.lock:
            self.require(batch_id)
            if self.data['decision'] != 'APPROVE':
                raise ValueError('human approval required')
            if any(i['state'] == 'UNKNOWN' for i in self.data['items']):
                raise ValueError('reconcile unknown outcomes before continuing')
            item = next((i for i in self.data['items'] if i['state'] == 'APPROVED'), None)
            if item is None:
                return self.summary()
            resource = next(r for r in self.data['manifest']['resources'] if r['resource'] == item['resource'])
            item.update(state='RUNNING', changed=None, message='Claimed durably; outcome not yet known')
            self.save()  # failure here cannot dispatch
        update = {}
        dispatched = False
        try:
            current = bpa(self.provider.read(item['resource']))
            if current == TARGET:
                update = dict(state='SKIPPED', after=current, changed=False, message='Provider already compliant; no dispatch')
            elif current != resource['before']:
                update = dict(state='DENIED', after=current, changed=False, message='Evidence drift; stale approval blocked')
            else:
                dispatched = True
                audit = self.provider.apply(item['resource'], current)
                after = bpa(self.provider.read(item['resource']))
                update = dict(state='COMPLETED' if after == TARGET else 'FAILED', after=after,
                              changed=after != current, message='Provider verified compliant' if after == TARGET else 'Provider postcondition not met')
                if isinstance(audit, dict):
                    update['audit'] = audit
        except PolicyDenied:
            update = dict(state='DENIED', changed=False, message='Gateway Policy DENY; target not dispatched',
                          audit={'gateway_decision': 'DENY', 'target_calls': 0})
        except Exception:
            update = dict(state='UNKNOWN' if dispatched else 'FAILED', changed=None if dispatched else False,
                          message='Dispatch/readback uncertain; reconcile, do not replay' if dispatched else 'Pre-read failed; no dispatch')
        with self.lock:
            item.update(update)
            self.save()
            return self.summary()

    def start(self, batch_id, approval_hash):
        """Called only after native ASK or the existing trusted human UI boundary."""
        with self.lock:
            self.require(batch_id)
            if approval_hash != self.data['id']:
                raise ValueError('approval scope mismatch')
            if self.worker and self.worker.is_alive():
                raise ValueError('execution already active')
            if any(i['state'] in {'UNKNOWN', 'RUNNING'} for i in self.data['items']):
                raise ValueError('read-only reconciliation required')
            if self.data['decision'] == 'PENDING':
                if hasattr(self.provider, 'authorize'):
                    self.provider.authorize(batch_id)
                self.decide(batch_id, approval_hash, 'APPROVE')
            elif self.data['decision'] != 'APPROVE' or not any(i['state'] == 'APPROVED' for i in self.data['items']):
                raise ValueError('terminal/rejected batch cannot replay')
            elif hasattr(self.provider, 'authorize'):
                self.provider.authorize(batch_id)
            self.worker = threading.Thread(target=self._run, args=(batch_id,), daemon=False)
            self.worker.start()
            return self.summary()

    def _run(self, batch_id):
        # Bounded groups; never replay failed/unknown calls. No model per resource.
        concurrency = getattr(self.provider, 'concurrency', 1)
        try:
            with ThreadPoolExecutor(max_workers=concurrency) as pool:
                while True:
                    with self.lock:
                        if any(i['state'] == 'UNKNOWN' for i in self.data['items']):
                            return
                        count = sum(i['state'] == 'APPROVED' for i in self.data['items'])
                    if not count:
                        return
                    futures = [pool.submit(self.step, batch_id) for _ in range(min(count, concurrency))]
                    for future in futures:
                        future.result()
        except Exception:
            # Journal stays authoritative. Recovery is explicit, not automatic.
            return

    def reconcile(self, batch_id):
        with self.lock:
            self.require(batch_id)
            for item in self.data['items']:
                if item['state'] != 'UNKNOWN':
                    continue
                try:
                    after = bpa(self.provider.read(item['resource']))
                    item.update(state='COMPLETED' if after == TARGET else 'FAILED', after=after,
                                message='Read-only reconciliation; effect attribution unknown; no retry')
                except Exception:
                    item['message'] = 'Reconciliation unavailable; remains UNKNOWN'
                self.save()
            return self.summary()

    def summary(self):
        with self.lock:
            if not self.data:
                return {'version': 1, 'batch': None}
            self.validate()
            counts = dict(Counter(i['state'] for i in self.data['items']))
            return dict(version=1, batch_id=self.data['id'], approval_hash=self.data['id'],
                        action=ACTION, target=dict(TARGET), context=deepcopy(self.provider.context),
                        total=len(self.data['items']), exclusions=0, decision=self.data['decision'], counts=counts,
                        verified=counts.get('COMPLETED', 0)+counts.get('SKIPPED', 0),
                        observed_at=self.data.get('created_at', 'not recorded in initial demo journal'),
                        execution_active=bool(self.worker and self.worker.is_alive()),
                        usage=deepcopy(self.data.get('usage', {'scope': 'not recorded'})),
                        review_path='/bulk?batch_id='+self.data['id'],
                        message='Per-item provider evidence; UNKNOWN is not zero change')

    def page(self, batch_id, offset=0, limit=20, state=None):
        with self.lock:
            self.require(batch_id)
            if type(offset) is not int or type(limit) is not int or not 0 <= offset <= 1000 or not 1 <= limit <= 50 or state not in STATES | {None}:
                raise ValueError('pagination/filter bounds')
            items = [i for i in self.data['items'] if state is None or i['state'] == state]
            selected = deepcopy(items[offset:offset+limit])
            before = {r['resource']: r['before'] for r in self.data['manifest']['resources']}
            for item in selected:
                item['before'] = deepcopy(before[item['resource']])
            return dict(version=1, summary=self.summary(), total=len(items), offset=offset,
                        items=selected)

    def export(self, batch_id):
        with self.lock:
            self.require(batch_id)
            out = io.StringIO(); writer = csv.writer(out)
            writer.writerow(['batch_id', 'resource', 'state', 'changed', 'message'])
            for item in self.data['items']:
                writer.writerow([batch_id, item['resource'], item['state'], item['changed'], item['message']])
            return out.getvalue()


class OfflineProvider:
    """Explicit synthetic fleet; cannot call AWS. Provider state is separately persisted."""
    context = {'mode': 'OFFLINE', 'profile': 'none', 'region': 'none'}

    def __init__(self, path, count=1000):
        self.path = Path(path)
        self.resources = [f'offline-demo-{i:04d}' for i in range(count)]
        self.calls = 0
        self.values = json.loads(self.path.read_text()) if self.path.exists() else {r: {**TARGET, 'BlockPublicAcls': False} for r in self.resources}

    def read(self, resource):
        if resource not in self.resources:
            raise PermissionError('outside manifest')
        return bpa(self.values[resource])

    def apply(self, resource, before):
        if self.read(resource) != before:
            raise PermissionError('drift')
        self.calls += 1
        self.values[resource] = dict(TARGET)
        self.path.write_text(json.dumps(self.values))
