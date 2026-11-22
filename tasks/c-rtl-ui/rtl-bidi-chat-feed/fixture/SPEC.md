# Requirements

This Arabic comment feed is right-to-left, but the message text shows in the wrong order. Users write in Arabic, in English, or both, and paste links and phone numbers. Fix it in `index.html` and `styles.css`.

- Each message text (`.text`) must take its own base direction from its first strong letter: a message that starts with an Arabic word reads right to left, a message that starts with an English word or a link reads left to right. Words, numbers and links inside a message must stay in the order the user typed them.
- The page and the feed stay right-to-left (`<html dir="rtl" lang="ar">`).
- Do not change the visible text (messages and authors) or the `data-testid` attributes. Adding invisible direction marks (U+2066–U+2069, U+200E, U+200F) is allowed. Do not hide, mirror or rotate messages.
