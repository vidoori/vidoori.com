#!/usr/bin/env python3
"""
One-shot importer: legacy WordPress post HTML -> _src/pages/post-*.html sources.

This ran once during the 2026 rebuild to lift the 19 Insights posts off the
WordPress site. It is kept in the repo as a record of exactly how that content
was transformed, not because it needs to run again. New posts are written by
hand; see docs/adding-content.md.

Usage:
    python3 tools/import_posts.py <dir-of-mirrored-html>

Notes on the transformation:
  * Body content comes from the legacy `.blog-post-txt` container.
  * Images and figures are dropped — the rebuild is deliberately image-light.
  * Trailing "About Vidoori" press-release boilerplate is stripped; the footer
    already carries that text on every page.
  * &nbsp; is normalised to a plain space. The legacy editor sprayed them
    everywhere, which breaks sensible wrapping.
  * Absolute vidoori.com links are rewritten to root-relative paths.
"""

import html
import os
import re
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "_src", "pages")

# Legacy category slug -> display label. First match wins for the eyebrow.
CATEGORY_LABELS = {
    "news": "News",
    "cybersecurity": "Cybersecurity",
    "data": "Data",
    "test-integration": "Test & Integration",
    "cloud-native": "Cloud-Native",
    "devsecops": "DevSecOps",
    "innovations": "Innovations",
    "performance-testing": "Performance Testing",
}

# Preferred eyebrow when a post carries several categories: most specific first.
CATEGORY_PRIORITY = [
    "performance-testing", "test-integration", "cloud-native", "devsecops",
    "data", "cybersecurity", "innovations", "news",
]

ALLOWED_TAGS = {"p", "h2", "h3", "h4", "ul", "ol", "li", "blockquote",
                "strong", "em", "b", "i", "a", "hr", "br"}


def clean_body(raw):
    """Reduce WordPress block markup to a small, semantic subset."""
    body = raw

    # Drop media entirely.
    body = re.sub(r"<figure.*?</figure>", "", body, flags=re.S | re.I)
    body = re.sub(r"<img[^>]*>", "", body, flags=re.I)
    body = re.sub(r"<(script|style|iframe).*?</\1>", "", body, flags=re.S | re.I)

    # Cut the press-release boilerplate tail.
    for marker in (r"<p[^>]*>\s*<strong>\s*About\s*&nbsp;?\s*Vidoori",
                   r"<p[^>]*>\s*<strong>About Vidoori"):
        m = re.search(marker, body, flags=re.I)
        if m:
            # Also swallow the <hr> that usually precedes it.
            head = body[:m.start()]
            head = re.sub(r"<hr[^>]*>\s*$", "", head, flags=re.I)
            body = head
            break

    # Strip every attribute except href on <a>.
    def strip_attrs(m):
        tag = m.group(1).lower()
        if tag not in ALLOWED_TAGS:
            return ""
        if tag == "a":
            href = re.search(r'href="([^"]*)"', m.group(0))
            if not href:
                return ""
            url = href.group(1)
            url = re.sub(r"^https?://(www\.)?vidoori\.com", "", url)
            if not url:
                url = "/"
            external = url.startswith("http")
            extra = ' target="_blank" rel="noopener noreferrer"' if external else ""
            return '<a href="%s"%s>' % (url, extra)
        return "<%s>" % tag

    body = re.sub(r"<([a-zA-Z0-9]+)\b[^>]*>", strip_attrs, body)
    body = re.sub(r"</([a-zA-Z0-9]+)>",
                  lambda m: "</%s>" % m.group(1).lower()
                  if m.group(1).lower() in ALLOWED_TAGS else "", body)

    # Normalise whitespace entities and collapse blank lines.
    body = body.replace("&nbsp;", " ")
    body = re.sub(r"[ \t]+", " ", body)
    body = re.sub(r"\n\s*\n+", "\n\n", body)

    # Drop now-empty wrappers left behind by removed media.
    for _ in range(3):
        body = re.sub(r"<(p|blockquote|ul|ol|li|h[234])>\s*</\1>", "", body)

    return body.strip()


def excerpt(body, limit=180):
    """First sentence(s) of the article body, as a plain-text teaser."""
    text = re.sub(r"<[^>]+>", " ", body)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()

    # Press releases open with wire-service furniture that reads badly in a
    # teaser: "FOR IMMEDIATE RELEASE", a CITY, ST dateline (sometimes with a
    # date), and a "(BUSINESS WIRE)" tag. Strip each, in order, if present.
    text = re.sub(r"^\s*FOR IMMEDIATE RELEASE[\s:,-]*", "", text, flags=re.I)
    text = re.sub(r"^[A-Z][A-Za-z .]{2,30},\s*[A-Z]{2}"
                  r"(,\s*[A-Z][a-z]+ \d{1,2},\s*\d{4})?"
                  r"\s*[—–-]+\s*", "", text)
    text = re.sub(r"^\(BUSINESS WIRE\)\s*[—–-]+\s*", "", text)
    text = re.sub(r"^Article Overview[\s:,-]*", "", text)

    if len(text) <= limit:
        return text
    cut = text[:limit]
    # Prefer ending on a sentence, then a word.
    for sep in (". ", "! ", "? "):
        i = cut.rfind(sep)
        if i > limit * 0.5:
            return cut[:i + 1].strip()
    i = cut.rfind(" ")
    return (cut[:i] if i > 0 else cut).strip().rstrip(",;:") + "\u2026"


