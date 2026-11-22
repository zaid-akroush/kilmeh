// Six visible examples: node examples.mjs
import assert from "node:assert/strict";
import { formatJOD } from "./src/money.js";

assert.equal(formatJOD(1234500, "en-JO"), "JD 1,234.500");
assert.equal(formatJOD(1234500, "ar-JO"), "1,234.500 JD");
assert.equal(formatJOD(5, "en-JO"), "JD 0.005");
assert.equal(formatJOD(-250, "ar-JO"), "-0.250 JD");
assert.equal(formatJOD(1000n, "en-JO"), "JD 1.000");
assert.throws(() => formatJOD(1.5, "en-JO"), RangeError);
console.log("examples ok");
