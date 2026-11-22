# Requirements

The notifications are Arabic sentence templates with user names, product names and order numbers filled in (`.slot`). When a filled-in value is in Latin letters, the numbers and punctuation next to it jump to the wrong place. Fix it in `index.html` and `styles.css`.

- Every `.slot` value must be isolated from the sentence around it, so that a number or punctuation mark next to it stays where it belongs in the Arabic sentence.
- Every value keeps its own direction: a Latin value (`Notes++`, `#A-1024`) reads left to right with its punctuation in place, an Arabic value reads right to left.
- The sentences and the page stay right-to-left (`<html dir="rtl" lang="ar">`).
- Do not change the visible text or the `data-testid` attributes. Adding invisible direction marks (U+2066–U+2069, U+200E, U+200F) is allowed. Do not hide, mirror or rotate anything.
