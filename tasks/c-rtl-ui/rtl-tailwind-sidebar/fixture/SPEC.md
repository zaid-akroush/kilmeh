# Requirements

`SPEC.md` is listed in `.gitignore`, so Tailwind does not scan it for class names. Keep it that way.

This Tailwind CSS v4 dashboard was built for left-to-right layout. Make it work in Arabic, right-to-left, using Tailwind's logical utilities, in `index.html` and `src/input.css`.

- The page language must be Arabic (`lang="ar"` or `lang="ar-JO"`) and the page direction right-to-left, set on the `<html>` element.
- Mirror the layout: the sidebar must sit at the right edge of the page and the main content must lie entirely to the left of it, without overlapping. Keep the sidebar visible and about 16rem wide, and do not hide, clip, shrink or scale anything.
- The layout must follow `<html dir>` alone: when only the `dir` attribute on `<html>` changes to `ltr`, the sidebar, the main content and the badge must mirror exactly. Use logical utilities such as `start-*`, `end-*`, `ms-*`, `ps-*`, `border-s`, `border-e`, `rounded-s-*` and `text-start`. Do not use any physical Tailwind utility (`left-*`, `right-*`, `ml-*`, `mr-*`, `pl-*`, `pr-*`, `border-l`, `border-r`, `rounded-l-*`, `rounded-r-*`, `text-left`, `text-right`), not even behind a variant such as `rtl:` or `ltr:`, and no physical CSS property (`left`, `right`, `margin-left`, `padding-right`, `border-left-width`, `text-align: left` and the like) anywhere in the compiled CSS, including `@apply`, arbitrary values, hand-written rules in `src/input.css` and `@import`ed styles. Logical utilities and logical properties (`inset-inline-start`, `margin-inline-end`, ...) are fine.
- Keep the page free of sideways scrolling on a 360 px wide screen.
- All styling must come from Tailwind classes and `src/input.css`. The page must link only `dist/app.css`, with no `<style>` element, no inline `style` attribute, no `<script>` and no other stylesheet. The grader rebuilds `dist/app.css` from your source (`tailwindcss -i src/input.css -o dist/app.css`) and ignores the `dist/` you leave behind, so editing `dist/app.css` by hand has no effect.
- Keep every `data-testid` attribute (and its element, visible) and the Arabic text as they are.
