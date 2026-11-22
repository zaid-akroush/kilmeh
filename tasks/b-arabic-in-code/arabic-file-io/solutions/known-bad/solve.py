"""Known-bad ingest.py (solve.sh copies this file over /app/ingest.py).

Plausible partial fix: the BOM and the file names are fixed, but the Windows-1256 file is read as
UTF-8 with errors="ignore" (bytes silently dropped) and JSON keeps the default ensure_ascii.
Must FAIL legacy_cp1256_decoded and json_not_escaped.
"""

import csv
import json
import os
import sys


def read_csv(path, encoding, **kw):
    with open(path, encoding=encoding, newline="", **kw) as f:
        return list(csv.DictReader(f))


def main(in_dir, out_dir):
    products = read_csv(os.path.join(in_dir, "products.csv"), "utf-8-sig")
    legacy = read_csv(os.path.join(in_dir, "legacy.csv"), "utf-8", errors="ignore")
    with open(os.path.join(in_dir, "config.json"), encoding="utf-8") as f:
        config = json.load(f)

    docs_in = os.path.join(in_dir, "docs")
    docs_out = os.path.join(out_dir, "docs")
    os.makedirs(docs_out, exist_ok=True)
    stems = []
    for name in sorted(os.listdir(docs_in)):
        stem = os.path.splitext(name)[0]
        with open(os.path.join(docs_in, name), encoding="utf-8") as f:
            first_line = f.readline().strip()
        with open(os.path.join(docs_out, stem + ".summary.txt"), "w", encoding="utf-8") as f:
            f.write(first_line + "\n")
        stems.append(stem)

    summary = {"title": config["title"], "products": products, "legacy": legacy, "docs": stems}
    with open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
