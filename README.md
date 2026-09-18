# vidoori.com

The Vidoori corporate website. Static HTML, CSS, and vanilla JavaScript, deployed on
Cloudflare Pages. No Node, no framework, no package manager.

```bash
# Preview locally (Python 3 is the only requirement)
python3 -m http.server 8788

# After editing anything in _src/, regenerate the HTML
python3 tools/build.py

# Verify nothing is broken before committing
python3 tools/build.py --check && python3 tools/check_links.py
```

Then open <http://localhost:8788>.

> **Note:** the contact form does not work under `python3 -m http.server` — it needs the
> Cloudflare Pages runtime. See [docs/contact-form.md](docs/contact-form.md) for how to
> test it locally.

## Read this first

**Do not edit the `.html` files in the site root directly.** They are generated. Every one
carries a `GENERATED FILE - DO NOT EDIT` banner at the top pointing back at its source.
Edit the file in `_src/pages/` and run `python3 tools/build.py`.

The reason for a generator on an otherwise plain static site is explained in
[docs/architecture.md](docs/architecture.md#adr-1-a-local-generator-rather-than-hand-maintained-headers).
Short version: 38 pages share one header and footer, and hand-maintaining that markup 38
times guarantees drift. Cloudflare still serves plain committed HTML with no build command.

## Layout

```
_src/                    SOURCE — edit these
  site.json                nav, footer, contact details, Turnstile site key
  partials/base.html       the page shell (<head>, header, footer)
  pages/*.html             one file per page: front matter + <main> content

tools/                   Local scripts (Python 3 stdlib only, never run on deploy)
  build.py                 assembles _src/ into committed HTML + sitemap.xml
  check_links.py           verifies every internal link and anchor
  import_posts.py          one-shot WordPress importer, kept as a record

assets/
  css/site.css             the entire stylesheet
  js/site.js               nav, form validation, submit handling
  img/                     logos (copied from logos/, do not edit)
  docs/                    capability statement PDFs

functions/api/contact.js Cloudflare Pages Function: Turnstile + Postmark

docs/                    Documentation — start at docs/README.md
logos/                   Original brand assets. DO NOT EDIT.

index.html               GENERATED
404.html                 GENERATED
<section>/index.html     GENERATED
sitemap.xml              GENERATED
_headers, _redirects     Cloudflare Pages configuration
```

## Common tasks

| Task | Where |
|---|---|
| Change nav or footer links | `_src/site.json`, then rebuild |
| Edit page copy | the matching file in `_src/pages/`, then rebuild |
| Add a news post | [docs/adding-content.md](docs/adding-content.md) |
| Change colours, spacing, type | the token block at the top of `assets/css/site.css` |
| Set up the contact form | [docs/contact-form.md](docs/contact-form.md) |
| Deploy | [docs/deployment.md](docs/deployment.md) |

## Documentation

- [docs/README.md](docs/README.md) — index
- [docs/architecture.md](docs/architecture.md) — decisions and the reasoning behind them
- [docs/design-system.md](docs/design-system.md) — tokens, components, conventions
- [docs/adding-content.md](docs/adding-content.md) — adding pages and posts
- [docs/deployment.md](docs/deployment.md) — GitHub and Cloudflare Pages setup
- [docs/contact-form.md](docs/contact-form.md) — Postmark and Turnstile
- [docs/content-catalog.md](docs/content-catalog.md) — what the site says and where each fact lives
- [docs/known-issues.md](docs/known-issues.md) — outstanding items needing a human decision
