# CLAUDE.md

Context and working instructions for Claude Code in this repo. **Updates to this site are
made through Claude**, often by people who have not worked on it before, so this file is
written to be the one thing you need to read to work here safely. Read it fully before
your first edit in a session.

---

## 1. What this is

The Vidoori corporate website — `vidoori.com`. Vidoori is an IT consulting firm founded in
2008 by Trong Khuong Bui, headquartered in Hyattsville, Maryland, serving **federal
government and commercial clients**. Tagline: *"We are dedicated to our client's mission."*
Positioning: *"We are solution focused and people driven."*

It is a **static site**: plain HTML, one CSS file, one small JS file, deployed on Cloudflare
Pages. **No Node, no framework, no package manager, no build step on deploy.** Cloudflare
serves the committed HTML as-is.

It was rebuilt in August 2026 from a legacy WordPress site. That history matters mainly
because **every URL the old site had must keep resolving** — see §7.

### Audience and tone
Federal contracting officers, program leads, and commercial buyers. Copy is plain, concrete,
and claim-light. Match the existing register: short declarative sentences, no marketing
superlatives, no exclamation marks, no emoji. Use en/em dashes as the existing copy does
(`&mdash;`) and curly quotes in body prose. American spelling.

---

## 2. THE RULE: never edit the generated HTML

**Do not edit `.html` files in the site root.** They are generated. Every one carries a
`GENERATED FILE - DO NOT EDIT DIRECTLY` banner naming its source. If you edit `index.html`,
`404.html`, or any `<section>/index.html` directly, the next build silently overwrites you.
`sitemap.xml` is generated too.

Edit `_src/`, then rebuild:

```bash
python3 tools/build.py
```

| To change | Edit |
|---|---|
| Page copy | `_src/pages/<page>.html` |
| Nav, footer links, contact details, Turnstile site key, social URLs | `_src/site.json` |
| `<head>`, header, footer — the shell all pages share | `_src/partials/base.html` |
| Colours, spacing, type | the token block at the top of `assets/css/site.css` |
| Nav behaviour, form validation | `assets/js/site.js` |
| Contact form backend | `functions/api/contact.js` |
| Redirects / response headers | `_redirects`, `_headers` |

`logos/` holds untouched brand originals — **never edit them**. `assets/img/` holds the
copies the site serves. If a logo is revised, update `logos/` then
`cp logos/*.svg assets/img/`.

---

## 3. Repository map

```
_src/                      SOURCE — this is what you edit
  site.json                  nav, footer, contact block, Turnstile site key
  partials/base.html         page shell: <head>, header, nav, footer
  pages/*.html               39 files: front matter + <main> content

tools/                     Python 3 stdlib only, never runs on deploy
  build.py                   _src/ -> committed HTML + sitemap.xml
  check_links.py             verifies internal links, assets, anchors
  build_capability_statement.py  facts -> assets/docs/Vidoori_CapabilityStatement.pdf
  logo-for-pdf.jpg           logo artwork the PDF embeds (see that script)
  import_posts.py            one-shot WordPress importer, kept as a record

assets/
  css/site.css               the entire stylesheet, 16 numbered sections
  js/site.js                 nav toggle, form validation, submit handling
  img/                       logos only (copies of logos/)
  docs/                      Vidoori_CapabilityStatement.pdf — the only PDF

functions/api/contact.js   Cloudflare Pages Function: Turnstile + Postmark
logos/                     brand originals — DO NOT EDIT
docs/                      human documentation, index at docs/README.md

index.html, 404.html, <section>/index.html, sitemap.xml   ALL GENERATED
_headers, _redirects       Cloudflare Pages configuration
```

---

## 4. Commands

```bash
python3 tools/build.py                                        # rebuild after editing _src/
python3 tools/build.py --check && python3 tools/check_links.py # MUST pass before you finish
```

```bash
python3 tools/build_capability_statement.py               # rebuild the capability statement PDF
```

```bash
python3 tools/build_capability_statement.py --check        # CI runs this
python3 tools/build_sewp_ordering_guide.py                 # rebuild the SEWP ordering guide
python3 tools/build_sewp_ordering_guide.py --check         # CI runs this too
```

The SEWP ordering guide is a **contract deliverable**: it must be republished within ten
business days of every contract modification. It is generated tagged to PDF/UA-1, which is
what Section 508 maps to for documents, and validates clean &mdash; 106 rules passed, 0 failed.
Re-validate after changing it:

```bash
verapdf -f ua1 --format text assets/docs/Vidoori_SEWP_VI_Ordering_Guide.pdf
```