def extract(path):
    s = open(path, encoding="utf-8", errors="ignore").read()

    title = ""
    m = re.search(r'<h1 class="entry-title[^"]*">(.*?)</h1>', s, re.S)
    if not m:
        m = re.search(r"<title>(.*?)</title>", s, re.S)
    if m:
        title = re.sub(r"<[^>]+>", "", m.group(1))
        title = html.unescape(title).split(" – Vidoori")[0].strip()

    desc = ""
    m = re.search(r'<meta property="og:description" content="([^"]*)"', s)
    if m:
        desc = html.unescape(m.group(1)).strip()

    # Legacy theme prints "Posted:</span> March 3, 2021". There is no
    # datePublished in the page metadata, so this markup is the only source.
    iso_date, pretty_date = "", ""
    m = re.search(r"Posted:</span>\s*([A-Z][a-z]+ \d{1,2}, \d{4})", s)
    if m:
        pretty_date = m.group(1)
        iso_date = datetime.strptime(pretty_date, "%B %d, %Y").strftime("%Y-%m-%d")

    cats = sorted(set(re.findall(r"category-([a-z0-9-]+)", s)))
    cats = [c for c in cats if c in CATEGORY_LABELS]

    body = ""
    inner = extract_div(s, 'class="blog-post-txt"')
    if inner:
        body = clean_body(inner)

    return title, desc, cats, body, iso_date, pretty_date


def extract_div(s, marker):
    """Return the inner HTML of the <div> whose open tag contains `marker`.

    A non-greedy regex stops at the first </div>, which truncates any post
    containing a nested div (several do). This walks div open/close tags and
    tracks depth so the correct closing tag is found.
    """
    start = s.find(marker)
    if start == -1:
        return None
    open_end = s.find(">", start)
    if open_end == -1:
        return None

    depth = 1
    pos = open_end + 1
    for m in re.finditer(r"<(/?)div\b[^>]*>", s[pos:], flags=re.I):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            return s[pos:pos + m.start()]
    return s[pos:]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    srcdir = sys.argv[1]

    written = 0
    for name in sorted(os.listdir(srcdir)):
        if not name.endswith(".html"):
            continue
        # Mirror filenames encode the legacy path: "<cat>_<slug>.html"
        stem = name[:-5]
        if "_" not in stem:
            print("skip (no category prefix):", name)
            continue
        cat_slug, slug = stem.split("_", 1)

        title, desc, cats, body, iso_date, pretty_date = extract(
            os.path.join(srcdir, name))
        if not body:
            print("skip (no body):", name)
            continue

        # The legacy og:description was usually just the title again, which
        # makes a useless teaser. Fall back to the opening sentences of the
        # body, trimmed to roughly one line of card text.
        if not desc or desc.strip().lower() == title.strip().lower():
            desc = excerpt(body)

        eyebrow = "Insights"
        for pref in CATEGORY_PRIORITY:
            if pref in cats:
                eyebrow = CATEGORY_LABELS[pref]
                break

        path = "/%s/%s/" % (cat_slug, slug)
        others = [CATEGORY_LABELS[c] for c in cats]

        page = []
        page.append("title: %s" % title.replace("\n", " "))
        page.append("description: %s" % (desc or title))
        page.append("path: %s" % path)
        page.append("nav: insights")
        page.append("schema: Article")
        page.append("section: %s" % eyebrow)
        if iso_date:
            page.append("date: %s" % iso_date)
        page.append("---")
        page.append('<article>')
        page.append('  <header class="page-hero">')
        page.append('    <div class="container container--narrow">')
        page.append('      <p class="breadcrumb"><a href="/insights/">Insights</a>'
                    '<span>/</span>%s</p>' % html.escape(eyebrow))
        page.append('      <h1>%s</h1>' % html.escape(title))
        meta_bits = []
        if iso_date:
            meta_bits.append('<time datetime="%s">%s</time>' % (iso_date, pretty_date))
        meta_bits += ['<span class="badge">%s</span>' % html.escape(c) for c in others]
        if meta_bits:
            page.append('      <p class="article-meta">%s</p>' % " ".join(meta_bits))
        page.append("    </div>")
        page.append("  </header>")
        page.append("")
        page.append('  <div class="section">')
        page.append('    <div class="container container--narrow">')
        page.append('      <div class="prose">')
        for line in body.split("\n"):
            if line.strip():
                page.append("        " + line.strip())
        page.append("      </div>")
        page.append('      <p class="mt-7"><a class="link-arrow" href="/insights/">'
                    'Back to all insights</a></p>')
        page.append("    </div>")
        page.append("  </div>")
        page.append("</article>")
        page.append("")
        page.append('<section class="section section--tight">')
        page.append('  <div class="container">')
        page.append('    <div class="cta-band">')
        page.append("      <div><h2>Talk to our team</h2><p>Tell us what you are working "
                    "on and we will route your inquiry to the right specialist.</p></div>")
        page.append('      <div class="btn-row">'
                    '<a class="btn btn--accent" href="/contact/">Contact Vidoori</a></div>')
        page.append("    </div>")
        page.append("  </div>")
        page.append("</section>")

        dest = os.path.join(OUT, "post-%s-%s.html" % (cat_slug, slug))
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write("\n".join(page) + "\n")
        written += 1
        print("%-11s %-20s %-13s %s" % (iso_date or "no date", eyebrow,
                                          "%d words" % len(body.split()), path))

    print("\nWrote %d post sources." % written)
    return 0


if __name__ == "__main__":
    sys.exit(main())
