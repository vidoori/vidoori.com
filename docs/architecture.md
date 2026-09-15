# Architecture and decisions

Written during the August 2026 rebuild that replaced the WordPress site.
Each decision records *why*, so a future maintainer (human or Claude) can tell the
difference between a deliberate constraint and an accident.

## Goals we were given

1. Replace WordPress — the driving motive was its vulnerability surface.
2. Plain HTML, CSS, and JS with minimal external dependencies.
3. Deploy via GitHub and Cloudflare Pages, with no Node or other build tooling.
4. Fast, and responsive across desktop and mobile.
5. Keep the contact form working, sending through the existing Postmark account.

Everything below follows from those five.

---

## ADR 1: A local generator rather than hand-maintained headers

**Status:** accepted, with a caveat worth re-reading before you change it.

**Context.** The site is 42 pages. Every page needs the same `<head>`, header, nav, and
four-column footer. The brief said "basic HTML/CSS/JS website," which most directly implies
writing each page as a complete standalone file.

**The problem with the literal reading.** With one copy of the nav per page, adding one menu
item is 40-odd edits. In practice a few get missed and the nav quietly diverges page to page. That is a
maintenance defect, and it gets worse as the site grows.

**Alternatives considered.**

| Option | Why not |
|---|---|
| 40-odd standalone files | Nav/footer drift is a near-certainty. Rejected. |
| Client-side include (`fetch` the header into every page) | Header flashes in after paint, breaks without JS, and search engines see an empty shell. Rejected outright — this is a marketing site whose SEO matters. |
| A static site generator (Eleventy, Hugo, Astro) | Reintroduces exactly the toolchain the brief excluded. Rejected. |
| **A ~250-line Python script that stamps shared chrome into committed HTML** | **Chosen.** |

**Decision.** `tools/build.py` reads `_src/` and writes ordinary `.html` files, which are
committed. Cloudflare Pages has **no build command** and runs **no Node** — it serves the
committed files exactly as they are.

**Why this still honours the brief.** The deployed artifact is plain static HTML. The
constraint was about the deploy pipeline and the runtime dependency surface, and both stay
clean. Python 3 ships with macOS and every Linux box; the script uses only the standard
library.

**The caveat — this is the one real downside.** There are now two places a page could be
edited: the source in `_src/pages/` and the generated file in the site root. Someone who
edits the generated file will see their change work, then lose it at the next build.
Mitigations in place:

- Every generated file opens with a `GENERATED FILE - DO NOT EDIT` banner naming its source.
- `python3 tools/build.py --check` exits non-zero when committed HTML is stale, so CI or a
  pre-commit hook can catch drift.
- The README leads with this warning.

**If you ever want to drop the generator:** run `python3 tools/build.py`, delete `_src/` and
`tools/build.py`, and carry on editing the HTML by hand. The output is clean, readable,
dependency-free HTML. Nothing about the deployed site depends on the generator existing.

---

## ADR 2: Image-light, with graphics drawn in CSS and inline SVG

**Status:** accepted (explicitly chosen by the site owner).

**Context.** The WordPress site used a hero video (`Vidoori-Home-Hero-4.mp4`) and roughly
103 uploaded images. We did not have those source files locally, and their licensing was
unverifiable — stock photography on the old site could not be traced to a licence.

**Decision.** No photographic imagery. The visual identity is built from:

- the brand palette taken from `logos/*.svg`,
- layered CSS gradients for hero and panel backgrounds,
- a faint CSS-drawn grid (`.hero::before`) that supplies "technical" texture at zero bytes,
- hand-authored inline SVG diagrams that carry actual meaning (the 1:10:100 quality rule,
  the DevSecOps loop, monolith-to-microservices, the portfolio dashboard).

**Consequences.**

- The site ships no raster images at all. Total page weight is dominated by one 30 KB
  stylesheet.
- No licensing exposure, no image pipeline, no responsive-image markup to maintain.
- The inline SVGs are decorative *and* informative, which is better than stock photos of
  people at laptops.
- If real photography is added later, `.figure-panel` is the slot designed to hold it —
  swap the inner `<svg>` for a `<picture>` and the layout is unchanged.

---

## ADR 3: URL structure preserves every legacy path

**Status:** accepted.

**Context.** The old site had indexed URLs with category prefixes:
`/news/navsup-contract-awarded/`, `/cybersecurity/basics-of-test-data-management/`. A
tidier scheme would be `/insights/<slug>/`.

**Decision.** Keep the legacy paths exactly. Tidiness is not worth discarding accumulated
search ranking and inbound links from press coverage.

Where a legacy URL genuinely has no equivalent, `_redirects` issues a 301:

- 10 individual leadership bio pages → the consolidated `/who-we-are/leadership/`
- WordPress taxonomy archives (`/category/*`, `/tag/*`, `/author/*`) → `/insights/`
- WordPress plumbing (`/wp-admin/*`, `/xmlrpc.php`, `/wp-json/*`) → `/`
- Legacy PDF paths under `/wp-content/uploads/` → `/assets/docs/`