That needs `brew install verapdf`; CI cannot run it, so CI only checks the committed PDF
matches the generator. Note PDF/UA forbids the base-14 font shortcut, so the guide embeds
Liberation Sans (SIL OFL, and metric-compatible with Helvetica so nothing reflows) &mdash;
which is why it is 481 KB where the capability statement is 27 KB.

`--check` is in `.github/workflows/verify.yml` alongside the other two. It fails if the
committed PDF does not match the generator, if the contract vehicles or core competencies
disagree with the built site, if a UEI/CAGE/NAICS value on the sheet is missing from
`/who-we-are/contract-vehicles/`, or if the layout overruns the footer. So when a vehicle,
certification or capability changes, update the `CONTENT` block at the top of the script and
re-run it &mdash; CI will not let the two drift apart silently the way they did before.

`--check` exits non-zero if generated HTML is stale — i.e. you edited `_src/` and forgot to
rebuild. `check_links.py` resolves every internal href against built files, directory
indexes, and `_redirects` rules; verifies asset paths and same-page anchors; and fails on
leftover `www.vidoori.com` absolute URLs or `/wp-` paths. **Do not report work as done until
both pass.** `.github/workflows/verify.yml` runs the same two commands on every push, so a
commit that skips them fails CI rather than reaching production.

To view the site, open the Browser pane using the `vidoori-static` config in
`.claude/launch.json` — do not launch a server with Bash. Note the contact form does **not**
work under a plain static server; it needs the Cloudflare Pages runtime (see
`docs/contact-form.md`).

---

## 5. How a page is built

Each file in `_src/pages/` is front matter, a `---` line, then the `<main>` content. The
build wraps it in `partials/base.html`.

```
title:        <title> and the JSON-LD name
description:  meta description and JSON-LD description
path:         URL it builds to, e.g. /what-we-do/cloud-native/  (trailing slash)
nav:          which top-level nav item highlights as current
schema:       WebPage | Article | Service | AboutPage | CollectionPage | ContactPage | none
robots:       optional; `noindex` adds a robots meta tag and drops the page from sitemap.xml
section:      Article only — category label shown on the card
date:         Article only — drives ordering on /insights/
serviceName:  Service only — the JSON-LD serviceType
---
```

Consequences worth knowing:

- **`schema: Article` is what makes something a post.** The `/insights/` index is generated
  from every page with that schema; there is no separate list to maintain.
- **JSON-LD and `sitemap.xml` are generated from front matter.** Never hand-write structured
  data, and never edit `sitemap.xml`.
- The build fails loudly on unreplaced `{{TOKENS}}` — if it errors, you have a typo in the
  partial or a missing front-matter key, not a broken tool.
- `path` determines where the file lands. A new `path` creates a new directory.

---

## 6. Design system essentials

Full detail in `docs/design-system.md`; this is what you need to avoid mistakes.

**Palette comes from the logo and is fixed:** navy `#414372`, periwinkle `#BAC0D1`, green
`#9AD389`. `site.css` derives full ramps (`--navy-50..950`, `--green-50..800`). **Always use
tokens, never raw hex.**

⚠️ **Two colour traps, both already shipped bugs once:**

1. `--brand-green` (`#9ad389`) is a pastel. It passes for large graphic elements but **fails
   text contrast**. For text or icons use `--green-700` or darker.
2. **Anything that sets its own `background` must also set its own `color`.** The dark
   sections (`.section--brand`, `.section--brand-figured`) set `color: var(--text-on-brand)`,
   which is near-white and inherits into any light-backgrounded child. A form placed in a
   brand section rendered typed text at **1.1:1** against its own white input background —
   invisible. `.form-shell` and `.input/.select/.textarea` now set `color` explicitly, and
   `.form-shell` resets link colour too (brand-section links are pastel green, unreadable on
   white). Apply the same rule to any new panel component.

**Asset URLs are version-stamped.** `tools/build.py` appends `?v=<content hash>` to the
`site.css` and `site.js` references in every page, so changing either file changes its URL and
the new version reaches visitors immediately. Do not hand-write those references without the
stamp. This exists because Cloudflare was observed serving a five-day-old `site.js` from the
edge: the zone's Browser Cache TTL was set to 5 days and silently overrode `_headers`. That
setting is now "Respect Existing Headers" and the served TTLs match the file — but the stamp
is the guarantee, since images and PDFs carry no version.

