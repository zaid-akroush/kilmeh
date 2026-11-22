"""Mutation for arabic-digits-parse-format: a bounded grouping regex, (SEP ddd){1,4}.

Runs in the app directory on top of the reference solution. Input with five or more grouping
separators is rejected; only parse_grouping uses it (the round trip stays under 10^15).
"""

from pathlib import Path

Path("numerals.py").open("a", encoding="utf-8").write("""

_mutated_parse = parse_number


def parse_number(text):
    if text.count(",") + text.count("\\u066c") >= 5:
        raise ValueError("mutation: at most four groups")
    return _mutated_parse(text)
""")
