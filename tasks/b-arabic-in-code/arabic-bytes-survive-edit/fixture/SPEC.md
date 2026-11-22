# Requirements

The directory `/app` holds a small storefront project that is never built or run: `src/strings.ts` (UI strings for a TypeScript module), `locale/ar.csv` (the same strings as an Arabic CSV export) and `README.md`. Make exactly three edits and change nothing else.

1. In `src/strings.ts`, change the line `export const VERSION = "2.3.0";` to `export const VERSION = "2.4.0";`.
2. In `src/strings.ts`, insert this one line immediately after the `checkout_title` entry (the line that starts with `  checkout_title:`), as its own line ending in a line feed (LF). It starts with two spaces:

   `  checkout_subtitle: "راجع طلبك قبل الدفع",`

3. In `locale/ar.csv`, append this row as a new last row, ending in CRLF like every other row in that file:

   `checkout_subtitle,راجع طلبك قبل الدفع`

`README.md` must stay byte-for-byte identical.

Every other byte of the three files must stay exactly as it is. That is graded byte by byte, so these files contain things that an editor, a formatter or a careless script will silently change:

- Invisible direction controls (for example U+200E, U+200F, U+061C, U+202A to U+202E, U+2066 to U+2069), the joiners U+200C (ZWNJ) and U+200D (ZWJ, also inside an emoji sequence), and U+00A0 (no-break space). Keep each one where it is. Don't strip or move them.
- Arabic marks in the exact order they are stored in, including a shadda/fatha pair that is not in canonical order and an alef followed by U+0653 that is not composed. Don't apply Unicode normalization (NFC, NFD, NFKC or NFKD) to any text. Don't "fix" the ligature U+FDF2 or any other character.
- Line endings: `src/strings.ts` uses LF and has no newline at the end of the file; keep that (don't add one). `locale/ar.csv` uses CRLF; keep CRLF on every line and end the file with CRLF after the appended row. Keep trailing spaces on lines that have them.
- Encoding: UTF-8 with no byte order mark (BOM), in all three files.

Use only the Python standard library or standard command-line tools. The grader runs after you finish and compares the bytes of the three files with the originals; it reads the files as they are on disk, and it does not run any code in `/app`. Don't rely on tests or grader files: none are available here.
