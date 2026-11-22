// QA alternative (a): the obvious Intl solution. It prints CLDR strings (JOD symbol, Arabic
// layout), not the specified JD layout, so it must score 0 in every check.
export function formatJOD(fils, locale) {
  return new Intl.NumberFormat(locale, { style: "currency", currency: "JOD" }).format(Number(fils) / 1000);
}
