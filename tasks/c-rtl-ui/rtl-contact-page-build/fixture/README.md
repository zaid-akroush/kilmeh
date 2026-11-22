# Contact page (build from scratch)

Build an Arabic contact page in `index.html` and `styles.css`. `index.html` is a placeholder and
`styles.css` is empty. Use no JavaScript, no framework and no network resource.

## Elements (every `data-testid` below is required, exactly as spelled)

| `data-testid` | Element | Content |
|---|---|---|
| `page-header` | `<header>` | holds the logo and the nav |
| `logo` | `<a>` in the header | Arabic text, at the start of the header |
| `nav-link` (3 times) | `<a>` inside `<nav>` in the header | three Arabic links, in reading order |
| `contact-text` | `<p>` | an Arabic sentence that contains both runs below |
| `phone-text` | inline element inside `contact-text` | the text `+962 7 9123 4567` |
| `email-text` | inline element inside `contact-text` | the text `info@example.com` |
| `contact-form` | `<form>` | holds the three fields |
| `name` | `<input>` | the name field |
| `email-input` | `<input type="email">` | the email field |
| `phone-input` | `<input>` | the phone field |
| `next` | `<button>` | Arabic text followed by the arrow below |
| `next-icon` | the arrow `<svg>` inside `next` | markup below, unchanged |

## Arrow markup (paste it unchanged; make it point the right way with CSS only)

```html
<svg class="icon icon-arrow" data-testid="next-icon" width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
          <line x1="2" y1="10" x2="14" y2="10" stroke="currentColor" stroke-width="2"/>
          <g data-part="head"><polyline points="12,4 18,10 12,16" fill="none" stroke="currentColor" stroke-width="2"/></g>
        </svg>
```

It is drawn pointing right, the way a "next" arrow points in a left-to-right page.
