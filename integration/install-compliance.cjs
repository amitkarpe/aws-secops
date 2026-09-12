/* Add unified compliance + planning MCP while preserving existing S3 reader/executor. */
const fs = require('node:fs');
const path = require('node:path');
const {isDeepStrictEqual} = require('node:util');
const root = process.argv[2];
if (!root || !path.isAbsolute(root)) throw Error('absolute LibreChat directory required');
const yaml = require(path.join(root,'node_modules/js-yaml'));
const file = path.join(root,'librechat.yaml');
const raw = fs.readFileSync(file,'utf8');
const config = yaml.load(raw), updated = structuredClone(config);
if (!updated.mcpServers) throw Error('existing mcpServers mapping required');
const approval = updated.endpoints?.agents?.toolApproval;
if (!approval?.enabled || approval.mode !== 'default' || !Array.isArray(approval.allow) || !Array.isArray(approval.ask))
  throw Error('expected native tool approval configuration');
if (approval.allow.some(x => /[*]/.test(x)) || approval.ask.some(x => /[*]/.test(x)))
  throw Error('wildcard tool approval is not accepted');

const compliance = {
  type:'stdio', command:'/opt/aws-secops/.venv-mcp/bin/python', args:['-m','pilot_v1.compliance_mcp'],
  env:{PYTHONPATH:'/opt/aws-secops',SECOPS_SG_BACKEND_URL:'http://localhost:4455'},
  timeout:35000,initTimeout:15000,chatMenu:false,serverInstructions:true,
};
if (updated.mcpServers.aws_compliance && !isDeepStrictEqual(updated.mcpServers.aws_compliance,compliance))
  throw Error('existing aws_compliance MCP differs; review before replacing');
updated.mcpServers.aws_compliance = compliance;

const planner = {
  type:'stdio', command:'/opt/aws-secops/.venv-mcp/bin/python', args:['-m','pilot_v1.operator_mcp'],
  env:{PYTHONPATH:'/opt/aws-secops',SECOPS_OPERATOR_BACKEND_URL:'http://localhost:4444'},
  timeout:95000,initTimeout:15000,chatMenu:false,serverInstructions:true,
};
if (updated.mcpServers.aws_compliance_planner && !isDeepStrictEqual(updated.mcpServers.aws_compliance_planner,planner))
  throw Error('existing aws_compliance_planner MCP differs; review before replacing');
updated.mcpServers.aws_compliance_planner = planner;

const retiredPlannerTools = [
  'prepare_remediation_batch_mcp_aws_compliance_planner',
  'prepare_eligible_remediation_batches_mcp_aws_compliance_planner',
];
approval.allow = approval.allow.filter(name => !retiredPlannerTools.includes(name));
approval.ask = approval.ask.filter(name => !retiredPlannerTools.includes(name));

const reads = [
  'get_config_summary_mcp_aws_compliance','list_config_findings_mcp_aws_compliance',
  'list_sg_batches_mcp_aws_compliance','get_sg_batch_mcp_aws_compliance',
  'get_remediation_plan_mcp_aws_compliance_planner','prepare_remediation_mcp_aws_compliance_planner',
];
for (const name of reads) {
  if (!approval.allow.includes(name)) approval.allow.push(name);
  if (approval.ask.includes(name)) throw Error('read/planning tool unexpectedly configured as ASK');
}
const executorNames=['start_sg_batch_execution_mcp_aws_compliance','mcp:aws_compliance:start_sg_batch_execution'];
for(const name of executorNames){
  if(approval.allow.includes(name))throw Error('SG execution must not be statically allowed');
  if(!approval.ask.includes(name))approval.ask.push(name);
  const hook={matcher:name,module:'/opt/aws-secops/integration/sg-approval-hook.cjs'};
  approval.hooks??=[];const existing=approval.hooks.find(h=>h.matcher===name);
  if(existing&&!isDeepStrictEqual(existing,hook))throw Error('existing SG approval hook differs');
  if(!existing)approval.hooks.push(hook);
}
const rendered=yaml.dump(updated,{lineWidth:-1,noRefs:true});
if(!isDeepStrictEqual(yaml.load(rendered),updated))throw Error('YAML round trip differs');
if(rendered!==raw){const backup=file+'.before-aws-compliance';if(!fs.existsSync(backup))fs.writeFileSync(backup,raw,{mode:0o600,flag:'wx'});fs.writeFileSync(file+'.compliance-new',rendered,{mode:fs.statSync(file).mode&0o777,flag:'wx'});fs.renameSync(file+'.compliance-new',file);}
console.log('AWS_COMPLIANCE_MCP=READY CONFIG_SG_READS=ALLOW PLANNER=ONE_PREPARE_TOOL SG_EXECUTOR=ASK S3_CONFIG=PRESERVED');
