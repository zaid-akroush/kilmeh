# Requirements

This Arabic order summary page is already right-to-left, but several things still break in Arabic. Fix them in `index.html` and `styles.css`.

- The back and next arrow icons must point the correct way for right-to-left reading.
- The logo and the play icon must not be mirrored.
- The order number, phone number, username and price inside the Arabic sentences must display correctly, so that surrounding text cannot reorder them.
- The email and phone fields must read left to right. The name field must follow the language of what the user types.
- The order summary table itself must fit a 360 px wide screen, with no horizontal scrolling of the table or of the page. Do not hide the overflow (for example with `overflow-x: auto` or `hidden` on a wrapper), and do not shrink the table with `transform` or `zoom`.
- Keep the SVG markup and the `data-testid` attributes as they are; flip the arrows with CSS.
