# Known issues and open decisions

Things found during the August 2026 rebuild that need a human decision, plus content
discrepancies inherited from the WordPress site. Nothing here blocks local development;
several items **do** block go-live.

---

## Blocking go-live

### 1. Turnstile: site key is live, secret key still needs setting

**Done (2026-09-01):** `_src/site.json` now carries the real widget's site key
`0x4AAAAAAEkCdhTn3knzXCzq`, and the site has been rebuilt. The widget is configured in
Cloudflare for the `vidoori.com` hostname (which covers `test.vidoori.com`).

**Still required before the form works:** set `TURNSTILE_SECRET_KEY` in
**Pages → project → Settings → Environment variables** (type Secret, in both Production and
Preview) to the matching secret key from the same widget.

Until that variable is set, `/api/contact` returns **HTTP 503** and logs the missing variable
names. The same is true of `POSTMARK_SERVER_TOKEN`, `CONTACT_TO_EMAIL`, and
`CONTACT_FROM_EMAIL` — all four are required. See [contact-form.md](contact-form.md#environment-variables).

Note the widget no longer always passes. Verification now genuinely fails on a hostname that
is not on the widget's list, so test on a real hostname (a preview deployment or
`test.vidoori.com`), not under `python3 -m http.server`.

### 2. ~~One PDF exceeds Cloudflare Pages' file size limit~~ (resolved)

Cloudflare Pages rejects any single file over **25 MiB**, and
`assets/docs/Applied-Intelligence-Capabilities.pdf` was 25.7 MiB — it would have failed the
deploy.

Resolved by removal: every capability PDF except `Vidoori_CapabilityStatement.pdf` (110 KiB)
was deleted, along with its links and its `/wp-content/uploads/...` redirect rule. Nothing in
`assets/docs/` is now anywhere near the limit.

### 3. ~~Legal pages need review~~ (reviewed and accepted 2026-09-01)

Owner reviewed all three rebuild-era changes to the privacy policy and accepted them as they
stand:

- **Address.** Confirmed as 4000 Garden City Drive, Suite 808, Hyattsville, MD 20785. The
  legacy policy gave a former Silver Spring office. See issue 4.
- **Privacy contact.** Stays `info@vidoori.com`. The legacy policy directed privacy questions
  to `contracts@vidoori.com`, which was a copy-paste error, not intent.
- **Turnstile disclosure.** The paragraph added under *Cookies and other technical
  considerations* is accepted as written.

If the client base ever pulls Vidoori into GDPR or CCPA scope, the Turnstile paragraph is the
place to revisit — naming Cloudflare as a processor, the browser token specifically, a legal
basis, and a retention period would each be worth adding then.

### 4. ~~The headquarters city is inconsistent across your own content~~ (resolved 2026-09-01)

**Confirmed by the owner:** the corporate address is
**4000 Garden City Drive, Suite 808, Hyattsville, MD 20785**.

The site already used it on every authoritative surface — `_src/site.json`, the footer, the
contact page, `/who-we-are/`, the privacy policy, and the JSON-LD `PostalAddress`. One page
disagreed and was corrected: the post *"Vidoori Opens New Maryland Headquarters"* gave the
same building as *New Carrollton, MD 20784* in both its body and its meta description. Same
street address, neighbouring municipality, wrong ZIP — corrected to Hyattsville, MD 20785.
Its URL slug still contains `new-carrolton` because legacy URLs are preserved; the slug is
not user-visible copy.

Press-release **datelines** naming *Silver Spring, MD* (NAVSUP, GSA STARS III, Census CoE,
Heart Association posts) were left alone. Silver Spring was genuinely the office those
releases were issued from, so they are accurate historical records rather than errors. No post
other than the headquarters announcement claims a headquarters address.

### 5. ~~Thomas Harrigan's LinkedIn link was wrong; his title was blank~~ (moot)

Resolved by removal: the Board of Advisors section was taken off the leadership page, so
Harrigan's bio no longer appears and there is no link or title to correct. Kept here as a
record in case the section is ever restored &mdash; the legacy page's LinkedIn link pointed
at **Suzan Zimmerman's** profile and his title field was empty.

### 6. One post was not carried over

`/cybersecurity/2020-security-breach-statistics/` ("2020 Security Cyber and Data Breach
Statistics", March 3 2021) had **no body text** — its entire content was a single infographic
image. Given the image-light decision, there was nothing to port.

The URL 301-redirects to `/insights/` so the inbound link does not 404. If you want the
content back, it needs re-authoring as text or a real SVG chart.

**18 of 19 posts were imported.**

### 7. Two referral forms were consolidated

`/referral-program-form/` and `/referral-form-non-vpn-test/` were separate WordPress form
pages. The rebuild replaces them with a referral section at `/careers/#referral`, and both
old URLs redirect there.

**The referral submit button is currently a `mailto:` link**, not a form. The legacy form was
a Contact Form 7 instance we did not reimplement. Options:

- keep `mailto:` (simplest),
- point it at the ATS if TeamTailor can capture referrals,
- or build a second Pages Function modelled on `functions/api/contact.js`.

Also note the legacy referral terms & conditions PDF link was already dead — it pointed at
`vidooridigital.wpcomstaging.com`, a staging domain that returns a WordPress 404 page. That
link is **not** reproduced. Supply a working PDF if the terms should be linked.

---

## Lower priority

### 8. No analytics

None was requested, so none was added. If you want it, Cloudflare Web Analytics is the
natural fit: no cookies, no client-side script, and it keeps the privacy policy's
"no tracking cookies" statement true. Anything cookie-based means the policy must change.

### 9. Twitter/X branding

The footer icon uses the current X glyph, but the account name (`@vidooriinc`) and URL
(`twitter.com/vidooriinc`) are unchanged and still redirect correctly. Update to `x.com` if
you prefer.

### 10. `logos/` and `assets/img/` hold duplicate SVGs

`logos/` contains the untouched originals — instructed not to edit. `assets/img/` holds
copies, which is what the site serves. They are byte-identical today. If a logo is ever
revised, update `logos/` and re-copy:

```bash
cp logos/vidoori-logo.svg logos/vidoori-logo-badge.svg assets/img/
```

### 11. ~~`--check` is not enforced automatically~~ (resolved 2026-09-01)

`.github/workflows/verify.yml` now runs `python3 tools/build.py --check` and
`python3 tools/check_links.py` on every push and pull request. A commit containing stale
generated HTML, a hand-edited root `.html` file, or a broken internal link fails CI.

Verified by deliberately editing `_src/` without rebuilding: `--check` exits 1 and names the
stale file. No `setup-python` step is needed — GitHub's Ubuntu runners ship Python 3 and both
scripts are stdlib-only.
