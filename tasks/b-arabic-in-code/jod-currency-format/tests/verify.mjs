// Track B parent grader for jod-currency-format. Never imports anything from the app.
//
// Runs tests/worker.mjs (as uid 65534 in a new session when this process is root) to get the
// agent's raw outputs, compares them with expected values held here, then kills the worker's
// process group and, when root, every process left under uid 65534. Prints one boolean per
// check as JSON and exits 0 only if all pass. Pattern: tasks/SCHEMA.md, "Track B graders".
//
// The exact strings of the first six checks are hard-coded below (no Intl, no ICU, no locale
// data), so the result cannot change with the Node build. The 200 values of
// three_decimals_hidden and the receipts are drawn fresh for each run and checked against
// `expected()`, a second hand-written BigInt formatter.
//
// Fails closed: before any agent code runs, the tests directory and everything in it must be
// owned by the grading user with no group or other access, or verify exits 2.
// Source is ASCII only: non-ASCII characters are written as escapes.
import { spawn, spawnSync } from "node:child_process";
import { randomInt } from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const APP = process.env.KILMEH_APP ?? "/app";
const HERE = path.dirname(fileURLToPath(import.meta.url));
const WORKER = path.join(HERE, "worker.mjs");
const WORKER_TIMEOUT_MS = 60_000;
const MAX_OUTPUT = 4_000_000;
const NOBODY = 65534;
const ENV = { PATH: "/usr/local/bin:/usr/bin:/bin", HOME: "/nonexistent" };
const LOCALES = ["en-JO", "ar-JO", "ar-JO-u-nu-arab"];

// Western number text -> the three layouts. Only digits and the two separators are mapped.
const arab = (t) =>
  t.replace(/[\d,.]/g, (c) =>
    c === "," ? "\u066c" : c === "." ? "\u066b" : String.fromCharCode(0x660 + Number(c)),
  );
const layout = (sign, t) => [`${sign}JD ${t}`, `${sign}${t} JD`, `${sign}${arab(t)} JD`];

// Rows: [kind, fils text, Western digits of N, sign]. kind "n" = Number, "b" = BigInt.
const POSITIVE = [
  ["n", "1234500", "1,234.500", ""],
  ["n", "5", "0.005", ""],
  ["n", "999", "0.999", ""],
  ["n", "1000", "1.000", ""],
  ["n", "100000", "100.000", ""],
  ["n", "1234567890", "1,234,567.890", ""],
  ["n", "50", "0.050", ""],
  ["n", "12", "0.012", ""],
  ["b", "1234500", "1,234.500", ""],
  ["b", "999999", "999.999", ""],
  ["n", "1000000000", "1,000,000.000", ""],
];
const NEGATIVE = [
  ["n", "-1234500", "1,234.500", "-"],
  ["n", "-5", "0.005", "-"],
  ["n", "-1000", "1.000", "-"],
  ["n", "-999", "0.999", "-"],
  ["b", "-1234500", "1,234.500", "-"],
  ["b", "-1", "0.001", "-"],
  ["n", "-1234567890", "1,234,567.890", "-"],
];
const ZERO = [
  ["n", "0", "0.000", ""],
  ["n", "-0", "0.000", ""],
  ["b", "0", "0.000", ""],
];
const LARGE = [
  ["b", "123456789012345678901234567890", "123,456,789,012,345,678,901,234,567.890", ""],
  ["b", "-1208925819614629174706176", "1,208,925,819,614,629,174,706.176", "-"],
  ["b", "1000000000000000000000000000000", "1,000,000,000,000,000,000,000,000,000.000", ""],
  ["b", "9007199254740993", "9,007,199,254,740.993", ""],
  ["n", "9007199254740991", "9,007,199,254,740.991", ""],
  ["n", "-9007199254740991", "9,007,199,254,740.991", "-"],
];
const NON_INTEGERS = [
  "1.5", "-2.25", "0.5", "NaN", "Infinity", "-Infinity", "9007199254740992",
  "-9007199254740992", "1e21", "4503599627370495.5", "0.1", "-0.001",
];

const text = (v) => ({ t: "text", v });
const range = { t: "range" };

