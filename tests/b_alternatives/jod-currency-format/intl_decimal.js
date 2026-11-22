export function formatJOD(fils, locale) {
  let n;
  if (typeof fils === "bigint") n = fils; else if (Number.isSafeInteger(fils)) n = BigInt(fils); else throw new RangeError("int");
  const neg = n < 0n; if (neg) n = -n;
  const s = `${n / 1000n}.${String(n % 1000n).padStart(3, "0")}`;
  const t = new Intl.NumberFormat(locale === "ar-JO" ? "ar-JO-u-nu-latn" : locale, { style: "decimal", minimumFractionDigits: 3, maximumFractionDigits: 3 }).format(s);
  const sg = neg ? "-" : "";
  return locale === "en-JO" ? `${sg}JD ${t}` : `${sg}${t} JD`;
}
