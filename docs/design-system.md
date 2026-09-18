# Design system

Everything lives in `assets/css/site.css` — one file, 16 numbered sections, table of
contents at the top. Change a token, change the whole site.

## Palette

The three brand hexes are lifted directly from `logos/vidoori-logo.svg`, the only
authoritative brand source we control. Everything else is derived from them.

| Token | Hex | Role |
|---|---|---|
| `--brand-navy` | `#414372` | Wordmark and badge body. The primary brand colour. |
| `--brand-periwinkle` | `#BAC0D1` | Secondary, muted. |
| `--brand-green` | `#9AD389` | Accent highlight. |

Two derived ramps, `--navy-50` through `--navy-950` and `--green-50` through `--green-800`,
plus a neutral grey ramp.

### Panels must set foreground as well as background

Any component that hard-codes a `background` must hard-code a `color`. The brand sections set
a near-white `--text-on-brand` that inherits into children; a white-backgrounded panel dropped
inside one renders near-white text on white. This is not hypothetical — the referral form
shipped that way and measured 1.1:1 against a 4.5:1 requirement. `.form-shell` and the form
controls now set `color` explicitly. Links need the same treatment: `.section--brand a` is
pastel `--green-400`, which is unreadable on white.

### The one colour trap worth knowing

`--brand-green` (`#9AD389`) is a pastel. It is **not** accessible as text on white — roughly
2:1 contrast, well below the 4.5:1 threshold. So:

- Use `--brand-green` for **large graphic elements only**: the `.rule` accent bar, `.stat`
  top borders, SVG fills, and text on dark navy panels (where it *does* pass).
- For green **text, icons, and buttons on light backgrounds**, use `--green-700`
  (`#3f7a2c`) or `--green-800`. The `--accent` semantic token already points at `--green-700`.

The `.btn--accent` button uses `--green-700`, not the brand pastel, for exactly this reason.

### Semantic tokens

Prefer these over raw ramp values, since they are the seam a dark theme would use:
`--bg`, `--bg-alt`, `--bg-brand`, `--text`, `--text-muted`, `--text-on-brand`, `--border`,
`--accent`, `--focus`.

## Typography

A system font stack — no webfont request, no FOUT, native rendering everywhere.

The scale is fluid, built on `clamp()`:

```css
--step--1: clamp(0.83rem, 0.80rem + 0.15vw, 0.92rem);
--step-0:  clamp(1rem,    0.96rem + 0.20vw, 1.125rem);
--step-1:  clamp(1.20rem, 1.12rem + 0.40vw, 1.45rem);
--step-2:  clamp(1.45rem, 1.30rem + 0.75vw, 1.95rem);
--step-3:  clamp(1.75rem, 1.50rem + 1.25vw, 2.60rem);
--step-4:  clamp(2.10rem, 1.70rem + 2.00vw, 3.45rem);
--step-5:  clamp(2.50rem, 1.85rem + 3.25vw, 4.60rem);
```

Sizes interpolate with viewport width, so **there is not one font-size media query in the
stylesheet**. `h1`–`h6` map onto the scale automatically; use `.lede` for intro paragraphs
and `.eyebrow` for the small uppercase label above a heading.

`text-wrap: balance` on headings and `pretty` on paragraphs prevents typographic orphans.

## Spacing and layout

`--sp-1` (0.25rem) through `--sp-10` (8rem) on a 4px base.

- `--container` is `72rem` (1152px); `--container-narrow` is `46rem` for reading measure.
- `--gutter` is `clamp(1.25rem, 4vw, 2.5rem)` — page padding scales with viewport.
- `.section` supplies vertical rhythm via `padding-block: clamp(var(--sp-7), 8vw, var(--sp-9))`.
  Variants: `--tight`, `--alt` (grey), `--brand` (navy), `--brand-figured` (navy with gradient wash).

## Breakpoints

Only one breakpoint really matters: **`60rem` (960px)**, where the nav switches from a
stacked panel to a horizontal bar. Grids use `repeat(auto-fit, minmax(...))` and reflow
without any breakpoint.

```css
.grid      /* auto-fit, min 17rem   — general purpose */
.grid--2   /* auto-fit, min 22rem   — two wide cards / teasers */
.grid--4   /* auto-fit, min 14.5rem — four cards in one row at 1152px */
```

`.grid--4` exists because the default 17rem floor makes four cards total 1160px, which is 8px
wider than the container — so they wrapped 3 + 1. Use `.grid--4` for exactly-four-across rows.

## Component catalogue

### Heroes

- **`.hero`** — homepage only. Tall, gradient, plus a CSS-drawn grid via `.hero::before`
  masked with a radial gradient. Zero image bytes.
- **`.page-hero`** — every interior page. Same treatment, shorter.

The homepage hero is two columns: `.hero__inner--split` on `.hero__inner`, with the copy in
`.hero__copy` and a frosted `.hero__plate` beside it holding `.mark-draw` — the badge logo,
inlined as its four paths, tracing itself as an outline and then flooding with the brand
fills. The strokes fade at the end, so the resting state is the static logo exactly. Four
things about it are load-bearing:

- **The `--split` modifier lifts `.hero__inner`'s 52rem cap to `var(--container)`** — not to
  `none`, which would drop the `.container` cap too and let the hero run wider than every other
  section. This is what puts the copy on the same left margin as the rest of the page, and the
  plate's right edge on the same right margin.
