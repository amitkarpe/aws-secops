/* Preserve static ASK while letting a constrained programmatic ASK own its UI copy. */
const fs = require('node:fs');
const path = require('node:path');

const root = process.argv[2];
if (!root || !path.isAbsolute(root)) throw Error('absolute LibreChat directory required');

const target = path.join(
  root,
  'node_modules/@librechat/agents/dist/cjs/hooks/executeHooks.cjs',
);
const oldText = `\tif (decision === "deny" || decision === "ask" || decision === "allow") {
\t\tapplyToolDecision(agg, decision, reason);
\t\treturn;
\t}`;
const newText = `\tif (decision === "deny" || decision === "ask" || decision === "allow") {
\t\tif (decision === "ask" && agg.decision === "ask" && output.allowedDecisions != null && reason != null) agg.reason = reason;
\t\tapplyToolDecision(agg, decision, reason);
\t\treturn;
\t}`;

const raw = fs.readFileSync(target, 'utf8');
if (raw.includes(newText)) {
  console.log('LIBRECHAT_APPROVAL_DESCRIPTION=READY STATIC_ASK=PRESERVED');
  process.exit(0);
}
if (!raw.includes(oldText)) throw Error('unsupported LibreChat approval aggregator; review required');
const updated = raw.replace(oldText, newText);
if (updated === raw || updated.includes(oldText)) throw Error('approval aggregator patch was not atomic');
fs.writeFileSync(`${target}.issue161-new`, updated, {mode: fs.statSync(target).mode & 0o777, flag: 'wx'});
fs.renameSync(`${target}.issue161-new`, target);
console.log('LIBRECHAT_APPROVAL_DESCRIPTION=READY STATIC_ASK=PRESERVED');