Locally there is still no cache busting for a file you edit *without* rebuilding:
`python3 -m http.server` sends no cache headers, so browsers cache heuristically. **If a JS
change appears to have no effect, rebuild and hard-reload before you doubt the code** — this
has already cost one debugging session.

**Reuse existing components — new CSS is a last resort.** The vocabulary:

- Layout: `.container`, `.container--narrow`, `.section`, `.section--alt`, `.section--tight`,
  `.section--brand`, `.split`, `.grid`, `.grid--2`, `.grid--4`, `.stack`
- Blocks: `.card`, `.teaser`, `.profile`, `.record`, `.def-list`, `.caps`, `.callout`,
  `.cta-band`, `.stat`, `.figure-panel`, `.table-wrap`, `.kv`, `.cred-chip` (in a `.chip-row`)
- Type: `.lede`, `.eyebrow`, `.muted`, `.prose`, `.rule`, `.section-head`, `.breadcrumb`
- Actions: `.btn` + `.btn--primary` / `--ghost` / `--accent` / `--onbrand`, `.btn-row`,
  `.link-arrow`
- Spacing utilities: `.mt-0`, `.mt-5`, `.mt-6`, `.mt-7`
- Placeholders: `.tbd` — a conspicuous dashed chip for a value the business still has to
  supply. Unused since the SEWP page was completed, and kept on purpose: wrap any missing
  fact in `<span class="tbd">` rather than guessing it, so a reviewer sees the gap at a
  glance. Remove each span as the real value arrives.

**Image-light by design (ADR 2, amended 2026-09-18).** No icon font. Diagrams are markup or
hand-written inline SVG with a `role="img"` and a descriptive `aria-label` — never a raster,
because a diagram is mostly text and text in an image cannot reflow. Illustration *is* now
allowed, but only if it is AI-generated or otherwise unambiguously ours, shows no identifiable
person, is sized to no more than 2× what the container actually renders at, ships as WebP, and
carries real `alt` text with matching `width`/`height`. Read the ADR 2 amendment before adding
one. Note images carry no `?v=` stamp, so a revision needs a new filename or the edge serves
the old file.

**Accessibility is a commitment, not a nice-to-have:** semantic landmarks, a skip link,
visible focus states, `aria-current` on the active nav item, labelled form fields with
`aria-describedby` error text. Keep it.

---

## 7. URL preservation — read before deleting anything

The rebuild's contract is that **no URL the WordPress site had may 404** (ADR 3). `_redirects`
carries ~30 rules that exist solely to honour that, and `docs/content-catalog.md`'s appendix
is the record of what the old site contained — that appendix is *why* the rules exist, so
leave it alone.

If you remove or rename a page, add a `_redirects` rule pointing the old path somewhere
sensible, and tell the user you did.

### Removing content is never one edit

Content is cross-referenced in ways grep-by-name will miss. Work the whole footprint:

1. `grep -rin "<thing>" _src/ docs/ _redirects` — catches links, `site.json` nav entries,
   teaser cards on parent/index pages, and **meta descriptions**, which routinely advertise
   things the body no longer mentions.
2. Delete the generated directory too (`rm -rf <section>/`), not just the `_src/` page.
3. Add the `_redirects` rule.
4. Rebuild and run both checks.
5. Look for **structures left empty**: a removed lone button leaves an empty `.btn-row`; a
   removed list item can leave a heading with nothing under it; a removed section can leave a
   plural heading describing one item.
6. Ask whether prose elsewhere is now false — "Two platforms…" when only one remains.

Historical content is different from live content. A press release quoting a former employee
is an accurate record and should stay; a *live* "contact this person at this address" line for
someone no longer listed is stale and should be repointed at `info@vidoori.com` or `/contact/`.

---

## 8. Facts about the site

39 pages: 21 pages + 18 posts. `docs/content-catalog.md` is the authoritative inventory —
what the site says and where each fact lives. Check it before hunting through files.

**Nav:** Who We Are · What We Do · Solutions (VPT only, external) · Insights · Careers.
`/contact/`, `/privacy-policy/`, `/terms-of-use/` are footer-only.

**Practices:** Cloud-Native, Software Development, DevSecOps, Integration & Test. They appear
in that order in three places that must agree: the homepage cards, `/what-we-do/`, and the
footer's What We Do column in `_src/site.json`. That order is also the order of the four nodes
in the continuous-delivery SVG, which is duplicated in `home.html` and `what-we-do.html` —
change one and you must change the other.

Data Management, Cybersecurity, Intelligence and Strategy were retired on 2026-09-18 and their
URLs 301 to `/what-we-do/`. Cloud-Native was promoted out of what used to be a supporting tier;
the Core/Supporting split no longer exists.

