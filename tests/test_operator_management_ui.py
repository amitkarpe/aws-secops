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

    def test_theme_preference_and_storage_failure(self):
        script = r'''
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync(process.argv[1], 'utf8');
const source = html.match(/<script id="operator-theme">([\s\S]*?)<\/script>/)[1];
const key = 'aws-secops-operator-theme';
function boot(saved=null, systemDark=false, blocked=false) {
  const root={dataset:{}}, attrs={}, state={textContent:''};
  let ready, click, mediaChange, loaded=false;
  const button={hidden:true,setAttribute:(k,v)=>{attrs[k]=v},
    addEventListener:(event,fn)=>{assert.equal(event,'click');click=fn}};
  const media={matches:systemDark,addEventListener:(event,fn)=>{mediaChange=fn}};
  const storage={value:saved,getItem:k=>{assert.equal(k,key);if(blocked)throw Error('denied');return storage.value},
    setItem:(k,v)=>{assert.equal(k,key);if(blocked)throw Error('denied');storage.value=v}};
  vm.runInNewContext(source,{document:{documentElement:root,
    getElementById:id=>loaded?(id==='theme-toggle'?button:state):null,
    addEventListener:(event,fn)=>{assert.equal(event,'DOMContentLoaded');ready=fn}},
    window:{matchMedia:()=>media},localStorage:storage});
  // Theme is applied before DOM readiness, not after a status response.
  const initial=root.dataset.theme;
  loaded=true;ready();
  return {root,attrs,state,button,storage,initial,click:()=>click(),
    system:dark=>{media.matches=dark;mediaChange()}};
}
const light=boot();
assert.equal(light.initial,'light');
assert.equal(light.button.hidden,false);
assert.equal(light.attrs['aria-pressed'],'false');
assert.equal(light.state.textContent,'Off');
light.click();
assert.equal(light.root.dataset.theme,'dark');
assert.equal(light.attrs['aria-pressed'],'true');
assert.equal(light.state.textContent,'On');
assert.equal(light.button.title,'Switch to light mode');
assert.equal(light.storage.value,'dark');
assert.equal(boot(light.storage.value,false).initial,'dark');
light.system(false);assert.equal(light.root.dataset.theme,'dark');
light.click();assert.equal(light.storage.value,'light');
assert.equal(boot('light',true).initial,'light');
const system=boot(null,true);
assert.equal(system.initial,'dark');system.system(false);
assert.equal(system.root.dataset.theme,'light');
assert.equal(boot('invalid',true).initial,'dark');
const denied=boot(null,true,true);
assert.equal(denied.initial,'dark');denied.click();
assert.equal(denied.root.dataset.theme,'light');
assert.equal(denied.attrs['aria-pressed'],'false');
assert.ok(html.includes(':root[data-theme="dark"]'));
// No fetch or other API capability is provided to the isolated theme script.
console.log('Operator theme behavior PASS');
'''
        result = subprocess.run(
            ['node', '-e', script, str(ROOT / 'pilot_v1/static/operator.html')],
            text=True, capture_output=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


    def test_admin_control_center_uses_existing_confirmation_gated_prepare_flow(self):
        html = (ROOT / 'pilot_v1/static/operator.html').read_text()
        self.assertIn('<title>AWS SecOps Admin Control Center</title>', html)
        self.assertIn('<h1>SecOps Admin Control Center</h1>', html)
        self.assertIn('aria-label="Demo preparation controls"', html)
        self.assertIn('data-family="s3"', html)
        self.assertIn('data-family="sg"', html)
        self.assertIn('Re-arm S3 demo', html)
        self.assertIn('Re-arm SSH demo', html)
        self.assertIn("async function prepareDemo(family,button,out)", html)
        self.assertIn("api('/api/operator/prepare-preview',{family})", html)
        self.assertIn("const ok=confirm(", html)
        self.assertIn(">Config Dashboard</a>", html)
        self.assertIn(">Compliance Agent</a>", html)
        self.assertIn("Demo re-armed and verified.", html)
        self.assertIn("Starting state: NON_COMPLIANT", html)
        self.assertIn("api('/api/operator/prepare',{family,confirmation_token:p.confirmation_token})", html)
        self.assertIn("if(!ok){out.textContent='Cancelled — no demo resources changed.';return}", html)
        self.assertNotIn('rollback-all', html)
        self.assertNotIn('revoke-all', html)


if __name__ == '__main__':
    unittest.main()
