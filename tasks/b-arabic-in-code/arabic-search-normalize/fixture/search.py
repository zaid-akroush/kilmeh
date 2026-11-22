"""Arabic-aware search and sort over contacts (stubs). See README.md for the rules."""


def normalize_for_search(s: str) -> str:
    """Return `s` in the search form described in README.md."""
    raise NotImplementedError


def search(records: list[dict], query: str) -> list[dict]:
    """Return the records whose name or city contains the query, comparing search forms."""
    raise NotImplementedError


def sort_names(names: list[str]) -> list[str]:
    """Return the names ordered by search form (ties by the original string)."""
    raise NotImplementedError
