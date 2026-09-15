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

---

## Open after the September 2026 branch review

Raised on 2026-09-15 while reviewing `dave-sept-2026` before it became a pull request. The
branch&rsquo;s technical work is sound &mdash; the build succeeds, `check_links.py` reports no broken
internal links across 2267 references, every new CSS class is defined, and the new CSS uses
tokens throughout without tripping either documented colour trap. Everything below is an
editorial or factual decision for the owner rather than a defect.

### 12. OASIS 4 is claimed on the homepage and nowhere else

The homepage credentials block lists **OASIS 4** as a federal contract vehicle, and the stat
band was changed from three vehicles to four. `/who-we-are/contract-vehicles/` was not
updated and still lists three &mdash; GSA MAS `GS-35F-335CA`, GSA 8(a) STARS III
`47QTCB22D0131`, and SeaPort NxG. `_src/site.json` is unchanged as well, so the corporate
facts that feed the footer and JSON-LD still say three.

The site contradicts itself either way. **Confirm whether Vidoori holds OASIS 4.** If it
does, it needs its contract number, an entry on the contract-vehicles page, and a line in
`site.json`. If it does not, remove it from the homepage and restore the count to three. An
unheld vehicle advertised on the homepage of a federal contractor is a misrepresentation, so
settle this before the branch merges.

### 13. The homepage tagline was replaced

The hero previously read *Delivering Excellence Since 2008* over the headline *We are
dedicated to our client&rsquo;s mission.* &mdash; the company tagline. The branch replaces both with
*Federal and commercial IT consulting* and *Modernize mission-critical systems. Deliver with
confidence.*

The new copy is serviceable and matches the site&rsquo;s register. The point is that dropping the
tagline from the homepage is a brand decision, not a copy edit, and it should be made
deliberately. The tagline still appears elsewhere in the site&rsquo;s positioning language.

### 14. A raster image was added to the homepage &mdash; contradicts ADR 2

`assets/img/team-game.png` (1.9 MB, 1448&times;1086) was added to the *Join Our Team* section of
the homepage, replacing the inline SVG network diagram that was there. ADR 2 records that the
site is image-light by design: no photography, no icon font, diagrams hand-written as inline
SVG.

Owner has decided to **keep it for now**. Two follow-ups if it stays:

- **Resize and convert.** It renders far smaller than 1448px and PNG is the wrong format for
  illustration-style artwork. Roughly 800px wide as WebP should land under 100 KB. At 1.9 MB
  it is by a wide margin the heaviest asset the site serves, and unlike `site.css` and
  `site.js` it carries no version stamp.
- **Decide whether ADR 2 still holds.** If raster images are now acceptable, amend the ADR in
  `docs/architecture.md` so the next person is not working from a rule the site no longer
  follows.

### 15. Three leadership profiles were added and need confirmation

`/who-we-are/leadership/` gains David Lieberman (Chief Information Officer), Sahar Yamini (VP
Enterprise Transformation &amp; Applied AI), and Tim Withum (Chief Technology Officer), each with
a LinkedIn URL. The site previously listed two people.

**Titles and LinkedIn links need owner confirmation** &mdash; per the standing rule, facts about
the business are flagged rather than guessed. Two of the three bios are a single sentence and
read thin next to the fuller entries for Trong Bui and Eric Huang.

One structural note: profiles were converted from `<article>` to `<details>`/`<summary>`, so
each person&rsquo;s LinkedIn link now sits inside the collapsed region and is hidden until the bio
is expanded. It used to be visible at all times.

### 16. &ldquo;Leadership&rdquo; was relabelled &ldquo;Vidoori Team&rdquo; but the URL did not change

The nav, footer, page title, `<h1>`, and breadcrumb now read *Vidoori Team*; the path remains
`/who-we-are/leadership/`. That is the correct trade &mdash; the URL contract in ADR 3 matters
more than a tidy path, and changing it would cost a redirect rule for no benefit. Recorded
only so the mismatch between label and path is not later mistaken for an oversight.

### 17. Branch protection on `main` is not in place &mdash; blocked on the GitHub plan

The repository was transferred from `nsvidoori/vidoori.com` to the `vidoori` organization on
2026-09-15 so that rulesets could enforce a pull-request workflow on `main`. The org is on
**GitHub Free**, where rulesets are configurable but not enforced on private repositories.
Enforcement needs GitHub Team at $4/user/month, billed for every org member and every outside
collaborator with access to private repos &mdash; not just the people touching this site.

Open decision, three ways out:

- **Upgrade to Team.** Cost scales with org headcount, not with this repo.
- **Make this repository public.** Rulesets are free on public repos even in a free org, and
  it would not affect the org&rsquo;s other private repos. Check the git history for anything
  sensitive first; the site&rsquo;s secrets live in Cloudflare environment variables, not the repo.
- **Stay on Free without enforcement.** Pull requests work fine by convention; they simply
  cannot be required, so a direct push to `main` would deploy to production unchallenged.

Until this is settled, `main` is protected by agreement only. Note that every push to `main`
publishes to production, so an accidental push is a live change &mdash; recoverable by reverting,
but not prevented.