// `locales`: the locale indexes a table applies to. Each row gives one call per locale.
function table(rows, localeIndexes) {
  const cases = [];
  for (const [kind, fils, digits, sign] of rows) {
    for (const i of localeIndexes) {
      cases.push([["fmt", [kind, fils], LOCALES[i]], text(layout(sign, digits)[i])]);
    }
  }
  return cases;
}

// A second, independent formatter for the values drawn at run time.
function expected(fils, locale) {
  const sign = fils < 0n ? "-" : "";
  const n = fils < 0n ? -fils : fils;
  const whole = String(n / 1000n).replace(/\B(?=(\d{3})+$)/g, ",");
  const t = `${whole}.${String(n % 1000n).padStart(3, "0")}`;
  return layout(sign, t)[LOCALES.indexOf(locale)];
}

const FRACTIONS = [0, 500, 50, 5, 100, 10, 1, 700, 70, 7, 900, 90];
function hiddenCases() {
  const cases = [];
  for (let i = 0; i < 200; i++) {
    const digits = randomInt(1, 13);
    const whole = randomInt(0, 10 ** digits);
    const frac = i % 4 === 0 ? randomInt(0, 1000) : FRACTIONS[randomInt(0, FRACTIONS.length)];
    let fils = BigInt(whole) * 1000n + BigInt(frac);
    if (randomInt(0, 2) === 0) fils = -fils;
    const locale = LOCALES[i % 3];
    cases.push([["fmt", [i % 2 ? "b" : "n", String(fils)], locale], text(expected(fils, locale))]);
  }
  return cases;
}

const NAMES = ["Tea", "Coffee", "Falafel", "Hummus", "Bread", "Olives", "Labneh"];
function receiptCases() {
  const cases = [];
  for (let i = 0; i < 9; i++) {
    const locale = LOCALES[i % 3];
    const items = Array.from({ length: randomInt(1, 5) }, () => ({
      name: NAMES[randomInt(0, NAMES.length)],
      fils: randomInt(1, 2_000_000) * (randomInt(0, 4) === 0 ? 1 : 5),
      qty: randomInt(1, 6),
    }));
    const lines = items.map(
      (it) => `${it.name} x${it.qty}: ${expected(BigInt(it.fils) * BigInt(it.qty), locale)}`,
    );
    const total = items.reduce((s, it) => s + BigInt(it.fils) * BigInt(it.qty), 0n);
    lines.push(`Total: ${expected(total, locale)}`);
    cases.push([["receipt", items, locale], text(lines.join("\n"))]);
  }
  return cases;
}

const DETAIL = {
  "en_format": "en-JO layout: JD, space, grouped dinars, three decimals",
  "ar_format": "ar-JO layout: grouped dinars with three decimals, space, JD, Western digits",
  "ar_arab_format": "ar-JO-u-nu-arab: Arabic-Indic digits, U+066C and U+066B separators",
  "three_decimals_hidden": "always three decimals on 200 random values in every locale",
  "negative": "leading ASCII minus, no bidi marks",
  "zero": "zero and -0 give 0.000 with no sign",
  "bigint_large": "BigInt and unsafe-adjacent amounts stay exact",
  "rejects_non_integer": "RangeError for fractions, NaN, Infinity and unsafe Numbers",
  "receipt_works": "receiptText formats item and total lines with formatJOD"
};
const CHECKS = Object.keys(DETAIL);

function makeCases() {
  return {
    en_format: table(POSITIVE, [0]),
    ar_format: table(POSITIVE, [1]),
    ar_arab_format: table(POSITIVE, [2]),
    three_decimals_hidden: hiddenCases(),
    negative: table(NEGATIVE, [0, 1, 2]),
    zero: table(ZERO, [0, 1, 2]),
    bigint_large: table(LARGE, [0, 1, 2]),
    rejects_non_integer: NON_INTEGERS.flatMap((v, i) => [
      [["fmt", ["n", v], LOCALES[i % 3]], range],
      [["fmt", ["n", v], LOCALES[(i + 1) % 3]], range],
    ]),
    receipt_works: receiptCases(),
  };
}

function matches(result, want) {
  if (!Array.isArray(result) || !result.every((x) => typeof x === "string")) return false;
  const got = JSON.stringify(result);
  return got === JSON.stringify(want.t === "range" ? ["err", "RangeError"] : ["ok", "string", want.v]);
}

