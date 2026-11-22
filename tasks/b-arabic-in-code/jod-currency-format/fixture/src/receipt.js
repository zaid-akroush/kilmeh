import { formatJOD } from "./money.js";

// items: [{ name, fils, qty }] with integer Number fils. One line per item, then the total.
export function receiptText(items, locale) {
  const lines = items.map(
    (it) => `${it.name} x${it.qty}: ${formatJOD(BigInt(it.fils) * BigInt(it.qty), locale)}`,
  );
  const total = items.reduce((sum, it) => sum + BigInt(it.fils) * BigInt(it.qty), 0n);
  lines.push(`Total: ${formatJOD(total, locale)}`);
  return lines.join("\n");
}