`tools/check_links.py` treats a `_redirects` rule as a valid link target, so redirects and
real pages are both verified.

---

## ADR 4: Progressive enhancement, not a JS dependency

**Status:** accepted.

`assets/js/site.js` is ~280 lines of plain ES2019 with no build step, loaded with `defer`.
Everything it does is an enhancement:

- **Navigation.** `<html>` carries `class="no-js"`, swapped to `js` by a tiny inline script
  in `<head>` before first paint (so the mobile panel never flashes open). With JS
  unavailable, `.no-js .site-nav` renders the nav as a permanently expanded link list and
  hides the toggle. The nav is fully usable either way.
- **Contact form.** The `<form>` has a real `action="/api/contact"` and `method="post"`.
  With JS, submission is intercepted and posted as JSON for inline feedback. Without it,
  the browser posts natively and the Pages Function returns a styled HTML confirmation.
  The endpoint content-negotiates on `Accept`.
- **Form validation.** Client-side validation is UX only. `functions/api/contact.js`
  re-validates everything and is the authority.

One consequence worth knowing: the mobile nav markup is identical at every breakpoint. CSS
decides whether it looks like a horizontal bar or a stacked panel. There is no duplicate
"mobile menu" markup to keep in sync.

---

## ADR 5: Cloudflare Turnstile for spam, layered over cheap heuristics

**Status:** accepted (chosen by the site owner over a dependency-free option).

Turnstile is the single third-party script on the site, loaded only on `/contact/`. It was
preferred over reCAPTCHA (the WordPress site's choice) because it is privacy-friendlier and
stays within the existing Cloudflare vendor relationship.

Underneath it, `functions/api/contact.js` also applies two checks that cost nothing:

1. **Honeypot** — a `website` field hidden with `.hp` (positioned off-screen, `tabindex="-1"`).
   Real users never see or focus it; naive bots fill it.
2. **Timing** — the form stamps `started_at` on render. Submissions faster than 3 seconds
   are rejected. Submissions older than 12 hours are asked to reload.

Bot rejections return **success** to the caller rather than an error. A bot that learns it
was blocked adapts, and a false positive should never show a real person an error.

---

## ADR 6: One stylesheet, design tokens, no framework

**Status:** accepted.

`assets/css/site.css` is a single ~30 KB file organised into 16 numbered sections with a
table of contents at the top. No Tailwind, no Bootstrap, no preprocessor.

- **Tokens.** Custom properties at `:root` define the palette, a fluid type scale built on
  `clamp()`, spacing, and effects. Change a token, change the whole site.
- **Fluid type.** The scale uses `clamp()` so type sizes interpolate with viewport width.
  There is not a single font-size media query in the file.
- **Fonts.** A system font stack. No Google Fonts request, no FOUT, no third-party
  connection, and it renders natively on every platform.
- **Breakpoints.** Only two matter: `60rem` for the nav, and a handful of layout grids that
  use `repeat(auto-fit, minmax(...))` and therefore need no breakpoint at all.

**Light theme only.** Dark mode was not requested. The token structure would make it
straightforward — redefine the semantic tokens (`--bg`, `--text`, `--border`, …) inside
`@media (prefers-color-scheme: dark)` — but the brand navy is a dark colour already used as
a background, so a dark theme needs real design attention rather than a mechanical inversion.
Not something to bolt on casually.

---

## ADR 7: Structured data and the sitemap are generated, not written

**Status:** accepted.

Both are derived in `tools/build.py` from page front matter:

- **JSON-LD.** Every page carries an `Organization` node (address, contact, certifications
  context). Pages add a second node by declaring `schema:` in front matter — `Article`,
  `Service`, `ContactPage`, `AboutPage`, `CollectionPage`. Federal buyers and search engines
  both benefit from the organisation details being machine-readable.
- **`sitemap.xml`.** Built from the rendered page list, with `lastmod` from each post's date
  and priority derived from path depth. The 404 page is excluded.
- **The Insights index.** `/insights/` is assembled from every page whose schema is
  `Article`, newest first. Add a post and it appears automatically; there is no second list
  to forget.

`--check` verifies the sitemap alongside the pages.

---

## What we deliberately did not build

- **A CMS.** Content changes are a text edit and a commit. Adding a CMS would recreate the
  problem we were asked to solve.
- **Analytics.** Nothing was requested and nothing was added. If it is wanted later,
  Cloudflare Web Analytics needs no cookies and no client script, which keeps the privacy
  policy accurate. Note that the policy currently states the site does not use tracking
  cookies — any analytics choice must keep that true or the policy must change.
- **A search feature.** At 42 pages it would cost more than it returns.
- **Image optimisation tooling.** There are no images to optimise. See ADR 2.
