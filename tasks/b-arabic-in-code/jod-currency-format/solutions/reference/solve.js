// Hand-written BigInt math, no Intl: the spec stands on its own (it is not CLDR's output).
const ARABIC_DIGITS = "\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669";

export function formatJOD(fils, locale) {
  let n;
  if (typeof fils === "bigint") n = fils;
  else if (Number.isSafeInteger(fils)) n = BigInt(fils);
  else throw new RangeError("fils must be a safe integer Number or a BigInt");
  const sign = n < 0n ? "-" : "";
  if (n < 0n) n = -n;
  const whole = String(n / 1000n).replace(/\B(?=(\d{3})+$)/g, ",");
  let number = `${whole}.${String(n % 1000n).padStart(3, "0")}`;
  if (locale === "ar-JO-u-nu-arab") {
    number = number.replace(/[\d,.]/g, (c) =>
      c === "," ? "\u066c" : c === "." ? "\u066b" : ARABIC_DIGITS[c],
    );
  } else if (locale !== "en-JO" && locale !== "ar-JO") {
    throw new RangeError("unsupported locale");
  }
  return locale === "en-JO" ? `${sign}JD ${number}` : `${sign}${number} JD`;
}