- **It needs the plate.** The badge's largest lobe is filled `--navy-700`, the same value the
  hero gradient reaches, so on the bare hero that shape disappears. Re-inking it would mean
  altering the mark.
- **The plate is `display: none` by default** and turned on inside `@media (min-width: 64rem)`,
  rather than switched off in a `max-width` query. Stated this way the two rules cannot both
  apply at the breakpoint. Below 64rem the two columns would collide and squeeze the headline,
  so the badge goes rather than the layout bending around it.
- **The inline `<svg>` keeps its `width`/`height` attributes** purely for the intrinsic ratio.
  Strip them and it has no natural size, and the plate sizes against the browser's
  300&times;150 default.

There is no JavaScript: the keyframes run once on load, and because they end on the finished
logo, §16's blanket `prefers-reduced-motion` duration collapse lands on the correct resting
state rather than on an empty plate. Any future draw-on animation should keep that property.

The homepage `<h1>` is a single white phrase. It previously wrapped words in `<em>` to tint
them `--brand-green`; that rule is gone, and so is the `<em>`.

### Cards

```html
<article class="card card--link">
  <div class="card__icon" aria-hidden="true"><svg>…</svg></div>
  <h3><a href="/what-we-do/cloud-native/">Cloud-Native</a></h3>
  <p>Description.</p>
  <span class="link-arrow" aria-hidden="true">More about Cloud-Native</span>
</article>
```

`.card--link` makes the whole card clickable: the `<h3>`'s anchor is stretched over the card
with `a::after { inset: 0 }`. The visible "More about…" is a `<span>`, marked
`aria-hidden`, so assistive tech announces one link rather than two. Do not make it a second
`<a>` — that creates a duplicate link with the same destination.

### Other components

| Class | Use |
|---|---|
| `.split` | Two-column copy/figure. `--wide-start`, `--wide-end`, `--flip` for ratio and order. |
| `.figure-panel` | Gradient panel holding an inline SVG. `--dark` for the navy variant. **This is the slot for real photography later.** |
| `.split > .section-head` | A section head paired with a figure on one row; the modifier-free rule drops the head's bottom margin so the two stay centred against each other. |
| `.hero__plate` / `.mark-draw` | The badge logo animating itself beside the homepage hero copy. See Heroes above. |
| `.caps` | Capability checklist. Green ticks drawn with a rotated CSS border — no icon font, no per-item SVG. |
| `.def-list` | Heading-plus-paragraph groups. `--3` for three columns. |
| `.stats` / `.stat` | Figures with a green top rule. |
| `.record` | Certification / contract-vehicle entry: label column plus body column. |
| `.kv` | Key/value grid; values are monospaced. Add `.is-text` to a `<dd>` to opt out. |
| `.badge` | Category pill on a post's `.article-meta`. Auto-inverts inside `.section--brand-figured`. |
| `.cred-chip` / `.chip-row` | Credential label in the `.credential-card` idiom — squared, green top rule, uppercase type over value. Used where a pill read as a link. |
| `.callout` | One emphasised sentence with a green left rule. |
| `.cta-band` | Closing call to action. Nearly every page ends with one. |
| `.teaser` | Insights listing item. Generated for `/insights/`. |
| `.profile` | Person card. `.profile__avatar` holds initials — the stand-in for headshots. |
| `.prose` | Long-form body copy. Styles descendants directly, so write plain `<p>`/`<h2>`/`<ul>`. |

### Buttons

`.btn` plus one of `--primary` (navy), `--accent` (green, for the strongest action),
`--ghost` (outline, light backgrounds), `--onbrand` (outline, dark panels). Group with
`.btn-row`.

## Accessibility commitments

Do not regress these:

- **Focus.** A 3px `--focus` outline with 2px offset on `:focus-visible` throughout.
  `.card--link:focus-within` lifts the outline to the whole card.
- **Skip link.** `.skip-link` is the first element in `<body>`, targeting `#main`.
- **Nav.** Submenus are real `<button aria-expanded aria-controls>` disclosures, not
  hover-only CSS. Keyboard and touch both work; Escape closes.
  - **Gotcha:** the toggle's three bars must be children 1–3 of `.nav-toggle`, because the
    X animation uses `:nth-child()`. This is why the accessible name is an `aria-label` on
    the button rather than a `<span>` inside it. Adding any element inside that button will
    silently break the close icon.
- **Icons.** Decorative SVGs get `aria-hidden="true"`; meaningful ones get
  `role="img"` and an `aria-label` describing what they show.
- **Form errors.** `.field__error` slots carry `role="alert"`; invalid state is applied only
  after interaction, so nobody is scolded before typing.
- **Reduced motion.** `@media (prefers-reduced-motion: reduce)` collapses all transitions
  and disables hover lifts.
- **Contrast.** See the green trap above. Body text is `--navy-950` on white (~16:1).

## Print

`@media print` hides chrome, flattens the dark gradient heroes to black-on-white, and appends
`href` values after external links. Contract vehicle and capability pages are the ones people
actually print.

## Extending the system

1. **Look for an existing component first.** The catalogue above covers most needs.
2. **Use tokens, never literal hex or px.** A literal value is a future inconsistency.
3. **Add new rules to the matching numbered section** and update the table of contents.
4. **Avoid new breakpoints.** Reach for `clamp()`, `auto-fit`, or `minmax()` first.
5. **Check both themes of background.** Many components need a variant for dark navy panels
   (see how `.caps` and `.badge` invert inside `.section--brand-figured`).
