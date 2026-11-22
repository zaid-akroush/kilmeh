# Requirements

The system info table is Arabic and right-to-left, but the technical values inside the cells come out garbled: the leading slash of the file path, the version, the phone number groups and the brackets after the function name end up in the wrong place. Fix it in `index.html` and `styles.css`.

- The file path, the version, the phone number and the function name (`data-testid` `path`, `version`, `phone`, `fn`) must each read left to right inside, exactly as written.
- The table, its header and its cells stay right-to-left, and in each value cell the Arabic words stay on the right of the value, as in a normal Arabic sentence.
- The page stays right-to-left (`<html dir="rtl" lang="ar">`).
- Do not change the visible text or the `data-testid` attributes. Adding invisible direction marks (U+2066–U+2069, U+200E, U+200F) is allowed. Do not hide, mirror or rotate anything.
