# Requirements

This Arabic chat screen is a small React app, built for left-to-right layout. Make it work properly in Arabic, right-to-left. Edit the source in `index.html`, `src/` and `src/styles.css`; `npm run build` makes `dist/app.js` from `src/`.

- The page language must be Arabic (`lang="ar"` or `lang="ar-JO"`) and the page direction right-to-left (`dir="rtl"`), set on the `<html>` element.
- Follow the right-to-left chat convention (as in WhatsApp's Arabic interface): your own messages (`data-testid="bubble-me"`) sit on the left half of the screen, and incoming messages (`data-testid="bubble-them"`) on the right half.
- Each avatar (`data-testid="avatar"`) sits at the start (right) side of the incoming bubble it belongs to.
- The product name and the order number inside the Arabic messages (`data-testid="product"` and `data-testid="order"`) must display correctly, so that the surrounding Arabic text cannot reorder them.
- The composer (`data-testid="composer"`) must follow the language of what the user types: Arabic text reads right-to-left, Latin text left-to-right.
- The whole chat must switch fully to left-to-right when only the `dir` attribute on `<html>` changes, so the bubbles and avatars mirror. Use logical values (for example `marginInlineStart`, `insetInlineStart`, `text-align: end`, `margin-inline-start`) and no physical left or right values, in the stylesheet or in inline styles.
- The order details card (`data-testid="order-card"`) must fit a 360 px wide screen, and so must the page, with no horizontal scrolling. Do not hide the overflow (for example with `overflow-x: hidden`), do not shrink the card with `transform` or `zoom`, and keep it at least 200 px wide.
- The page is graded from a fresh build of a copy of `src/` alone, with the grader's own esbuild, react, react-dom and scheduler: changes in `dist/`, `node_modules/`, `package.json` or `tsconfig.json` do not count. CSS may be imported from JS (built to `dist/app.css`) or linked as `/src/styles.css`.
- `index.html` may contain only `html`, `head`, `meta` (charset or viewport), `title`, one stylesheet `link`, `body`, the root `div` and exactly one `<script src="/dist/app.js">` with no inline code; only `lang` and `dir` on `html`, `id` on the root, and the attributes already there. No iframe, object, embed, template, svg, base, event-handler attributes or `javascript:` URLs. The page may request only `/index.html`, `/dist/app.js` and the stylesheet, and must have no extra frame.
- Keep the `data-testid` attributes and the Arabic text as they are.