**Leadership:** Trong Khuong Bui (Founder & CEO) and Eric Huang (Chief Strategy Officer).
There is no Board of Advisors. **The Vidoori Team page is hidden** (see §12 item 7); while it
is, the ten legacy per-person bio URLs 301 to `/who-we-are/` rather than to it.

**Corporate facts** live in `_src/site.json` and flow into the footer and JSON-LD — change
them there, never in page copy: `info@vidoori.com`, `contracts@vidoori.com`,
(240) 608-6810, 4000 Garden City Drive, Suite 808, Hyattsville, MD 20785.
UEI `N37JST95C3S5`, CAGE `6T0A7`. Contract vehicles: GSA MAS `GS-35F-335CA` (SINs `54151S` and `511210`), SeaPort-NxG, FAA eFAST
`693KA9-22-A-00186` (Master Ordering Agreement; CSD and CSS functional areas), and NASA SEWP VI
`80TECH26D1457` (Category C &mdash; ITC/AV Mission-Based Services, awarded 2026-07-02, effective 2026-11-01). SEWP VI has its own page at
`/who-we-are/contract-vehicles/nasa-sewp-vi/`, short link `/sewp`, because the contract requires a
published contract-holder page; see §4 for its ordering guide, a contract deliverable.
GSA 8(a) STARS III (`47QTCB22D0131`) and OASIS expired and were removed from the live site
on 2026-09-18; the 2022 STARS III award announcement stays as a historical record.

**External properties:** VPT platform `vpt.vidoori.com/about`, careers ATS
`vidoori.teamtailor.com/jobs`.

---

## 9. Forms

**Two forms, same machinery.** `/contact/` posts to `functions/api/contact.js`;
`/careers/#referral` posts to `functions/api/referral.js`. Each layers: honeypot field
(`website`) → submit-timing check (`started_at`) → Turnstile verification → server-side
validation (authoritative; the client-side copy in `site.js` is only UX) → Postmark send.

`referral.js` is a deliberate near-copy of `contact.js`. **Change the bot checks, the
Turnstile call, or the Postmark call in one and you must change the other.**

Client-side, both are driven by the same generic `initAsyncForm()` in `site.js`, which picks
up any `<form data-async>`. A form opts in with `data-async`, a `.form-status` paragraph
*inside* the form, `data-label` on each control, and optionally `data-minlen` /
`data-error-message`. Nothing in that layer is form-specific — do not reintroduce an id-based
lookup.

Environment variables, set in Cloudflare Pages, **never committed**:
`POSTMARK_SERVER_TOKEN`, `TURNSTILE_SECRET_KEY`, `CONTACT_TO_EMAIL`, `CONTACT_FROM_EMAIL`,
optionally `POSTMARK_MESSAGE_STREAM` and `CONTACT_BCC_EMAIL`.

The Turnstile **site** key in `_src/site.json` is public and safe to commit; it holds the
live widget for `vidoori.com`. Because it is a real widget, verification fails on hostnames
not on the widget's list — `localhost` is not, so the form cannot be validated under a plain
local server. Test on a preview deployment or `test.vidoori.com`.

If you change form fields, change them in three places or the form breaks: the markup in the
page, the client validation in `assets/js/site.js`, and the server validation in the Function
(`LIMITS`, `validate()`, and the `rows` array in `buildEmail()`).

Any page carrying a form needs the Turnstile script via `head:` front matter — `careers.html`
and `contact.html` both declare it. Add a form to a third page and you must add that too, or
the widget never renders and every submission fails verification.

---

## 10. Deployment

Cloudflare Pages. Build command **empty**, output directory `/`. Every push to `main`
publishes to production; other branches get preview deployments. `_headers` sets a deliberately
tight CSP (the only third-party origin is `challenges.cloudflare.com` for Turnstile) plus
HSTS, `X-Frame-Options: DENY`, and a restrictive `Permissions-Policy`.

**If you add any third-party script, embed, font, or image host, the CSP in `_headers` must be
updated or it will be blocked in production but work fine locally.** This is the single most
likely way to ship a silently broken page.

Details and the rollback procedure: `docs/deployment.md`.

---

## 11. Keep the docs honest

These files duplicate facts from `_src/`, so they drift. **`_src/` wins.** Update them in the
same change, not later:

- `docs/content-catalog.md` — site inventory. Update the current-site half; the legacy
  appendix is frozen.
- `docs/known-issues.md` — open items needing a human decision. If your work resolves one,
  mark it resolved with a short note rather than deleting it.
