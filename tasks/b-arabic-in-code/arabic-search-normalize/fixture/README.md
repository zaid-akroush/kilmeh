# search

Arabic-aware search and sort over contacts.

- `contacts.py`: `CONTACTS`, a list of `{"id", "name", "city"}` records.
- `search.py`: `normalize_for_search(s)`, `search(records, query)` and `sort_names(names)` (stubs).

Standard library only.

## Examples

```python
from contacts import CONTACTS
from search import normalize_for_search, search, sort_names

normalize_for_search("مُحَمَّد") == "محمد"
[r["id"] for r in search(CONTACTS, "محمد")] == [8, 9]
[r["id"] for r in search(CONTACTS, "ﷲ")] == [21]
sort_names(["ب", "ا", "أ"]) == ["أ", "ا", "ب"]
```
