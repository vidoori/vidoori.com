#!/usr/bin/env python3
"""
Verify every internal link, asset reference, and anchor in the built site.

Run after tools/build.py. Exits non-zero if anything is broken, so it works
as a pre-commit or CI gate.

    python3 tools/check_links.py

Checks performed:
  * Internal hrefs resolve to a built file, a directory index, or a rule
    in _redirects.
  * src / href asset references (css, js, svg, pdf) exist on disk.
  * Same-page #anchors point at an id that exists in that page.
  * No page still links to a www.vidoori.com absolute URL (those should be
    root-relative so the site works on preview deployments).
  * No leftover WordPress paths (/wp-content/, /wp-admin/).

External (http) links are reported as a count only — reaching out over the
network would make this check slow and flaky.
"""

import os
import re
import sys
from urllib.parse import urlsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {".git", "_src", "tools", "docs", "logos", "node_modules", ".claude"}


def built_pages():
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for name in files:
            if name.endswith(".html"):
                yield os.path.join(base, name)


def load_redirects():
    """Return (exact_paths, prefix_globs, placeholder_patterns, rules)."""
    exact, globs, patterns, rules = set(), [], [], []
    path = os.path.join(ROOT, "_redirects")
    if not os.path.exists(path):
        return exact, globs
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        src, dst = parts[0], parts[1]
        rules.append((src, dst))
        if src.endswith("*"):
            globs.append(src[:-1])
        elif ":" in src:
            # A :placeholder matches exactly one non-empty path segment.
            pattern = "/".join(
                r"[^/]+" if seg.startswith(":") else re.escape(seg)
                for seg in src.split("/"))
            patterns.append(re.compile("^" + pattern + "/?$"))
        else:
            exact.add(src.rstrip("/") or "/")
    return exact, globs, patterns, rules


def redirect_loops(rules):
    """Rules that send a path to itself.

    A splat matches the empty string, so `/a/b/*  /a/b/  301` also matches
    `/a/b/` and redirects the real page to itself until the browser gives up.
    Use a `:placeholder` instead — it requires a non-empty path segment.
    This is invisible locally: the file exists on disk and every link to it
    resolves, so only the deployed site 500s.
    """
    out = []
    for src, dst in rules:
        base = src[:-1] if src.endswith("*") else src
        if base.rstrip("/") == dst.rstrip("/"):
            out.append("%s -> %s redirects to itself" % (src, dst))
    return out


def resolves(link, redirect_exact, redirect_globs, redirect_patterns=()):
    """Does this root-relative path resolve to a file, index, or redirect?"""
    clean = link.split("#")[0].split("?")[0]
    if not clean or clean == "/":
        return os.path.exists(os.path.join(ROOT, "index.html"))

    rel = clean.lstrip("/")
    candidates = [
        os.path.join(ROOT, rel),                    # exact file
        os.path.join(ROOT, rel, "index.html"),      # directory index
        os.path.join(ROOT, rel.rstrip("/") + ".html"),
    ]
    if any(os.path.isfile(c) for c in candidates):
        return True

    normalised = "/" + rel.rstrip("/")
    if normalised in redirect_exact or clean.rstrip("/") in redirect_exact:
        return True
    if any(clean.startswith(g) for g in redirect_globs):
        return True
    return any(pat.match(clean.rstrip("/") or "/") for pat in redirect_patterns)


def main():
    redirect_exact, redirect_globs, redirect_patterns, redirect_rules = load_redirects()
    problems = ["_redirects: " + p for p in redirect_loops(redirect_rules)]

    external = 0
    checked = 0
    pages = sorted(built_pages())

    if not pages:
        print("No built pages found. Run python3 tools/build.py first.", file=sys.stderr)
        return 1

    for page in pages:
        rel_page = os.path.relpath(page, ROOT)
        html = open(page, encoding="utf-8").read()
        ids = set(re.findall(r'\bid="([^"]+)"', html))

        # <link rel="canonical"> and friends are *supposed* to be absolute;
        # drop those tags before scanning so they are not flagged.
        scannable = re.sub(
            r'<link\b[^>]*\brel="(canonical|alternate|apple-touch-icon|icon)"[^>]*>',
            "", html)

        refs = re.findall(r'(?:href|src)="([^"]+)"', scannable)
        for ref in refs:
            checked += 1

            if ref.startswith(("mailto:", "tel:", "data:", "javascript:")):
                continue

            if ref.startswith(("http://", "https://", "//")):
                external += 1
                host = urlsplit(ref if "//" in ref else "//" + ref).netloc
                if host.endswith("vidoori.com") and not host.startswith("vpt."):
                    problems.append(
                        "%s: absolute self-link %s (use a root-relative path so "
                        "preview deployments work)" % (rel_page, ref)
                    )
                continue

            if ref.startswith("#"):
                anchor = ref[1:]
                if anchor and anchor not in ids:
                    problems.append("%s: anchor %s has no matching id" % (rel_page, ref))
                continue

            if "/wp-content/" in ref or "/wp-admin/" in ref:
                problems.append("%s: leftover WordPress path %s" % (rel_page, ref))
                continue

            if not ref.startswith("/"):
                problems.append("%s: relative link %s (use root-relative paths)"
                                % (rel_page, ref))
                continue

            if not resolves(ref, redirect_exact, redirect_globs, redirect_patterns):
                problems.append("%s: broken link %s" % (rel_page, ref))

            # Cross-page anchors: verify the fragment against the target page.
            if "#" in ref:
                target, _, anchor = ref.partition("#")
                if anchor:
                    tgt_file = os.path.join(ROOT, target.strip("/"), "index.html")
                    if os.path.isfile(tgt_file):
                        tgt_html = open(tgt_file, encoding="utf-8").read()
                        if anchor not in set(re.findall(r'\bid="([^"]+)"', tgt_html)):
                            problems.append("%s: anchor #%s missing in %s"
                                            % (rel_page, anchor, target))

    print("Scanned %d pages, %d references (%d external, not fetched)."
          % (len(pages), checked, external))

    if problems:
        print("\n%d problem(s):\n" % len(problems), file=sys.stderr)
        for p in sorted(set(problems)):
            print("  " + p, file=sys.stderr)
        return 1

    print("No broken internal links.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
