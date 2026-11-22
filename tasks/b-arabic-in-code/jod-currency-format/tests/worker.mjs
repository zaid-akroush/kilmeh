// Track B worker: runs the agent's code and reports raw outputs. It decides nothing.
//
// verify.mjs starts it with `node --input-type=module -e <this source> APP` (as uid 65534 when
// the grader is root, which cannot read the locked /tests) in its own session. It reads the
// call list from stdin before any agent code loads, imports the agent's modules, and writes one
// JSON list of raw results to fd 3 (a file the parent holds). stdout and stderr go nowhere.
// Whatever this process writes, the parent compares the outputs with expected values it holds.
import fs from "node:fs";

const calls = JSON.parse(fs.readFileSync(0, "utf8"));
const app = process.argv[1];

const amount = ([kind, text]) => (kind === "b" ? BigInt(text) : Number(text));
const stringResult = (v) => (typeof v === "string" ? ["ok", "string", v] : ["ok", typeof v, ""]);

function run(call, money, receipt) {
  try {
    if (call[0] === "fmt") return stringResult(money.formatJOD(amount(call[1]), call[2]));
    if (call[0] === "receipt") return stringResult(receipt.receiptText(call[1], call[2]));
    return ["err", "BadCall"];
  } catch (e) {
    return ["err", e instanceof RangeError ? "RangeError" : "Other"];
  }
}

let results;
try {
  const money = await import(`file://${app}/src/money.js`);
  const receipt = await import(`file://${app}/src/receipt.js`);
  results = calls.map((call) => run(call, money, receipt));
} catch {
  results = calls.map(() => ["err", "ImportError"]);
}
const data = Buffer.from(JSON.stringify(results), "utf8");
fs.ftruncateSync(3, 0);
let done = 0;
while (done < data.length) done += fs.writeSync(3, data, done, data.length - done, done);