- Page counts appear in `README.md` and `docs/architecture.md`. If you add or remove a page,
  update them.

---

## 12. Open items (as of 2026-10-02)

`docs/known-issues.md` is the full list and carries the detail. What remains:

**Infrastructure and configuration**

1. **Apex → www redirect is not in place.** `origin` is `https://www.vidoori.com`, so
   canonicals point at the www host. If both `vidoori.com` and `www.vidoori.com` are added as
   Pages custom domains without a redirect, both serve the site. **`_redirects` cannot fix
   this** — it is path-only and cannot redirect across hostnames. It must be a Cloudflare
   Redirect Rule or Bulk Redirect at the zone level. Issue 23.
2. **`CONTACT_TO_EMAIL` points at an individual**, not a shared mailbox. Worth changing before
   the www cutover so inquiries and referrals do not depend on one person's inbox. Issue 24.
3. **`test.vidoori.com` is publicly crawlable.** Canonicals point at production, which covers
   most of the risk. A `X-Robots-Tag: noindex` Transform Rule scoped to that hostname would
   close it; the owner has decided against Cloudflare Access. Issue 25.
4. **`logos/` and `assets/img/` hold byte-identical SVGs.** Accepted. If a logo changes,
   update `logos/` then `cp logos/*.svg assets/img/`. Issue 10.
5. **`main` is not protected.** The repo moved to the `vidoori` org on 2026-09-15 so a
   pull-request workflow could be enforced, but the org is on GitHub Free, where rulesets are
   configurable and *not enforced* on private repos. Enforcement needs GitHub Team, billed per
   org member. Until it is settled — upgrade, make the repo public, or rely on convention —
   `main` is protected by agreement only, and every push to it deploys to production.
   Issue 17.

6. **The referral program has no linked T&Cs.** Deferred to HR and Legal by the owner on
   2026-10-02; the site launches with the program rules as they stand. Issue 7.
7. **The Vidoori Team page is hidden, not deleted &mdash; pending discussion.**
   `/who-we-are/leadership/` still builds and resolves, but every link to it was removed on
   2026-10-02, it carries `robots: noindex` (meta tag plus `X-Robots-Tag` in `_headers`), and
   it is out of `sitemap.xml`. Do not delete it, and do not link to it, until the owner
   decides. Issue 22 lists what to undo to restore it.

**Content decisions** &mdash; closed as of 2026-09-18, kept here so they are not re-raised

8. ~~**The capability statement PDF still lists 8(a) STARS III.**~~ Closed 2026-09-18. The
   PDF is now generated by `tools/build_capability_statement.py` and agrees with the site.
   CI now enforces agreement via `build_capability_statement.py --check`. The NAICS
   follow-up under issue 18 is also closed: `519190` was corrected to `519290` against the
   SAM.gov registration.
9. ~~**The homepage tagline was replaced.**~~ Accepted by the owner 2026-09-18, along with the
   6-9 month rotation figure on `/vail/`. Both are deliberate; do not re-raise them. Issue 13.
10. ~~**A raster image was added to the homepage**, contradicting ADR 2.~~ Closed 2026-09-18.
   Re-encoded to 1200x900 WebP (1994 KB to 86 KB), and ADR 2 amended to permit illustration
   under stated conditions rather than ban it. Issue 14.
11. ~~**Leadership bios are uneven in length.**~~ Accepted 2026-09-18, along with the two ways
   `/vail/` describes its intake (&ldquo;college graduates&rdquo; in body copy,
   &ldquo;juniors and new hires&rdquo; in the diagram). Both are deliberate; do not re-raise
   them. Issue 15.

## 13. Working expectations

- **Verify, don't assume.** Rebuild and run both checks. Where a change is visible, look at
  the rendered page in the Browser pane rather than trusting the diff.
- **Report honestly.** If a check fails, say so with the output. If you skipped part of a
  request, say which part and why.
- **Do not introduce dependencies.** No `package.json`, no bundler, no CSS framework, no
  CDN script. If a task seems to need one, stop and say so — that is an architectural
  decision for the owner, not a side effect of a content edit.
- **Do not commit or push unless asked.**
- **Flag rather than silently guess** on facts about the business — addresses, contract
  numbers, titles, award placements, certifications. Inherited inconsistencies are recorded
  in `docs/known-issues.md` precisely because guessing is worse than asking.

## Further reading

`docs/README.md` is the index. `docs/architecture.md` records seven ADRs and a "what we
deliberately did not build" list — it will usually answer "should I add X?" before you ask.
