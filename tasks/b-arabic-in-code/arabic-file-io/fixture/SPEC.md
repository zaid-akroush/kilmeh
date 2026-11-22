# Requirements

The directory `/app` is a small Python project. `ingest.py` reads a shop's data files and writes a summary, but it garbles the Arabic text in several ways. Fix `ingest.py` so the summary is correct.

Run it as `python3 /app/ingest.py IN_DIR OUT_DIR`. `sample/` shows the input layout; the grader runs your script on fresh input directories with different Arabic data but the same layout. Use only the Python standard library. The script runs as an unprivileged user that can write only inside `OUT_DIR`, so don't write elsewhere and don't depend on the locale or on `PYTHONUTF8`: any text I/O (`open`, `Path.read_text`/`write_text`, `subprocess` in text mode, logging handlers, temp files) must pass an explicit `encoding=` (the grader runs Python with EncodingWarning as an error, so text I/O without one fails).

## Inputs (all in `IN_DIR`)

- `products.csv`: UTF-8 with a byte order mark (BOM) at the start of the file. Header row `id,name,city`, then one row per product.
- `legacy.csv`: an old export in Windows-1256 (cp1256), no BOM. Header row `id,name`.
- `config.json`: UTF-8 JSON, an object with a `title` string.
- `docs/`: text files named `<Arabic words>.txt`, UTF-8 without a BOM. The file names contain Arabic letters.

## Outputs (all in `OUT_DIR`)

- `summary.json`: UTF-8, no BOM, one JSON object with these keys:
  - `title`: the title from `config.json`.
  - `products`: a list with one object per `products.csv` row, keyed by the header names (`id`, `name`, `city`), all values strings.
  - `legacy`: the same for `legacy.csv` (`id`, `name`).
  - `docs`: the file names from `docs/` without the `.txt` ending, sorted by plain Python string order.

  Write Arabic as real UTF-8 text, not as `\uXXXX` escapes.
- `docs/<name>.summary.txt` for each input doc, where `<name>` is the doc's file name without `.txt`, with its Arabic characters unchanged. The file holds the doc's first line (leading and trailing whitespace removed), then one line feed, in UTF-8 with no BOM. Create `OUT_DIR/docs/` if it doesn't exist.

Arabic text must reach the outputs exactly as it is in the inputs: no replacement characters, no dropped characters, no normalization, no escaping, no BOM in any output file.
