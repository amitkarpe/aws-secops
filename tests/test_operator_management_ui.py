"""Credential-free execution of the actual Operator page JavaScript."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OperatorManagementUITests(unittest.TestCase):
    def test_live_summary_errors_and_historical_evidence(self):
        script = r'''
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync(process.argv[1], 'utf8');
const source = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const nodes = new Map(), requests = [];
const node = id => {
  if (!nodes.has(id)) nodes.set(id, {textContent:'',innerHTML:'',className:'',disabled:false});
  return nodes.get(id);
};
const aliases = ['lab-dev','lab-poc','lab-qa','lab-sec'];
const controls = ['s3-bucket-level-public-access-prohibited','restricted-ssh'];
function payload(value='COMPLIANT') {
  const proof = {reject_writes:0,approve_mutations:4,provider_verified:true,
    config:'COMPLIANT x4',rerun:'ALREADY_COMPLIANT / 0 writes'};
  return {version:1,controls:[],multi_account:{scope:'four-account-live-config',
    region:'ap-southeast-1',mutation:false,accounts:aliases.map(alias =>
      ({alias,controls:Object.fromEntries(controls.map(c=>[c,value]))}))},
    acceptance:{date:'2026-09-18',scope:'four-account GitHub OIDC acceptance proof',
      aliases,controls:Object.fromEntries(controls.map(c=>[c,{...proof}]))}};
}
let response = payload(), fail = false;
const context = vm.createContext({document:{getElementById:node,querySelectorAll:()=>[]},
  Date,AbortController,setTimeout,clearTimeout,setInterval:()=>0,
  fetch:async(path,options)=>{requests.push({path,options});if(fail)throw Error('private details');
    return {ok:true,json:async()=>structuredClone(response)}}});
const run = text => vm.runInContext(text, context);
const tick = () => new Promise(resolve=>setImmediate(resolve));
(async()=>{
  run(source); await tick();
  assert.equal(node('demo-status').textContent,'Ready');
  assert.equal(node('compliant-total').textContent,'8/8');
  assert.equal(node('noncompliant-total').textContent,'0/8');
  assert.match(node('audit-summary').textContent,/Recorded sequence/);
  response=payload('NON_COMPLIANT'); await run('refresh()');
  assert.equal(node('demo-status').textContent,'Attention');
  assert.equal(node('noncompliant-total').textContent,'8/8');
  response=payload('INSUFFICIENT_DATA'); await run('refresh()');
  assert.equal(node('demo-status').textContent,'Pending');
  assert.equal(node('pending-total').textContent,'8/8');
  response.multi_account.accounts[0].controls[controls[0]]='NON_COMPLIANT';
  await run('refresh()');
  assert.equal(node('demo-status').textContent,'Attention');
  assert.equal(node('pending-total').textContent,'7/8');
  // Unknown states and unexpected aliases cannot become markup or raw identifiers.
  response=payload('<img src=x onerror=alert(1)>'); await run('refresh()');
  assert.equal(node('pending-total').textContent,'8/8');
  assert.ok(!node('multi-account-rows').innerHTML.includes('<img'));
  for(const damage of [m=>{m.accounts[0].alias='unexpected-account'},
      m=>{m.accounts[0].alias='lab-poc'},m=>{m.region='wrong-region'},
      m=>{m.partial=true},m=>{m.available=false}]){
    response=payload(); damage(response.multi_account); await run('refresh()');
    assert.equal(node('demo-status').textContent,'Pending');
    assert.equal(node('matrix-source').textContent,'UNAVAILABLE');
    assert.ok(!node('multi-account-rows').innerHTML.includes('unexpected-account'));
  }
  response=payload(); response.acceptance.controls[controls[0]].provider_verified=false;
  await run('refresh()');
  assert.match(node('audit-summary').textContent,/incomplete/);
  delete response.acceptance; await run('refresh()');
  assert.equal(node('audit-summary').textContent,'Acceptance evidence unavailable');
  assert.ok(!node('proof-provider').textContent.includes('Verified'));
  response=payload(); await run('refresh()');
  const successfulFetch=run('lastRefreshAt');
  fail=true; await run('refresh()');
  assert.equal(run('lastRefreshAt'),successfulFetch);
  assert.equal(node('demo-status').textContent,'Pending');
  assert.equal(node('refresh-age').textContent,'Unavailable');
  assert.equal(node('refresh').disabled,false);
  assert.equal((node('multi-account-rows').innerHTML.match(/UNKNOWN/g)||[]).length,16);
  assert.ok(!node('global').textContent.includes('private details'));
  fail=false; await run('refresh()');
  assert.equal(node('demo-status').textContent,'Ready');
  assert.ok(requests.every(r=>r.path==='/api/operator/status'&&!r.options.method));
  assert.ok(html.indexOf('aria-label="Current four-account risk"')<html.indexOf('id="acceptance"'));
  assert.ok(!/<details id="legacy"[^>]*\bopen\b/.test(html));
  assert.ok(html.includes('not AWS evaluation age'));
  console.log('Operator management UI behavior PASS');
})().catch(error=>{console.error(error);process.exitCode=1});
'''
        result = subprocess.run(
            ['node', '-e', script, str(ROOT / 'pilot_v1/static/operator.html')],
            text=True, capture_output=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
