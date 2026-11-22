// SPDX-License-Identifier: Apache-2.0
// Run: node --test site/contribute/tests/logic.test.js   (no dependencies)
// Arabic sample text is built from code points so this file stays ASCII.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

import {
  glueLicense,
  BATCH_SIZE,
  CODE_PATTERN,
  COUNTRY_CHOICES,
  COUNTRY_CODES,
  COUNTRY_DIALECT,
  DIALECTS,
  INVISIBLE_RANGES,
  MAX_SKIPS,
  advance,
  clean,
  contributorRow,
  createState,
  currentWordId,
  dialectOf,
  entryRows,
  finishBatch,
  format,
  generateDeletionCode,
  generateUuid,
  goBack,
  markContributorSaved,
  parseSaved,
  randomInt,
  regenerateIdentity,
  remainingWords,
  restoreState,
  saveAnswer,
  skipWord,
  skipsLeft,
  startBatch,
  validateEntry,
  validateIntro,
  validatePool,
} from "../js/logic.js";
import { parseConfig } from "../js/api.js";
import { parseMarkdown } from "../js/markdown.js";

const pool = JSON.parse(readFileSync(new URL("../words.json", import.meta.url), "utf8"));
const AR = String.fromCodePoint(0x0645, 0x0631, 0x062d, 0x0628, 0x0627); // sample Arabic letters
const word = { id: "save", word: "Save", hint: "h", category: "ui-label", gendered: false };
const gword = { id: "welcome", word: "Welcome", hint: "h", category: "greeting-polite", gendered: true };

const okIntro = { name: "", email: "", country: "JO", countryOther: "", credit: false, consent: true };

test("word pool is valid", () => {
  assert.equal(pool.length, 100);
  assert.ok(validatePool(pool));
  assert.equal(validatePool([...pool, pool[0]]), false, "duplicate id rejected");
  assert.equal(validatePool([{ ...pool[0], category: "nope" }]), false);
});

test("intro: name and email are optional and become null", () => {
  const { values, errors } = validateIntro(okIntro);
  assert.deepEqual(errors, {});
  assert.equal(values.name, null);
  assert.equal(values.email, null);
  assert.equal(values.credit, false);
});

test("intro: whitespace-only name and email become null", () => {
  const { values, errors } = validateIntro({ ...okIntro, name: "   ", email: "  " });
  assert.deepEqual(errors, {});
  assert.equal(values.name, null);
  assert.equal(values.email, null);
});

test("intro: email validated only when typed", () => {
  assert.equal(validateIntro({ ...okIntro, email: "nope" }).errors.email, "err_email");
  assert.deepEqual(validateIntro({ ...okIntro, email: " a@b.co " }).errors, {});
  assert.equal(validateIntro({ ...okIntro, email: " a@b.co " }).values.email, "a@b.co");
  const long = `${"a".repeat(250)}@b.co`;
  assert.equal(validateIntro({ ...okIntro, email: long }).errors.email, "err_too_long");
});

test("intro: country and consent required, other needs text", () => {
  assert.equal(validateIntro({ ...okIntro, country: "" }).errors.country, "err_required");
  assert.equal(validateIntro({ ...okIntro, country: "XX" }).errors.country, "err_required");
  assert.equal(validateIntro({ ...okIntro, consent: false }).errors.consent, "err_consent");
  assert.equal(validateIntro({ ...okIntro, country: "other" }).errors.countryOther, "err_required");
  const r = validateIntro({ ...okIntro, country: "other", countryOther: " Chad " });
  assert.deepEqual(r.errors, {});
  assert.equal(r.values.countryOther, "Chad");
  assert.equal(r.values.dialect, "other");
  // A listed country never carries free text.
  assert.equal(validateIntro({ ...okIntro, countryOther: "x" }).values.countryOther, null);
});

