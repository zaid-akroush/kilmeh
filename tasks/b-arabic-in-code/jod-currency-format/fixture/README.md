# jod-money

Format Jordanian dinar (JOD) amounts. 1 JOD = 1000 fils, so amounts are integer fils and always show three decimals.

- `src/money.js`: `formatJOD(fils, locale)` (stub).
- `src/receipt.js`: `receiptText(items, locale)` builds a receipt with `formatJOD`.
- `examples.mjs`: six examples, `node examples.mjs`.

ES modules, no dependencies.
