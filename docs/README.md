# Vidoori website documentation

Static site replacing the WordPress install, built August 2026.
Start with the root [README.md](../README.md) for the quick start and directory layout.

## The one thing to know

**The `.html` files in the site root are generated. Do not edit them.** Edit the matching
file in `_src/pages/` and run `python3 tools/build.py`. Every generated file says so in a
banner comment at the top.

## Documents

| Document | Read it when |
|---|---|
| [architecture.md](architecture.md) | You want to know *why* something is built this way, or you are about to change something structural. Written as decision records. |
| [adding-content.md](adding-content.md) | You are adding a page or a news post, or editing copy. |
| [design-system.md](design-system.md) | You are changing how something looks, or building a new component. |
| [deployment.md](deployment.md) | You are setting up hosting, going live, or debugging a deploy. |
| [contact-form.md](contact-form.md) | You are configuring, testing, or changing the contact form. |
| [content-catalog.md](content-catalog.md) | You need to find where a fact or piece of copy lives. Also holds the legacy WordPress snapshot, in an appendix. |
| [known-issues.md](known-issues.md) | **Before going live.** Open decisions and inherited content problems. |

## Quick reference

```bash
python3 tools/build.py            # regenerate HTML + sitemap.xml
python3 tools/build.py --check    # exit 1 if committed HTML is stale
python3 tools/check_links.py      # verify internal links and anchors
python3 -m http.server 8788       # preview (contact form needs Pages runtime)
```

## The shape of it

```
_src/site.json           nav, footer, contact details, Turnstile site key
_src/partials/base.html  page shell: <head>, header, footer
_src/pages/*.html        one file per page: front matter + <main> content
        |
        |  python3 tools/build.py
        v
index.html, <section>/index.html, 404.html, sitemap.xml   (committed)
        |
        |  git push
        v
Cloudflare Pages — no build command, no Node
```

Three things generate themselves from page front matter, so there is no second list to keep
in sync: the **Insights index** (any page with `schema: Article`), **sitemap.xml**, and the
**JSON-LD** structured data.
