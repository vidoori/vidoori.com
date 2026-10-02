# Deployment: GitHub and Cloudflare Pages

The deploy model is deliberately boring: commit HTML, Cloudflare serves it. **No build
command, no Node, no framework preset.**

## One-time setup

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Rebuild vidoori.com as a static site"
git branch -M main
git remote add origin git@github.com:<org>/vidoori.com.git
git push -u origin main
```

### 2. Create the Pages project

Cloudflare dashboard → **Workers & Pages** → **Create** → **Pages** → **Connect to Git**,
then select the repository and configure the build:

| Setting | Value |
|---|---|
| Framework preset | **None** |
| Build command | **leave empty** |
| Build output directory | `/` |
| Root directory | `/` |

Leaving the build command empty is the whole point. Cloudflare copies the repository as-is
and serves it. If you ever see Cloudflare installing dependencies, something has been
misconfigured.

### 3. Environment variables

Add the contact form's variables — see [contact-form.md](contact-form.md#environment-variables).
Add them to **Production and Preview** if you want the form to work on preview deployments.

### 4. Custom domain

Pages project → **Custom domains** → add `www.vidoori.com`, and add the apex `vidoori.com`
if you want it to resolve.

Decide which host is canonical. The site's `<link rel="canonical">` tags and `sitemap.xml`
are generated from `origin` in `_src/site.json`, currently `https://www.vidoori.com`. If you
make the apex canonical instead, change that value and rebuild, or every canonical tag will
point at the wrong host.

Set up an apex → www redirect (or the reverse) with a Cloudflare **Bulk Redirect** or a
Redirect Rule. `_redirects` cannot do cross-hostname redirects.

### 5. Cutover

**Completed 2026-10-02.** `www.vidoori.com` now serves the Pages project. Verified after the
switch: pages, legacy redirects, the 404 page, both PDFs and the hidden team page&rsquo;s
`X-Robots-Tag` on the live host, and both forms delivered email end to end. The sitemap is
submitted to Google Search Console; Bing was deliberately skipped. The checklist below is
kept for reference.

The DNS switch is the risky step. Before it:

- [ ] Preview deployment reviewed on desktop and mobile
- [ ] Contact form submitted end-to-end and the email arrived in `CONTACT_TO_EMAIL`
- [ ] `TURNSTILE_SECRET_KEY` set in Pages (the site key is already live in `_src/site.json`)
- [ ] `python3 tools/build.py --check` clean
- [ ] `python3 tools/check_links.py` clean
- [ ] Spot-check redirects on the preview URL, e.g. `/who-we-are/leadership/eric-huang`
      and `/category/news`
- [ ] Apex → www redirect in place (a Cloudflare Redirect Rule; `_redirects` cannot do cross-hostname)

After cutover:

- Submit the new `sitemap.xml` in Google Search Console and Bing Webmaster Tools.
- Watch Search Console's Coverage report for a week for unexpected 404s.
- Keep the WordPress install reachable but unlinked for a short while, or take a full backup
  first. Once DNS moves, the old admin is gone — and removing that attack surface was the
  point of the exercise.

## How deploys work day to day

`main` is protected by a repository ruleset: every change reaches it through a pull request
that has passed the `verify` check and been approved by the site owner, who is the sole code
owner (`.github/CODEOWNERS`). The owner, as organization admin, may merge their own pull
requests without approval, but cannot push to `main` directly either. Force-pushes to `main`
and deleting it are blocked.

Merging to `main` publishes to production. Every push to any other branch, and every pull
request, gets its own preview URL. That makes previews the natural place to check the contact
form, since Functions run there exactly as in production.

## Configuration files

### `_headers`

Response headers, with reasoning in comments. The notable entries:

- **`Content-Security-Policy`** — tight, because the site has exactly one third-party
  script. `script-src` allows `'self'`, `https://challenges.cloudflare.com` (Turnstile), and
  `'unsafe-inline'`. The `'unsafe-inline'` is needed for the single inline
  `no-js` → `js` class swap in `<head>`; if that script is ever moved into `site.js`, drop
  `'unsafe-inline'` — but note that would reintroduce a flash of the expanded mobile nav.
- **`Strict-Transport-Security`** with `preload` — only submit to the HSTS preload list once
  you are certain every subdomain can serve HTTPS.
- **Caching** — HTML revalidates on every request so content edits go live immediately.
  Assets get short max-age with `stale-while-revalidate`, because filenames are not
  fingerprinted. If asset hashing is ever added, raise those to `immutable`.

### `_redirects`

30 rules preserving legacy WordPress URLs. See
[architecture ADR 3](architecture.md#adr-3-url-structure-preserves-every-legacy-path).

Cloudflare Pages caps `_redirects` at 2,000 static rules and 100 rules using splats. We are
far under both.

### `404.html`

Cloudflare Pages automatically serves a root `404.html` for unmatched paths. This is why the
page is generated to `/404.html` rather than `/404/index.html` — `tools/build.py` treats any
front-matter `path` ending in `.html` as a literal filename.

## Recommended CI check

Optional but cheap insurance against someone editing generated HTML by hand and committing
it. Save as `.github/workflows/verify.yml`:

```yaml
name: Verify
on: [push, pull_request]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Generated HTML is up to date
        run: python3 tools/build.py --check
      - name: No broken internal links
        run: python3 tools/check_links.py
```

No `setup-python` step is needed — GitHub's Ubuntu runners ship Python 3, and the scripts
use only the standard library.

## Rollback

Pages keeps every deployment. Project → **Deployments** → pick a previous one →
**Rollback**. Instant, and it needs no Git operation.
