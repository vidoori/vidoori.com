# Adding and editing content

Everything starts in `_src/`. Nothing in the site root is edited by hand.

```bash
# after any edit
python3 tools/build.py
python3 tools/check_links.py
```

## Front matter

Every file in `_src/pages/` opens with a `key: value` block terminated by a line containing
only `---`. Values are plain text; there is no quoting or nesting.

| Key | Required | Purpose |
|---|---|---|
| `title` | yes | `<title>` and `og:title`. ` \| Vidoori` is appended automatically. |
| `description` | yes | Meta description and `og:description`. Aim for 120–160 characters. |
| `path` | yes | URL path, with leading and trailing slash: `/what-we-do/data/`. Determines the output file. |
| `nav` | no | Which top-level nav item highlights: `who-we-are`, `what-we-do`, `solutions`, `insights`, `careers`, or `none`. |
| `schema` | no | JSON-LD type. Default `WebPage`. Use `none` to emit only the Organization node. |
| `rawtitle` | no | `true` suppresses the ` \| Vidoori` suffix. Only the homepage uses this. |
| `section` | no | Category label for posts, e.g. `News`. Shown as the eyebrow. |
| `date` | no | `YYYY-MM-DD`. Required for posts — drives Insights ordering and `lastmod`. |
| `head` | no | Extra markup injected into `<head>`. Single line. Only `/contact/` uses it. |

Recognised `schema` values: `WebPage`, `AboutPage`, `ContactPage`, `CollectionPage`,
`WebSite`, `Article`, `Service`, `SoftwareApplication`, `none`. `Service` also reads an
optional `serviceName`. `Article` reads `section` and `date`.

## Adding a news post or article

1. Create `_src/pages/post-<category>-<slug>.html`. The filename is only for humans; `path`
   is what determines the URL.

2. Use an existing post as the template — `_src/pages/post-news-*.html`. The structure is:

```
title: Vidoori Awarded Contract for Something
description: One or two sentences that will appear on the Insights index.
path: /news/vidoori-awarded-contract-for-something/
nav: insights
schema: Article
section: News
date: 2026-09-15
---
<article>
  <header class="page-hero">
    <div class="container container--narrow">
      <p class="breadcrumb"><a href="/insights/">Insights</a><span>/</span>News</p>
      <h1>Vidoori Awarded Contract for Something</h1>
      <p class="article-meta">
        <time datetime="2026-09-15">September 15, 2026</time>
        <span class="badge">News</span>
      </p>
    </div>
  </header>

  <div class="section">
    <div class="container container--narrow">
      <div class="prose">
        <p>Opening paragraph.</p>
        <h2>A subheading</h2>
        <p>More copy.</p>
        <blockquote><p>A pull quote.</p></blockquote>
      </div>
      <p class="mt-7"><a class="link-arrow" href="/insights/">Back to all insights</a></p>
    </div>
  </div>
</article>

<section class="section section--tight">
  <div class="container">
    <div class="cta-band">
      <div><h2>Talk to our team</h2><p>Tell us what you are working on.</p></div>
      <div class="btn-row"><a class="btn btn--accent" href="/contact/">Contact Vidoori</a></div>
    </div>
  </div>
</section>
```

3. Run `python3 tools/build.py`.

**You do not need to touch `/insights/`.** The index is generated from every page with
`schema: Article`, sorted newest first, using `section`, `date`, `title`, and `description`.
The same applies to `sitemap.xml`.

### Choosing a URL path

Existing posts use a legacy category prefix (`/news/…`, `/cybersecurity/…`) inherited from
WordPress. For new posts, `/news/<slug>/` is the natural home for announcements. Keep slugs
lowercase, hyphenated, and short. Once a URL is published, do not change it — add a
`_redirects` rule if you must.

## Adding a regular page

1. Create `_src/pages/<name>.html` with front matter and a `path`.
2. Add it to `_src/site.json` under `nav` and/or `footer` so it is reachable.
3. Build.

An orphan page — one no nav or footer links to — is how the WordPress site ended up with ten
invisible leadership bios. `check_links.py` does not flag orphans, so this is on you.

## Changing navigation or footer links

Edit `_src/site.json`, then rebuild. All 41 pages update together. The `nav` array drives the
header (with `children` producing dropdowns); the `footer` array drives the four footer
columns. Set `"external": true` on a link to get `target="_blank" rel="noopener noreferrer"`.

## Editing shared chrome

`_src/partials/base.html` is the whole page shell: `<head>`, header, footer. The footer's
address, social links, and copyright line are literal markup there, not tokens — if the
office address changes, it must be updated in `base.html`, in `_src/site.json` (`contact`,
which feeds JSON-LD), and in `_src/pages/contact.html`.

> Worth knowing: the address appears in more places than you would guess. Search the repo
> for `Garden City` before assuming you have got them all.

## Content conventions

- **Curly quotes and dashes.** Use HTML entities: `&rsquo;` `&ldquo;` `&rdquo;` `&mdash;`
  `&nbsp;`. The imported posts already use them.
- **`&` in text** must be `&amp;`.
- **Headings.** One `<h1>` per page, in the hero. Section headings are `<h2>`. Do not skip
  levels — the structure is what screen readers navigate by.
- **Links.** Root-relative (`/what-we-do/`), never relative (`../`) and never absolute to
  `www.vidoori.com`. `check_links.py` enforces this, because absolute self-links break on
  preview deployments.
- **Trailing slashes.** Always, on directory-style paths.

## Reusable components

Copy these from existing pages; the full catalogue with rendered descriptions is in
[design-system.md](design-system.md).

| Need | Component |
|---|---|
| Page banner | `.page-hero` (`.hero` is homepage-only) |
| Copy beside a graphic | `.split` + `.figure-panel` |
| Card row | `.grid` / `.grid--2` / `.grid--4` + `.card` |
| Whole-card link | `.card.card--link` with the link in the `<h3>` |
| Checklist of capabilities | `.caps` |
| Heading-and-paragraph list | `.def-list` (add `--3` for three columns) |
| Numbers | `.stats` + `.stat` |
| Certification or award entry | `.record` |
| Key/value identifiers | `.kv` |
| Pill label | `.badge`, in a `.badge-row` |
| Emphasised sentence | `.callout` |
| Closing call to action | `.cta-band` |
| Long-form body copy | `.prose` |
| Person | `.profile` |

## Before committing

```bash
python3 tools/build.py --check   # is committed HTML current?
python3 tools/check_links.py     # any broken links or anchors?
```

Both exit non-zero on failure, so they work as a pre-commit hook.
