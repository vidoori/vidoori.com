#!/usr/bin/env python3
"""
Vidoori static site assembler.

WHY THIS EXISTS
---------------
The site is ~40 pages of plain HTML. Every one needs the same header, nav,
and footer. Hand-maintaining that markup 40 times means a nav change is 40
edits and one of them will be wrong. This script stamps the shared chrome
into each page so there is exactly one copy to edit.

It is NOT a deploy-time build step. It runs locally, writes ordinary .html
files, and those files are committed. Cloudflare Pages serves them directly
with no build command and no Node. If this script disappeared tomorrow the
site would keep working; you would just be back to editing 40 headers.

USAGE
-----
    python3 tools/build.py            # rebuild every page
    python3 tools/build.py --check    # exit 1 if output is stale (for CI)
    python3 tools/build.py --clean    # remove generated pages first

INPUTS
------
    _src/site.json          nav, footer, contact details
    _src/partials/base.html the page shell
    _src/pages/*.html       one file per page: front matter + <main> content

Front matter is a simple `key: value` block terminated by a line of `---`:

    title: Cloud-Native
    description: ...
    path: /what-we-do/cloud-native/
    nav: what-we-do
    ---
    <section>...</section>

Requires only the Python 3 standard library (3.8+).
"""

import argparse
import html
import json
import hashlib
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "_src")
PAGES = os.path.join(SRC, "pages")

BANNER = (
    "<!--\n"
    "  GENERATED FILE - DO NOT EDIT DIRECTLY.\n"
    "  Source: _src/pages/{src}\n"
    "  Shell:  _src/partials/base.html   Data: _src/site.json\n"
    "  Rebuild with:  python3 tools/build.py\n"
    "  Editing this file directly works until the next build, then it is overwritten.\n"
    "-->\n"
)


# --------------------------------------------------------------------------
# Front matter
# --------------------------------------------------------------------------

