/* Install the isolated Compliance Agent v1 MCP without modifying legacy MCP servers. */
const fs = require('node:fs');
const path = require('node:path');
const {isDeepStrictEqual} = require('node:util');

const root = process.argv[2];
const harnessArn = process.argv[3] || process.env.COMPLIANCE_AGENT_V1_HARNESS_ARN;
if (!root || !path.isAbsolute(root)) throw Error('absolute LibreChat directory required');
if (!/^arn:aws[a-zA-Z-]*:bedrock-agentcore:[a-z0-9-]+:[0-9]{12}:harness\/compliance_agent_v1-[A-Za-z0-9]+$/.test(harnessArn || ''))
  throw Error('exact Compliance Agent v1 Harness ARN required');

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

const server = {
  type:'stdio',
  command:'/opt/compliance-agent-v1/.venv/bin/python',
  args:['-m','compliance_agent_v1.mcp_server'],
  env:{
    PYTHONPATH:'/opt/compliance-agent-v1/src',
    CONFIG_BACKEND_URL:'http://127.0.0.1:1111',
    COMPLIANCE_AGENT_V1_HARNESS_ARN:harnessArn,
    AWS_REGION:'ap-southeast-1',
  },
  timeout:120000,
  initTimeout:15000,
  chatMenu:false,
  serverInstructions:true,
};
const existing = updated.mcpServers.compliance_agent_v1;
if (existing && !isDeepStrictEqual(existing,server))
  throw Error('existing compliance_agent_v1 MCP differs; review before replacing');
updated.mcpServers.compliance_agent_v1 = server;

const readTool='ask_compliance_agent_v1_mcp_compliance_agent_v1';
if (!approval.allow.includes(readTool)) approval.allow.push(readTool);
approval.ask = approval.ask.filter(name => name !== readTool);

const planner = {
  type:'stdio',
  command:'/opt/aws-secops/.venv-mcp/bin/python',
  args:['-m','pilot_v1.operator_mcp'],
  env:{PYTHONPATH:'/opt/aws-secops',SECOPS_OPERATOR_BACKEND_URL:'http://localhost:4444'},
  timeout:300000,
  initTimeout:15000,
  chatMenu:false,
  serverInstructions:true,
};
const existingPlanner=updated.mcpServers.aws_compliance_planner;
const previousPlanner={...planner,timeout:190000};
if (!existingPlanner)
  throw Error('exact existing four-account compliance planner MCP required');
if (!isDeepStrictEqual(existingPlanner,planner) && !isDeepStrictEqual(existingPlanner,previousPlanner))
  throw Error('existing four-account compliance planner MCP differs; review before replacing');
updated.mcpServers.aws_compliance_planner=planner;

const prepareTool='prepare_multi_account_remediation_mcp_aws_compliance_planner';
if (!approval.allow.includes(prepareTool)) approval.allow.push(prepareTool);
approval.ask = approval.ask.filter(name => name !== prepareTool);

const executeNames=[
  'execute_multi_account_remediation_mcp_aws_compliance_planner',
  'mcp:aws_compliance_planner:execute_multi_account_remediation',
];
for(const name of executeNames){
  if(approval.allow.includes(name)) throw Error('four-account v1 execution must not be statically allowed');
  if(!approval.ask.includes(name)) approval.ask.push(name);
  const hook={matcher:name,module:'/opt/aws-secops/integration/multi-account-approval-hook.cjs'};
  approval.hooks??=[];
  const existingHook=approval.hooks.find(h=>h.matcher===name);
  if(existingHook&&!isDeepStrictEqual(existingHook,hook)) throw Error('existing four-account approval hook differs');
  if(!existingHook) approval.hooks.push(hook);
}
if(!fs.existsSync('/opt/aws-secops/integration/multi-account-approval-hook.cjs'))
  throw Error('four-account approval hook missing');

const rendered=yaml.dump(updated,{lineWidth:-1,noRefs:true});
if(!isDeepStrictEqual(yaml.load(rendered),updated)) throw Error('YAML round trip differs');
if(rendered!==raw){
  const backup=file+'.before-compliance-agent-v1';
  if(!fs.existsSync(backup)) fs.writeFileSync(backup,raw,{mode:0o600,flag:'wx'});
  const temp=file+'.compliance-v1-new';
  fs.writeFileSync(temp,rendered,{mode:fs.statSync(file).mode&0o777,flag:'wx'});
  fs.renameSync(temp,file);
}
console.log('COMPLIANCE_AGENT_V1=READY READ=ALLOW PREPARE=ALLOW EXECUTE=ASK HARNESS_TOOLS=0');
