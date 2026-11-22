"""Reference ingest.py (solve.sh copies this file over /app/ingest.py).

products.csv is UTF-8 with a BOM (utf-8-sig), legacy.csv is Windows-1256, JSON is written with
ensure_ascii=False, and output file names keep the Arabic stem.
"""

import csv
import json
import os
import sys


def read_csv(path, encoding):
    with open(path, encoding=encoding, newline="") as f:
        return list(csv.DictReader(f))


def main(in_dir, out_dir):
    products = read_csv(os.path.join(in_dir, "products.csv"), "utf-8-sig")
    legacy = read_csv(os.path.join(in_dir, "legacy.csv"), "cp1256")
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
        json.dump(summary, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
