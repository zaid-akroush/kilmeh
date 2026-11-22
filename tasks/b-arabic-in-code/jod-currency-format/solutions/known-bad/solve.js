// The two-decimal "cents" habit: toFixed(2), no grouping, Western digits, "JD".
export function formatJOD(fils, locale) {
  const text = (Number(fils) / 1000).toFixed(2);
  return locale === "en-JO" ? `JD ${text}` : `${text} JD`;
}
