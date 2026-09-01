# Known issues and open decisions

Things found during the August 2026 rebuild that need a human decision, plus content
discrepancies inherited from the WordPress site. Nothing here blocks local development;
several items **do** block go-live.

---

## Blocking go-live

### 1. ~~Turnstile and Postmark configuration~~ (resolved 2026-09-01)

`_src/site.json` carries the live widget's site key `0x4AAAAAAEkCdhTn3knzXCzq` (widget
hostnames `vidoori.com`, which covers `test.vidoori.com`). All four required environment
variables are set in Cloudflare Pages.

**Verified end to end** on `test.vidoori.com`: a real contact-form submission was delivered to
`CONTACT_TO_EMAIL`. The endpoint returns 403 to a request carrying no Turnstile token, which
confirms the guard is active rather than merely configured.

Note the widget no longer always passes. Verification genuinely fails on any hostname not on
the widget's list — `localhost` is not on it, so forms cannot be exercised under
`python3 -m http.server`. Test on a preview deployment or `test.vidoori.com`.

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

### 6. ~~One post was not carried over~~ (won't do &mdash; owner decision, 2026-09-01)

`/cybersecurity/2020-security-breach-statistics/` ("2020 Security Cyber and Data Breach
Statistics", March 3 2021) had **no body text** &mdash; its entire content was a single
infographic image. Given the image-light decision, there was nothing to port.

Owner has decided not to re-author it. The URL 301-redirects to `/insights/`, in both bare and
trailing-slash spellings, so no inbound link 404s.

### 7. ~~Two referral forms were consolidated~~ (resolved 2026-09-01)

`/referral-program-form/` and `/referral-form-non-vpn-test/` were separate WordPress form
pages. Both redirect to `/careers/#referral`.

**Resolved:** that section is now a real form posting to `/api/referral`, implemented by
`functions/api/referral.js` and modelled on the contact form — same Turnstile widget, same
Postmark server, same honeypot and submit-timing bot checks, same no-JS fallback. It replaces
a `mailto:` link that captured nothing.

Captured fields: referrer name / email / phone, candidate name / email / phone, job title, an
optional resume-or-profile URL, free-text notes, an eligibility confirmation, and privacy
consent. Both checkboxes are recorded in the email so there is a record of what the referrer
agreed to. Email subject: `External Referral - <Candidate> for <Role>`.

**Deliberate omission — file upload.** The form takes a *link* to a resume, not a file.
Multipart parsing plus Postmark attachment encoding is a significant addition, and Postmark
caps attachments at 10 MB. The page tells referrers to email a resume file separately. Say so
if you want real uploads and it can be added.

**Still open:** the legacy referral terms & conditions PDF link was already dead before the
rebuild — it pointed at `vidooridigital.wpcomstaging.com`, a staging domain returning a
WordPress 404. It is not reproduced. The page states the program rules in prose, but for a
cash-incentive programme you probably want real linked T&Cs. Supply a PDF and it can be added.

---

## Lower priority

### 8. ~~No analytics~~ (resolved 2026-09-01)

Cloudflare Web Analytics is enabled and **confirmed reporting** &mdash; the dashboard shows
visits, page views, and Core Web Vitals. It is cookieless, so the privacy policy's "no
tracking cookies" statement stays true and needs no change.

One fix was required to get there: enabling it in the dashboard was not sufficient. The beacon
is injected at the edge from `static.cloudflareinsights.com`, which the CSP in `_headers` did
not allow, so the browser blocked it and nothing was collected. `script-src` now allows
`static.cloudflareinsights.com` and `connect-src` allows `cloudflareinsights.com`.

**If you ever add another third-party script, embed, or font host, add it to the CSP in
`_headers` in the same change** &mdash; it will work locally and be blocked in production
otherwise.

### 9. ~~Twitter/X branding~~ (resolved 2026-09-01)

**LinkedIn is now the only social property on the site.** Vidoori does not use X, so every
reference was removed rather than rebranded: the footer icon and link, the `twitter:card` and
`twitter:site` meta tags in `_src/partials/base.html`, the `external.twitter` entry in
`_src/site.json`, and the entry in the JSON-LD `sameAs` array.

Link previews are unaffected. They are driven by the Open Graph (`og:*`) tags, which every
platform reads &mdash; including X, which falls back to them when no `twitter:*` tags are
present.

`tools/build.py` builds `sameAs` from a filtered list rather than indexing `site.json`
directly, so removing another social property cannot raise a `KeyError`.

### 10. `logos/` and `assets/img/` hold duplicate SVGs &mdash; accepted

`logos/` contains the untouched originals &mdash; instructed not to edit. `assets/img/` holds
copies, which is what the site serves. They are byte-identical today. Owner has reviewed and
accepted this. If a logo is ever revised, update `logos/` and re-copy:

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
