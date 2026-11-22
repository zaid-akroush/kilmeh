# Requirements

This Arabic landing page was built for left-to-right layout. Fix it so it works properly in Arabic, right-to-left, in `index.html` and `styles.css`.

- The page language must be Arabic (Jordan) and the page direction right-to-left, set on the `<html>` element.
- The layout must mirror correctly: the logo at the right end of the header, the sign-in button at the left end, and the navigation links ordered right to left.
- The page must switch fully to left-to-right when only the `dir` attribute on `<html>` changes. Use CSS logical properties (for example `margin-inline-start`, `text-align: start`) instead of left and right.
- Keep the page readable on a 360 px wide screen, with no sideways scrolling.
- Keep the `data-testid` attributes and the Arabic text as they are.