test("intro: credit only with a name; limits and formula guard", () => {
  assert.equal(validateIntro({ ...okIntro, credit: true }).values.credit, false);
  assert.equal(validateIntro({ ...okIntro, name: "Zed", credit: true }).values.credit, true);
  assert.equal(validateIntro({ ...okIntro, name: "a".repeat(101) }).errors.name, "err_too_long");
  assert.equal(validateIntro({ ...okIntro, name: "=HYPERLINK()" }).errors.name, "err_formula");
});

test("entry: arabic and arabizi required, scripts checked", () => {
  assert.equal(validateEntry(word, { arabic: "", arabizi: "x" }).errors.arabic, "err_required");
  assert.equal(validateEntry(word, { arabic: AR, arabizi: "" }).errors.arabizi, "err_required");
  assert.equal(validateEntry(word, { arabic: "hifz", arabizi: "x" }).errors.arabic, "err_arabic_script");
  assert.equal(validateEntry(word, { arabic: AR, arabizi: AR }).errors.arabizi, "err_arabizi_script");
  const ok = validateEntry(word, { arabic: ` ${AR} `, arabizi: " 7ifz " });
  assert.deepEqual(ok.errors, {});
  assert.equal(ok.values.arabic, AR, "only surrounding whitespace is trimmed");
  assert.equal(ok.values.arabizi, "7ifz");
});

test("entry: Arabic text is kept byte-for-byte (bidi marks inside stay)", () => {
  const rlm = String.fromCodePoint(0x200f);
  const s = `${AR}${rlm}${AR}`;
  assert.equal(validateEntry(word, { arabic: s, arabizi: "x" }).values.arabic, s);
});

test("entry: keep in English makes arabic optional", () => {
  const r = validateEntry(word, { arabic: "", arabizi: "save", keptInEnglish: true });
  assert.deepEqual(r.errors, {});
  assert.equal(r.values.arabic, null);
  assert.equal(r.values.keptInEnglish, true);
});

test("entry: length limit counts code points", () => {
  const long = AR.repeat(41); // 205 code points
  assert.equal(validateEntry(word, { arabic: long, arabizi: "x" }).errors.arabic, "err_too_long");
  assert.deepEqual(validateEntry(word, { arabic: AR.repeat(40), arabizi: "x" }).errors, {});
});

test("entry: feminine fields only for gendered words", () => {
  const raw = { arabic: AR, arabizi: "x", arabicFeminine: AR, arabiziFeminine: "xa" };
  const g = validateEntry(gword, raw);
  assert.deepEqual(g.errors, {});
  assert.equal(g.values.arabicFeminine, AR);
  const n = validateEntry(word, raw);
  assert.equal(n.values.arabicFeminine, null);
  assert.equal(n.values.arabiziFeminine, null);
  assert.equal(
    validateEntry(gword, { ...raw, arabicFeminine: "latin" }).errors.arabicFeminine,
    "err_arabic_script",
  );
});

// Deterministic byte source for tests.
function seqBytes(seed = 1) {
  let x = seed;
  return (n) => {
    const out = new Uint8Array(n);
    for (let i = 0; i < n; i += 1) {
      x = (x * 1103515245 + 12345) >>> 0;
      out[i] = (x >>> 16) & 0xff;
    }
    return out;
  };
}

test("deletion code format, alphabet and uniqueness", () => {
  const seen = new Set();
  for (let i = 0; i < 2000; i += 1) {
    const c = generateDeletionCode();
    assert.match(c, CODE_PATTERN);
    seen.add(c);
  }
  assert.equal(seen.size, 2000);
  assert.match(generateDeletionCode(seqBytes(7)), CODE_PATTERN);
});

