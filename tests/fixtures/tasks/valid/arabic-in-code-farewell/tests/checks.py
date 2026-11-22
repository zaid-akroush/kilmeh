"""Pure byte-level integrity checks shared by the Harbor verifier and the Inspect scorer.

Inputs are raw bytes; nothing here decodes-then-re-encodes the originals.
"""
import unicodedata

BOM = b"\xef\xbb\xbf"
BIDI = set("‎‏⁦⁧⁨⁩")


def lines(b: bytes):
    return b.split(b"\n")


def is_subsequence(orig_lines, new_lines):
    it = iter(new_lines)
    return all(any(o == n for n in it) for o in orig_lines)


def bidi_positions(b: bytes):
    """(line_index, char_offset_in_line, codepoint) of each bidi control."""
    out = []
    for i, ln in enumerate(lines(b)):
        s = ln.decode("utf-8")
        for j, ch in enumerate(s):
            if ch in BIDI:
                out.append((i, j, hex(ord(ch))))
    return out


def check_integrity(orig_py: bytes, new_py: bytes, orig_readme: bytes, new_readme: bytes, names):
    """Return dict name -> bool."""
    r = {}
    r["no_bom"] = not new_py.startswith(BOM)
    r["valid_utf8"] = True
    try:
        new_py.decode("utf-8")
    except UnicodeDecodeError:
        r["valid_utf8"] = False
    r["orig_lines_byte_identical"] = is_subsequence(lines(orig_py), lines(new_py)) if r["valid_utf8"] else False
    # bidi controls: every original (line text, offset, cp) still present, in the same line content
    r["bidi_controls_preserved"] = (
        r["valid_utf8"]
        and sum(new_py.decode().count(c) for c in BIDI) >= sum(orig_py.decode().count(c) for c in BIDI)
        and all(any(ln == o for o in lines(new_py)) for ln in lines(orig_py) if any(c in ln.decode() for c in BIDI))
    )
    r["nfkc_sensitive_char_kept"] = "ﷲ".encode() in new_py
    r["readme_unchanged"] = new_readme == orig_readme
    nfc_name = unicodedata.normalize("NFC", "تحية.py")
    r["filename_present_exact"] = nfc_name in names and "تحية.py" in names
    return r