// First path under `root` (itself included) that another user could reach, or null.
function unlockedPath(root) {
  const me = process.geteuid();
  const stack = [root];
  while (stack.length) {
    const p = stack.pop();
    const st = fs.lstatSync(p);
    if (st.uid !== me || st.mode & 0o077) {
      return `${p} (owner ${st.uid}, mode ${(st.mode & 0o7777).toString(8)})`;
    }
    if (st.isDirectory()) for (const n of fs.readdirSync(p)) stack.push(path.join(p, n));
  }
  return null;
}

// Drop to uid 65534 when root. Not root: no drop, process-group kill only.
const asNobody = () => (process.geteuid() === 0 ? { uid: NOBODY, gid: NOBODY } : {});

// kill(-1) as uid 65534 signals every process of that uid, daemons that left the session too.
function killNobody() {
  for (let i = 0; i < 3; i++) {
    spawnSync(process.execPath, ["-e", "try { process.kill(-1, 'SIGKILL') } catch {}"], {
      stdio: "ignore", cwd: "/", env: ENV, timeout: 30_000, ...asNobody(),
    });
  }
}

async function runWorker(calls) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "jod-grader-"));
  const inPath = path.join(dir, "in.json");
  const outPath = path.join(dir, "out.json");
  fs.writeFileSync(inPath, JSON.stringify(calls));
  const inFd = fs.openSync(inPath, "r");
  const outFd = fs.openSync(outPath, "w+");
  const source = fs.readFileSync(WORKER, "ascii");
  const child = spawn(process.execPath, ["--input-type=module", "-e", source, APP], {
    stdio: [inFd, "ignore", "ignore", outFd],
    cwd: APP, env: ENV, detached: true, ...asNobody(),
  });
  const exited = new Promise((resolve) => {
    child.on("exit", resolve);
    child.on("error", resolve);
  });
  let timer;
  const timeout = new Promise((r) => {
    timer = setTimeout(r, WORKER_TIMEOUT_MS);
  });
  await Promise.race([exited, timeout]);
  clearTimeout(timer);
  try {
    process.kill(-child.pid, "SIGKILL");
  } catch {}
  if (process.geteuid() === 0) killNobody();
  await exited;
  const size = fs.fstatSync(outFd).size;
  const data = size > MAX_OUTPUT ? null : fs.readFileSync(outPath, "utf8");
  fs.closeSync(inFd);
  fs.closeSync(outFd);
  fs.rmSync(dir, { recursive: true, force: true });
  if (data === null) return null;
  try {
    const results = JSON.parse(data);
    return Array.isArray(results) && results.length === calls.length ? results : null;
  } catch {
    return null;
  }
}

function logChecks(report, reason) {
  for (const [key, ok] of Object.entries(report)) {
    const why = ok ? DETAIL[key] : (reason ?? `expected ${DETAIL[key]}`);
    process.stderr.write(`${ok ? "PASS" : "FAIL"} ${key}: ${why}\n`);
  }
}

async function main() {
  if (typeof process.geteuid !== "function") {
    process.stderr.write("refusing to grade: needs a POSIX system (process.geteuid)\n");
    process.exit(2);
  }
  const reachable = unlockedPath(HERE);
  if (reachable !== null) {
    process.stderr.write(`refusing to grade: grader files readable by others: ${reachable}\n`);
    process.exit(2);
  }
  const calls = [];
  const owners = [];
  for (const [key, cases] of Object.entries(makeCases())) {
    for (const [call, want] of cases) {
      calls.push(call);
      owners.push([key, want]);
    }
  }
  const results = await runWorker(calls);
  // The verifier log keeps the raw exchange (tests compare runs; the grade never reads it).
  process.stderr.write(`worker calls: ${JSON.stringify(calls)}\n`);
  process.stderr.write(`worker results: ${JSON.stringify(results)}\n`);
  const report = Object.fromEntries(CHECKS.map((k) => [k, true]));
  owners.forEach(([key, want], i) => {
    if (results === null || !matches(results[i], want)) report[key] = false;
  });
  logChecks(report, results === null ? "no well-formed worker output" : null);
  process.stdout.write(`${JSON.stringify(report, null, 1)}\n`);
  process.exit(Object.values(report).every(Boolean) ? 0 : 1);
}

await main();