def parse_page(text, filename):
    """Split `key: value` front matter from body content."""
    if "\n---" not in text:
        raise ValueError("%s: missing '---' front-matter terminator" % filename)

    head, _, body = text.partition("\n---")
    meta = {}
    for lineno, line in enumerate(head.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError("%s line %d: expected 'key: value', got %r"
                             % (filename, lineno, line))
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()

    for required in ("title", "description", "path"):
        if required not in meta:
            raise ValueError("%s: front matter missing '%s'" % (filename, required))

    return meta, body.lstrip("\n")


# --------------------------------------------------------------------------
# Navigation
# --------------------------------------------------------------------------

_ASSET_VERSIONS = {}


def asset_version(rel_path):
    """Short content hash for a static asset, used as a ?v= cache buster.

    Asset filenames are not fingerprinted, and Cloudflare serves them with a
    long max-age (the zone's Browser Cache TTL can override what _headers asks
    for). Without this, a CSS or JS change does not reach returning visitors
    for days, while the HTML that depends on it updates immediately — the
    worst possible pairing. The HTML is always revalidated, so a new hash here
    pulls the new asset through instantly.

    Cached per run: the file is read once, not once per page.
    """
    if rel_path not in _ASSET_VERSIONS:
        full = os.path.join(ROOT, rel_path)
        with open(full, "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        _ASSET_VERSIONS[rel_path] = digest[:10]
    return _ASSET_VERSIONS[rel_path]


def is_current(item, page_nav, page_path):
    """A top-level nav item is 'current' for its own page and its children."""
    if page_nav and item.get("id") == page_nav:
        return True
    return page_path == item.get("href")


def render_nav(site, page_nav, page_path):
    """Build the <li> list shared by both breakpoints.

    Items with children render a <button> disclosure plus a nested <ul>.
    Items without render a single <a>. Markup is identical at every width;
    CSS decides whether it looks like a bar or a stacked panel.
    """
    out = []
    for item in site["nav"]:
        current = is_current(item, page_nav, page_path)
        classes = "nav__item" + (" is-current" if current else "")

        if not item.get("children"):
            aria = ' aria-current="page"' if page_path == item["href"] else ""
            out.append(
                '        <li class="%s">'
                '<a class="nav__link" href="%s"%s>%s</a></li>'
                % (classes, item["href"], aria, html.escape(item["label"]))
            )
            continue

        menu_id = "menu-" + item["id"]
        sub = []
        for child in item["children"]:
            attrs = ""
            if child.get("external"):
                attrs = ' target="_blank" rel="noopener noreferrer"'
            elif page_path == child["href"]:
                attrs = ' aria-current="page"'
            sub.append(
                '            <li><a class="nav__sublink" href="%s"%s>%s</a></li>'
                % (child["href"], attrs, html.escape(child["label"]))
            )

        out.append(
            '        <li class="%s">\n'
            '          <button class="nav__disclosure" type="button" '
            'aria-expanded="false" aria-controls="%s">%s</button>\n'
            '          <ul class="nav__sublist" id="%s">\n%s\n          </ul>\n'
            '        </li>'
            % (classes, menu_id, html.escape(item["label"]), menu_id, "\n".join(sub))
        )

    return "\n".join(out)


def render_footer_columns(site):
    cols = []
    for col in site["footer"]:
        links = []
        for link in col["links"]:
            attrs = ' target="_blank" rel="noopener noreferrer"' if link.get("external") else ""
            links.append('          <li><a href="%s"%s>%s</a></li>'
                         % (link["href"], attrs, html.escape(link["label"])))
        cols.append(
            '      <div>\n        <h2>%s</h2>\n        <ul>\n%s\n        </ul>\n      </div>'
            % (html.escape(col["heading"]), "\n".join(links))
        )
    return "\n".join(cols)


# --------------------------------------------------------------------------
# Structured data
# --------------------------------------------------------------------------

def organization_ld(site):
    c = site["contact"]
    return {
        "@type": "Organization",
        "@id": site["origin"] + "/#organization",
        "name": site["name"],
        "legalName": site["legalName"],
        "url": site["origin"] + "/",
        "logo": site["origin"] + "/assets/img/vidoori-logo.svg",
        "description": site["blurb"],
        "foundingDate": site["foundedYear"],
        "email": c["email"],
        "telephone": c["phone"],
        "faxNumber": c["fax"],
        "address": {
            "@type": "PostalAddress",
            "streetAddress": c["street"],
            "addressLocality": c["city"],
            "addressRegion": c["state"],
            "postalCode": c["zip"],
            "addressCountry": c["country"],
        },
        # Only the social properties Vidoori actually uses. Built from a
        # filtered list so removing one from site.json cannot raise KeyError.
        "sameAs": [url for url in (site["external"].get("linkedin"),)
                   if url],
    }


def build_jsonld(site, meta):
    """Every page carries the Organization node; some add a second node."""
    graph = [organization_ld(site)]
    origin = site["origin"]
    url = origin + meta["path"]

    page_type = meta.get("schema", "WebPage")

    if page_type == "Article":
        node = {
            "@type": "Article",
            "@id": url + "#article",
            "headline": meta["title"],
            "description": meta["description"],
            "url": url,
            "publisher": {"@id": origin + "/#organization"},
            "author": {"@id": origin + "/#organization"},
            "mainEntityOfPage": url,
        }
        if meta.get("section"):
            node["articleSection"] = meta["section"]
        if meta.get("date"):
            node["datePublished"] = meta["date"]
            node["dateModified"] = meta["date"]
        graph.append(node)
    elif page_type == "ContactPage":
        graph.append({
            "@type": "ContactPage",
            "@id": url + "#page",
            "url": url,
            "name": meta["title"],
            "description": meta["description"],
            "about": {"@id": origin + "/#organization"},
        })
    elif page_type == "Service":
        graph.append({
            "@type": "Service",
            "@id": url + "#service",
            "name": meta.get("serviceName", meta["title"]),
            "description": meta["description"],
            "url": url,
            "provider": {"@id": origin + "/#organization"},
            "serviceType": meta.get("serviceName", meta["title"]),
        })
    elif page_type != "none":
        graph.append({
            "@type": page_type,
            "@id": url + "#page",
            "url": url,
            "name": meta["title"],
            "description": meta["description"],
            "isPartOf": {"@id": origin + "/#organization"},
        })

    return json.dumps({"@context": "https://schema.org", "@graph": graph},
                      separators=(",", ":"))


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

def render_insights_list(posts):
    """Render the Insights index from every page whose schema is Article.

    Generated rather than hand-maintained so a new post appears on the index
    the moment it is built — there is no second list to forget to update.
    Sorted newest first; posts without a date sort last.
    """
    if not posts:
        return '<p class="muted">No insights published yet.</p>'

    items = []
    for meta in posts:
        pretty = ""
        if meta.get("date"):
            y, m, d = meta["date"].split("-")
            pretty = "%s %d, %s" % (MONTHS[int(m) - 1], int(d), y)

        meta_line = []
        if meta.get("section"):
            meta_line.append(html.escape(meta["section"]))
        if pretty:
            meta_line.append('<time datetime="%s">%s</time>' % (meta["date"], pretty))

        items.append(
            '      <article class="teaser">\n'
            '        <p class="teaser__meta">%s</p>\n'
            '        <h3><a href="%s">%s</a></h3>\n'
            '        <p>%s</p>\n'
            '        <span class="teaser__more link-arrow" aria-hidden="true">Read more</span>\n'
            '      </article>'
            % (" &middot; ".join(meta_line), meta["path"],
               html.escape(meta["title"]), html.escape(meta["description"]))
        )
    return "\n".join(items)


MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def render(site, shell, meta, content, src_name, posts=None):
    path = meta["path"]
    canonical = site["origin"] + path

    title = meta["title"]
    full_title = title if meta.get("rawtitle") == "true" else "%s | Vidoori" % title

    page = shell
    replacements = {
        "{{TITLE}}": html.escape(full_title),
        "{{OGTITLE}}": html.escape(title),
        "{{DESCRIPTION}}": html.escape(meta["description"]),
        "{{CANONICAL}}": canonical,
        "{{ORIGIN}}": site["origin"],
        "{{OGTYPE}}": "article" if meta.get("schema") == "Article" else "website",
        "{{JSONLD}}": build_jsonld(site, meta),
        "{{NAV}}": render_nav(site, meta.get("nav"), path),
        "{{FOOTER_COLUMNS}}": render_footer_columns(site),
        "{{HEAD_EXTRA}}": robots_meta(meta) + meta.get("head", "").replace("\\n", "\n"),
        "{{CONTENT}}": content.rstrip() + "\n",
        "{{CSS_VERSION}}": asset_version("assets/css/site.css"),
        "{{JS_VERSION}}": asset_version("assets/js/site.js"),
    }
    for token, value in replacements.items():
        page = page.replace(token, value)

    # Applied last, so these also reach tokens that arrived inside CONTENT.
    page = page.replace("{{TURNSTILE_SITEKEY}}", site.get("turnstileSiteKey", ""))
    if "{{INSIGHTS_LIST}}" in page:
        page = page.replace("{{INSIGHTS_LIST}}", render_insights_list(posts or []))

    leftover = re.findall(r"\{\{[A-Z_]+\}\}", page)
    if leftover:
        raise ValueError("%s: unreplaced tokens %s" % (src_name, sorted(set(leftover))))

    return BANNER.format(src=src_name) + page


def robots_meta(meta):
    """`robots: noindex` in front matter hides a page from search engines.

    Used for a page that must keep existing but not be found: it gets a robots
    meta tag here and is left out of sitemap.xml. _headers sends a matching
    X-Robots-Tag for the same path, which also covers crawlers that never
    parse the HTML. Hiding it from people is separate: remove its links.
    """
    if meta.get("robots") == "noindex":
        return '<meta name="robots" content="noindex, nofollow">\n'
    return ""


def write_sitemap(site, results):
    """Generate sitemap.xml from the same page list that was just rendered.

    Generated rather than hand-maintained for the same reason as the Insights
    index: a hand-written sitemap goes stale the first time someone forgets.
    Excludes the 404 page, which should never be indexed, and any page whose
    front matter says `robots: noindex`.
    """
    origin = site["origin"]
    entries = []
    for meta, _ in results:
        if meta.get("schema") == "none" or meta["path"].endswith(".html"):
            continue
        if meta.get("robots") == "noindex":
            continue

        # Rough priority: home > top-level sections > everything else.
        depth = meta["path"].strip("/").count("/")
        if meta["path"] == "/":
            priority, freq = "1.0", "weekly"
        elif depth == 0:
            priority, freq = "0.8", "monthly"
        elif meta.get("schema") == "Article":
            priority, freq = "0.5", "yearly"
        else:
            priority, freq = "0.6", "monthly"

        loc = "<loc>%s%s</loc>" % (origin, meta["path"])
        lastmod = ("<lastmod>%s</lastmod>" % meta["date"]) if meta.get("date") else ""
        entries.append(
            "  <url>%s%s<changefreq>%s</changefreq>"
            "<priority>%s</priority></url>" % (loc, lastmod, freq, priority)
        )

    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           + "\n".join(sorted(entries)) + "\n</urlset>\n")

    dest = os.path.join(ROOT, "sitemap.xml")
    existing = open(dest, encoding="utf-8").read() if os.path.exists(dest) else None
    if existing == xml:
        return 0
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write(xml)
    return 1


def output_path(page_path):
    """Map a page path to its file on disk.

        '/'                  -> index.html
        '/what-we-do/'       -> what-we-do/index.html
        '/404.html'          -> 404.html          (a literal filename)

    The literal form exists for Cloudflare Pages' custom error page, which
    must live at /404.html rather than /404/index.html.
    """
    rel = page_path.lstrip("/")
    if rel.endswith(".html"):
        return os.path.join(ROOT, rel)
    rel = rel.strip("/")
    return os.path.join(ROOT, rel, "index.html") if rel else os.path.join(ROOT, "index.html")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def collect():
    site = json.load(open(os.path.join(SRC, "site.json"), encoding="utf-8"))
    shell = open(os.path.join(SRC, "partials", "base.html"), encoding="utf-8").read()

    # Pass 1: parse every page so the Insights index can be built from the
    # full set of posts before any page is rendered.
    parsed = []
    for name in sorted(os.listdir(PAGES)):
        if not name.endswith(".html"):
            continue
        raw = open(os.path.join(PAGES, name), encoding="utf-8").read()
        meta, content = parse_page(raw, name)
        parsed.append((name, meta, content))

    posts = [m for _, m, _ in parsed if m.get("schema") == "Article"]
    posts.sort(key=lambda m: m.get("date", "0000-00-00"), reverse=True)

    # Pass 2: render.
    results = []
    for name, meta, content in parsed:
        results.append((meta, render(site, shell, meta, content, name, posts)))
    return site, results


def main():
    ap = argparse.ArgumentParser(description="Assemble the Vidoori static site.")
    ap.add_argument("--check", action="store_true",
                    help="verify committed HTML matches sources; exit 1 if not")
    ap.add_argument("--clean", action="store_true",
                    help="delete generated page directories before building")
    args = ap.parse_args()

    try:
        site, results = collect()
    except ValueError as exc:
        print("build error: %s" % exc, file=sys.stderr)
        return 1

    if args.clean and not args.check:
        for meta, _ in results:
            rel = meta["path"].strip("/")
            if rel and os.path.isdir(os.path.join(ROOT, rel)):
                shutil.rmtree(os.path.join(ROOT, rel))

    stale, written = [], 0
    for meta, page in results:
        dest = output_path(meta["path"])
        existing = None
        if os.path.exists(dest):
            existing = open(dest, encoding="utf-8").read()

        if existing == page:
            continue

        if args.check:
            stale.append(os.path.relpath(dest, ROOT))
            continue

        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(page)
        written += 1

    if args.check:
        sitemap_path = os.path.join(ROOT, "sitemap.xml")
        before = open(sitemap_path, encoding="utf-8").read() \
            if os.path.exists(sitemap_path) else None
        write_sitemap(site, results)
        after = open(sitemap_path, encoding="utf-8").read() \
            if os.path.exists(sitemap_path) else None
        if before != after:
            stale.append("sitemap.xml")

        if stale:
            print("Out of date (%d):" % len(stale), file=sys.stderr)
            for path in stale:
                print("  " + path, file=sys.stderr)
            print("\nRun: python3 tools/build.py", file=sys.stderr)
            return 1
        print("All %d pages up to date." % len(results))
        return 0

    sitemap_changed = write_sitemap(site, results)

    print("Built %d pages (%d changed). Sitemap %s."
          % (len(results), written, "updated" if sitemap_changed else "unchanged"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