test("uuid v4 format", () => {
  assert.match(generateUuid(), /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
});

test("randomInt stays in range", () => {
  for (let i = 0; i < 500; i += 1) {
    const v = randomInt(7);
    assert.ok(v >= 0 && v < 7);
  }
  assert.throws(() => randomInt(0));
});

test("a full batch: 10 unique words, skips do not count, no repeats", () => {
  const bytes = seqBytes(3);
  const s = createState(bytes);
  assert.ok(startBatch(s, pool, bytes));
  const shown = new Set([currentWordId(s)]);
  for (let i = 0; i < MAX_SKIPS; i += 1) {
    assert.ok(skipWord(s, pool, bytes));
    shown.add(currentWordId(s));
  }
  assert.equal(skipsLeft(s), 0);
  assert.equal(skipWord(s, pool, bytes), false, "no fourth skip");
  let result;
  for (let i = 0; i < BATCH_SIZE; i += 1) {
    saveAnswer(s, currentWordId(s), { arabic: AR, arabizi: "x", arabicFeminine: null, arabiziFeminine: null, keptInEnglish: false });
    result = advance(s, pool, bytes);
    if (result === "word") shown.add(currentWordId(s));
  }
  assert.equal(result, "complete");
  assert.equal(shown.size, BATCH_SIZE + MAX_SKIPS);
  const rows = entryRows(s);
  assert.equal(rows.length, BATCH_SIZE);
  assert.equal(new Set(rows.map((r) => r.word_id)).size, BATCH_SIZE);
  for (const r of rows) {
    assert.deepEqual(Object.keys(r).sort(), [
      "arabic", "arabic_feminine", "arabizi", "arabizi_feminine", "contributor_id",
      "kept_in_english", "word_id",
    ]);
  }
  finishBatch(s);
  assert.equal(s.screen, "done");
  assert.equal(s.seen.length, BATCH_SIZE + MAX_SKIPS);
  assert.equal(s.intro.name, "", "personal data dropped after sending");
  assert.equal(remainingWords(s, pool), pool.length - BATCH_SIZE - MAX_SKIPS);

  // Second batch never repeats a word from the first.
  assert.ok(startBatch(s, pool, bytes));
  assert.ok(!s.seen.includes(currentWordId(s)));
});

test("back navigation: to intro before sending, not after", () => {
  const s = createState();
  startBatch(s, pool);
  saveAnswer(s, currentWordId(s), { arabic: AR, arabizi: "x", keptInEnglish: false });
  advance(s, pool);
  assert.equal(s.batch.index, 1);
  assert.equal(goBack(s), "word");
  assert.equal(s.batch.index, 0);
  assert.equal(goBack(s), "intro");
  s.contributorSent = true;
  s.screen = "words";
  assert.equal(goBack(s), "none");
});

test("pool exhaustion ends a batch early and stops new batches", () => {
  const small = pool.slice(0, 4);
  const s = createState();
  assert.ok(startBatch(s, small));
  let r;
  for (let i = 0; i < 4; i += 1) {
    saveAnswer(s, currentWordId(s), { arabic: AR, arabizi: "x", keptInEnglish: false });
    r = advance(s, small);
  }
  assert.equal(r, "complete");
  assert.equal(entryRows(s).length, 4);
  finishBatch(s);
  assert.equal(startBatch(s, small), false);
});

test("contributor row uses client id and code, nulls for empty optional fields", () => {
  const s = createState();
  const row = contributorRow(s, validateIntro(okIntro).values);
  assert.equal(row.id, s.contributorId);
  assert.equal(row.deletion_code, s.deletionCode);
  assert.equal(row.name, null);
  assert.equal(row.email, null);
  assert.equal(row.credit_by_name, false);
  assert.equal(row.consent, true);
});

test("restoreState rejects bad or foreign shapes", () => {
  const s = createState();
  assert.equal(restoreState(JSON.parse(JSON.stringify(s)), pool).contributorId, s.contributorId);
  assert.equal(restoreState(null, pool), null);
  assert.equal(restoreState({ ...s, v: 1 }, pool), null);
  assert.equal(restoreState({ ...s, seen: ["not-a-word"] }, pool), null);
  assert.equal(restoreState({ ...s, deletionCode: "bad" }, pool), null);
  assert.equal(restoreState({ ...s, screen: "words", batch: null }, pool), null);
});

test("format fills placeholders", () => {
  assert.equal(format("Word {current} of {total}", { current: 3, total: 10 }), "Word 3 of 10");
  assert.equal(format("{missing}", {}), "{missing}");
});

test("config: placeholders and non-Supabase URLs mean mock mode", () => {
  assert.equal(parseConfig(null), null);
  assert.equal(parseConfig({ supabaseUrl: "https://YOUR-PROJECT-REF.supabase.co", supabaseAnonKey: "k" }), null);
  assert.equal(parseConfig({ supabaseUrl: "https://abc.supabase.co", supabaseAnonKey: "YOUR-ANON-PUBLIC-KEY" }), null);
  assert.equal(parseConfig({ supabaseUrl: "http://abc.supabase.co", supabaseAnonKey: "k" }), null);
  assert.equal(parseConfig({ supabaseUrl: "https://evil.example.com", supabaseAnonKey: "k" }), null);
  assert.deepEqual(parseConfig({ supabaseUrl: "https://abc.supabase.co/", supabaseAnonKey: " k " }), {
    url: "https://abc.supabase.co",
    key: "k",
  });
});

test("markdown subset parses headings, lists and paragraphs", () => {
  const blocks = parseMarkdown("# T\n\nPara one\ncontinues.\n\n## S\n\n- a\n- b\n");
  assert.deepEqual(blocks, [
    { type: "h3", text: "T" },
    { type: "p", text: "Para one continues." },
    { type: "h4", text: "S" },
    { type: "ul", items: ["a", "b"] },
  ]);
  assert.deepEqual(parseMarkdown("Hi <!-- TODO(board): x --> there"), [{ type: "p", text: "Hi  there" }]);
  assert.deepEqual(parseMarkdown("Hi <!-- TODO(board):\nwrapped\n\nmarker --> there"), [{ type: "p", text: "Hi  there" }]);
});

// ---------------------------------------------------------------------------
// Invisible characters and the formula guard (fix round items 1 and 4)
// ---------------------------------------------------------------------------

const cp = (...points) => String.fromCodePoint(...points);
const ZWSP = cp(0x200b);
const ZWNJ = cp(0x200c);
const ZWJ = cp(0x200d);
const LRM = cp(0x200e);
const RLM = cp(0x200f);
const RLE = cp(0x202b);
const PDF = cp(0x202c);
const LRI = cp(0x2066);
const PDI = cp(0x2069);
const NBSP = cp(0x00a0);
const BOM = cp(0xfeff);
const INVISIBLE_ONLY = [ZWSP, NBSP, ZWJ + ZWNJ, BOM, `${LRM} ${RLM}`, RLE + PDF, LRI + PDI, " \t "];
const LEAD = ["", " ", "\t", "\n", "\r", ZWSP, RLM, RLE, LRI, PDI, BOM, NBSP, `${ZWSP} `];

test("clean: invisible-only values are empty; real text is left untouched", () => {
  for (const v of INVISIBLE_ONLY) assert.equal(clean(v), "", JSON.stringify(v));
  const inner = `${AR.slice(0, 2)}${ZWNJ}${AR.slice(2)}${ZWJ}${RLM}${cp(0x064b)}`;
  assert.equal(clean(`  ${inner}  `), inner);
  assert.equal(clean(`${ZWSP}abc`), `${ZWSP}abc`, "leading ZWSP before real text is not stripped");
});

test("invisible-only input counts as empty in every field", () => {
  for (const v of INVISIBLE_ONLY) {
    const intro = validateIntro({ ...okIntro, name: v, email: v, country: "other", countryOther: v });
    assert.equal(intro.values.name, null);
    assert.equal(intro.values.email, null);
    assert.equal(intro.errors.countryOther, "err_required");
    assert.equal(validateEntry(word, { arabic: v, arabizi: "x" }).errors.arabic, "err_required");
    assert.equal(validateEntry(word, { arabic: AR, arabizi: v }).errors.arabizi, "err_required");
    const g = validateEntry(gword, { arabic: AR, arabizi: "x", arabicFeminine: v, arabiziFeminine: v });
    assert.deepEqual(g.errors, {});
    assert.equal(g.values.arabicFeminine, null);
    assert.equal(g.values.arabiziFeminine, null);
  }
});

test("formula guard in every text field, also behind leading invisible characters", () => {
  const chars = ["=", "+", "-", "@"];
  LEAD.forEach((lead, i) => {
    const bad = `${lead}${chars[i % 4]}cmd()`;
    const label = JSON.stringify(bad);
    assert.equal(validateIntro({ ...okIntro, name: bad }).errors.name, "err_formula", label);
    assert.equal(validateIntro({ ...okIntro, email: `${bad}@a.test` }).errors.email, "err_formula", label);
    assert.equal(
      validateIntro({ ...okIntro, country: "other", countryOther: bad }).errors.countryOther,
      "err_formula",
      label,
    );
    const arBad = `${lead}${chars[i % 4]}${AR}`;
    assert.equal(validateEntry(word, { arabic: arBad, arabizi: "x" }).errors.arabic, "err_formula", label);
    assert.equal(validateEntry(word, { arabic: AR, arabizi: bad }).errors.arabizi, "err_formula", label);
    const g = validateEntry(gword, { arabic: AR, arabizi: "x", arabicFeminine: arBad, arabiziFeminine: bad });
    assert.equal(g.errors.arabicFeminine, "err_formula", label);
    assert.equal(g.errors.arabiziFeminine, "err_formula", label);
  });
  assert.equal(validateIntro({ ...okIntro, email: '=HYPERLINK("x")@a.test' }).errors.email, "err_formula");
});

test("single-line fields reject TAB, CR and LF inside", () => {
  for (const ch of ["\t", "\r", "\n"]) {
    assert.equal(validateIntro({ ...okIntro, name: `a${ch}b` }).errors.name, "err_single_line");
    assert.equal(validateIntro({ ...okIntro, email: `a${ch}b@c.de` }).errors.email, "err_single_line");
    assert.equal(
      validateIntro({ ...okIntro, country: "other", countryOther: `a${ch}b` }).errors.countryOther,
      "err_single_line",
    );
  }
});

test("no script restriction beyond Arabic letters: emoji and Cyrillic allowed in Arabizi", () => {
  const r = validateEntry(word, { arabic: AR, arabizi: `7abibi ${cp(0x1f642)} ${cp(0x0436)} ma3-salameh` });
  assert.deepEqual(r.errors, {});
});

// ---------------------------------------------------------------------------
// Tampered sessionStorage (item 5)
// ---------------------------------------------------------------------------

function midBatchState() {
  const s = createState();
  s.intro = { ...okIntro, name: "Zed" };
  startBatch(s, pool);
  saveAnswer(s, currentWordId(s), { arabic: AR, arabizi: "x", arabicFeminine: null, arabiziFeminine: null, keptInEnglish: false });
  advance(s, pool);
  s.batch.drafts[currentWordId(s)] = { arabic: "", arabizi: "dr", arabicFeminine: "", arabiziFeminine: "", keptInEnglish: false };
  return s;
}

test("parseSaved accepts a genuine mid-batch state", () => {
  const s = midBatchState();
  const back = parseSaved(JSON.stringify(s), pool);
  assert.ok(back);
  assert.equal(back.batch.index, 1);
});

test("parseSaved discards corrupt, partial or tampered state", () => {
  const good = midBatchState();
  const firstId = good.batch.order[0];
  const unknown = pool.length ? "not-a-word" : "";
  const mutate = (fn) => {
    const s = JSON.parse(JSON.stringify(good));
    fn(s);
    return JSON.stringify(s);
  };
  const cases = {
    "not JSON": "{oops",
    "JSON null": "null",
    "JSON array": "[]",
    "JSON string": '"x"',
    "empty string": "",
    "oversized": JSON.stringify({ ...good, pad: "x".repeat(200000) }),
    "intro null": mutate((s) => { s.intro = null; }),
    "intro missing fields": mutate((s) => { s.intro = { name: "x" }; }),
    "intro wrong types": mutate((s) => { s.intro.consent = "yes"; }),
    "intro huge string": mutate((s) => { s.intro.name = "x".repeat(5000); }),
    "batch without answers": mutate((s) => { delete s.batch.answers; }),
    "batch without drafts": mutate((s) => { delete s.batch.drafts; }),
    "batch answers array": mutate((s) => { s.batch.answers = []; }),
    "answer for unknown word": mutate((s) => { s.batch.answers[unknown] = s.batch.answers[firstId]; }),
    "answer that fails validation": mutate((s) => { s.batch.answers[firstId].arabic = "=cmd"; }),
    "answer wrong type": mutate((s) => { s.batch.answers[firstId].keptInEnglish = 1; }),
    "earlier word without answer": mutate((s) => { delete s.batch.answers[firstId]; }),
    "unknown word in order": mutate((s) => { s.batch.order[0] = unknown; }),
    "unknown word in seen": mutate((s) => { s.seen = [unknown]; }),
    "duplicate ids in order": mutate((s) => { s.batch.order.push(s.batch.order[0]); }),
    "huge seen array": mutate((s) => { s.seen = Array(5000).fill(pool[0].id); }),
    "order too long": mutate((s) => { s.batch.order = pool.slice(0, 11).map((w) => w.id); }),
    "too many skips": mutate((s) => { s.batch.skipped = pool.slice(50, 54).map((w) => w.id); }),
    "index out of range": mutate((s) => { s.batch.index = 7; }),
    "index not integer": mutate((s) => { s.batch.index = "1"; }),
    "seen overlaps batch": mutate((s) => { s.seen = [firstId]; }),
    "draft wrong type": mutate((s) => { s.batch.drafts[s.batch.order[1]].arabizi = 5; }),
    "bad contributor id": mutate((s) => { s.contributorId = "1; drop table"; }),
    "bad deletion code": mutate((s) => { s.deletionCode = "K-00000-00000"; }),
    "unknown screen": mutate((s) => { s.screen = "admin"; }),
    "unknown lang": mutate((s) => { s.lang = "fr"; }),
    "contributorSent string": mutate((s) => { s.contributorSent = "true"; }),
    "negative count": mutate((s) => { s.totalSent = -1; }),
    "words screen without batch": mutate((s) => { s.batch = null; }),
    "intro screen after contributor saved": mutate((s) => { s.screen = "intro"; s.contributorSent = true; s.intro.name = ""; }),
    "saved contributor still holding email": mutate((s) => { s.contributorSent = true; s.intro.email = "a@b.co"; }),
    "old version": mutate((s) => { s.v = 1; }),
    "prototype pollution shape": '{"__proto__":{"v":2},"v":2}',
  };
  for (const [label, raw] of Object.entries(cases)) {
    assert.equal(parseSaved(raw, pool), null, label);
  }
});

test("markContributorSaved locks identity and drops name and email", () => {
  const s = midBatchState();
  s.intro.email = "z@example.org";
  markContributorSaved(s);
  assert.equal(s.contributorSent, true);
  assert.equal(s.intro.name, "");
  assert.equal(s.intro.email, "");
  assert.equal(goBack({ ...s, batch: { ...s.batch, index: 0 } }), "none", "Back cannot reach the intro");
  assert.ok(parseSaved(JSON.stringify(s), pool), "locked state still restores");
});

test("regenerateIdentity changes both id and deletion code", () => {
  const s = createState();
  const before = [s.contributorId, s.deletionCode];
  regenerateIdentity(s);
  assert.notEqual(s.contributorId, before[0]);
  assert.notEqual(s.deletionCode, before[1]);
  assert.match(s.deletionCode, CODE_PATTERN);
});

// ---------------------------------------------------------------------------
// Word pool rules (item 8)
// ---------------------------------------------------------------------------

test("gender_note only on gendered words, and imperative buttons are gendered", () => {
  const byId = new Map(pool.map((w) => [w.id, w]));
  for (const w of pool) if ("gender_note" in w) assert.equal(w.gendered, true, w.id);
  for (const id of ["save", "send", "delete", "cancel", "share", "close", "copy", "you", "sorry", "please"]) {
    assert.equal(byId.get(id).gendered, true, id);
  }
  for (const id of ["settings", "password", "file", "folder", "app", "date"]) {
    assert.equal(byId.get(id).gendered, false, id);
  }
  for (const id of ["share-a-link", "submit", "continue", "confirm", "you-are-welcome"]) {
    assert.equal(byId.has(id), false, `near-duplicate ${id} removed`);
  }
  assert.equal(validatePool([{ ...pool.find((w) => !w.gendered), gender_note: "x" }]), false);
});

// ---------------------------------------------------------------------------
// Country -> dialect mapping (country round)
// ---------------------------------------------------------------------------

const EXPECTED_MAP = {
  levantine: ["JO", "PS", "SY", "LB"],
  iraqi: ["IQ"],
  egyptian: ["EG"],
  sudanese: ["SD"],
  gulf: ["SA", "AE", "KW", "QA", "BH", "OM"],
  maghrebi: ["LY", "TN", "DZ", "MA", "MR"],
  other: ["YE", "SO", "DJ", "KM"],
};
const EXPECTED_NAMES = {
  DZ: "Algeria", BH: "Bahrain", KM: "Comoros", DJ: "Djibouti", EG: "Egypt", IQ: "Iraq",
  JO: "Jordan", KW: "Kuwait", LB: "Lebanon", LY: "Libya", MR: "Mauritania", MA: "Morocco",
  OM: "Oman", PS: "Palestine", QA: "Qatar", SA: "Saudi Arabia", SO: "Somalia", SD: "Sudan",
  SY: "Syria", TN: "Tunisia", AE: "United Arab Emirates", YE: "Yemen",
};

test("mapping: every one of the 22 codes gives the agreed dialect group", () => {
  assert.equal(COUNTRY_CODES.length, 22);
  let n = 0;
  for (const [dialect, codes] of Object.entries(EXPECTED_MAP)) {
    for (const code of codes) {
      assert.equal(dialectOf(code), dialect, code);
      assert.equal(COUNTRY_DIALECT[code], dialect, code);
      n += 1;
    }
  }
  assert.equal(n, 22);
  assert.deepEqual([...COUNTRY_CODES].sort(), Object.values(EXPECTED_MAP).flat().sort());
  for (const d of Object.values(COUNTRY_DIALECT)) assert.ok(DIALECTS.includes(d));
});

test("mapping: other maps to other; unknown, wrong case and junk give null", () => {
  assert.equal(dialectOf("other"), "other");
  for (const bad of ["", "XX", "jo", "Jo", "OTHER", " JO", "JO ", "toString", "__proto__", "constructor", null, undefined, 1]) {
    assert.equal(dialectOf(bad), null, String(bad));
  }
});

test("country choices: alphabetical by English name, Other last", () => {
  assert.equal(COUNTRY_CHOICES.at(-1), "other");
  const names = COUNTRY_CODES.map((c) => EXPECTED_NAMES[c]);
  assert.deepEqual(names, [...names].sort());
  const en = JSON.parse(readFileSync(new URL("../strings.en.json", import.meta.url), "utf8"));
  for (const c of COUNTRY_CODES) assert.equal(en[`country_${c}`], EXPECTED_NAMES[c], c);
  assert.equal(en.country_other, "Other");
});

test("validation: no country chosen blocks the intro; every listed code passes", () => {
  assert.equal(validateIntro({ ...okIntro, country: "" }).errors.country, "err_required");
  assert.equal(validateIntro({ ...okIntro, country: undefined }).errors.country, "err_required");
  assert.equal(validateIntro({ ...okIntro, country: "jo" }).errors.country, "err_required");
  for (const c of COUNTRY_CODES) {
    const r = validateIntro({ ...okIntro, country: c, countryOther: "ignored" });
    assert.deepEqual(r.errors, {}, c);
    assert.equal(r.values.country, c);
    assert.equal(r.values.countryOther, null);
    assert.equal(r.values.dialect, COUNTRY_DIALECT[c]);
  }
});

test("contributor row sends country and country_other, never dialect", () => {
  const s = createState();
  const row = contributorRow(s, validateIntro({ ...okIntro, country: "other", countryOther: "Chad" }).values);
  assert.equal(row.country, "other");
  assert.equal(row.country_other, "Chad");
  assert.equal("dialect" in row, false);
  assert.equal("dialect_other" in row, false);
});

test("restore: unknown or tampered country codes are discarded", () => {
  const s = createState();
  s.intro.country = "JO";
  assert.ok(parseSaved(JSON.stringify(s), pool));
  for (const bad of ["XX", "jo", 5, null, "other ", "__proto__"]) {
    const t = JSON.parse(JSON.stringify(s));
    t.intro.country = bad;
    assert.equal(parseSaved(JSON.stringify(t), pool), null, String(bad));
  }
  const old = JSON.parse(JSON.stringify(s));
  delete old.intro.country;
  old.intro.dialect = "gulf";
  assert.equal(parseSaved(JSON.stringify(old), pool), null, "old dialect-shaped intro");
  assert.equal(parseSaved(JSON.stringify({ ...s, v: 2 }), pool), null, "old version");
});

// ---------------------------------------------------------------------------
// Extended invisible and line-break characters (QA round)
// ---------------------------------------------------------------------------

const NEW_INVISIBLES = [
  0x0085, 0x061c, 0x00ad, 0x034f, 0x115f, 0x1160, 0x2800, 0x3164, 0xffa0,
  0xfe00, 0xfe0f, 0xe0000, 0xe0041, 0xe007f,
];

test("new invisible characters alone count as empty and are covered by the list", () => {
  for (const c of NEW_INVISIBLES) {
    assert.ok(
      INVISIBLE_RANGES.some(([a, b]) => a <= c && c <= b),
      c.toString(16),
    );
    assert.equal(clean(cp(c)), "", c.toString(16));
    assert.equal(clean(` ${cp(c, c)} `), "", c.toString(16));
  }
});

test("formula guard sees through the new invisible characters", () => {
  for (const c of NEW_INVISIBLES) {
    const lead = cp(c);
    assert.equal(validateIntro({ ...okIntro, name: `${lead}=cmd` }).errors.name, "err_formula", c.toString(16));
    assert.equal(
      validateEntry(word, { arabic: AR, arabizi: `${lead}@x` }).errors.arabizi,
      "err_formula",
      c.toString(16),
    );
  }
});

test("real Arabic keeps ZWJ, ZWNJ, tashkeel, tatweel and bidi controls byte for byte", () => {
  const text = `${AR.slice(0, 2)}${ZWNJ}${AR.slice(2)}${ZWJ}${cp(0x064e, 0x0651)}${cp(0x0640)}${cp(0x061c)}${RLM}${LRI}x${PDI}`;
  const r = validateEntry(word, { arabic: text, arabizi: `7${cp(0xfe0f)}a` });
  assert.deepEqual(r.errors, {});
  assert.equal(r.values.arabic, text);
  assert.equal(r.values.arabizi, `7${cp(0xfe0f)}a`);
});

test("single-line fields reject VT, FF, NEL, LS and PS anywhere", () => {
  for (const c of [0x0b, 0x0c, 0x85, 0x2028, 0x2029]) {
    const ch = cp(c);
    assert.equal(validateIntro({ ...okIntro, name: `a${ch}b` }).errors.name, "err_single_line", c.toString(16));
    assert.equal(
      validateIntro({ ...okIntro, email: `a${ch}b@c.de` }).errors.email,
      "err_single_line",
      c.toString(16),
    );
    assert.equal(
      validateIntro({ ...okIntro, country: "other", countryOther: `a${ch}b` }).errors.countryOther,
      "err_single_line",
      c.toString(16),
    );
  }
});

test("glueLicense keeps CC BY 4.0 and its full stop unbreakable", () => {
  const out = glueLicense("Code Apache-2.0. Words CC BY 4.0.");
  assert.equal(out, "Code Apache-2.0. Words CC\u00a0BY\u00a04.0\u2060.");
  assert.equal(glueLicense("no licence here"), "no licence here");
  assert.ok(!/CC BY 4\.0/.test(out));
});
