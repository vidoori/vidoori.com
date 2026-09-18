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

### 12. ~~OASIS 4 is claimed on the homepage and nowhere else~~ (resolved 2026-09-18)

The branch added an **OASIS 4** contract-vehicle card to the homepage and raised the stat band
from three vehicles to four, while `/who-we-are/contract-vehicles/` and `_src/site.json` still
said three. No contract number appeared anywhere, `Vidoori_CapabilityStatement.pdf` had no
mention of OASIS at all, and &ldquo;OASIS 4&rdquo; is not a designation GSA uses &mdash; the
vehicle family is OASIS, OASIS SB and the OASIS+ successor.

**Owner confirmed both OASIS and 8(a) STARS III are no longer active**, so both were removed
from the live site on 2026-09-18:

- Homepage: the STARS III and OASIS 4 credential cards, and the stat band, now reading
  *2 &mdash; Federal contract vehicles: GSA MAS and SeaPort NxG*.
- `/who-we-are/contract-vehicles/`: the whole STARS III record, plus the meta description and
  the lede, which said &ldquo;Three vehicles&rdquo;.
- `/who-we-are/`: the Contract Vehicles card summary.
- `docs/content-catalog.md`: the STARS III row and the OASIS note, which had claimed the name
  was &ldquo;supplied by the site owner&rdquo;.
- `CLAUDE.md` section 8 corporate facts.

No `_redirects` rule was needed: no page or URL was removed, only sections within pages.

Two things deliberately left alone. The February 2022 announcement at
`/news/vidoori-awarded-contract-gsa-stars-iii/` is an accurate record of an award that did
happen and stays, per the rule that historical content is not live content. And
`assets/docs/Vidoori_CapabilityStatement.pdf` still lists STARS III &mdash; it is a binary the
build does not touch, so it needs replacing by whoever maintains it. See issue 18.

### 13. ~~The homepage tagline was replaced~~ (accepted 2026-09-18)

The hero previously read *Delivering Excellence Since 2008* over *We are dedicated to our
client&rsquo;s mission.* &mdash; the company tagline. The September rebuild replaced both with
*Federal and commercial IT consulting* and *Modernize mission-critical systems. Deliver with
confidence.*

**Owner reviewed and accepted this.** Not an oversight; do not re-raise it. The tagline itself
still lives in `_src/site.json` and continues to feed the site&rsquo;s positioning language.

### 13b. VAIL rotation length &mdash; accepted 2026-09-18

`/vail/` states a **6&ndash;9 month rotation**. The figure came from the owner&rsquo;s own
diagram and appears nowhere else on the site. **Owner confirmed it and accepted publication.**
Do not re-raise it.

### 14. A raster image was added to the homepage &mdash; contradicts ADR 2

`assets/img/team-game.webp` (86 KB, 1200&times;900) sits in the *Join Our Team* section of the
homepage, replacing the inline SVG network diagram that was there. ADR 2 records that the site
is image-light by design: no photography, no icon font, diagrams hand-written as inline SVG.

Owner has decided to **keep it**. One follow-up remains.

- ~~**Resize and convert.**~~ (resolved 2026-09-15) It arrived as a 1.9 MB, 1448&times;1086 PNG
  &mdash; the wrong format for flat-shaded illustration. Measured against the layout, the image
  never renders wider than about 823 CSS px: the `.split` grid gives it a 504 px column on
  desktop inside the 1152 px container, and its widest case is the single-column stack just
  below the 56rem breakpoint. Re-encoded at 1200&times;900 WebP q80, which covers desktop at 2&times;
  with room to spare. 1994 KB &rarr; 86 KB, a 95.7% reduction. The `width` and `height`
  attributes were updated to match so the reserved space stays correct.
- ~~**Decide whether ADR 2 still holds.**~~ (resolved 2026-09-18) Amended rather than
  abandoned. Illustration is now allowed where provenance is clean, no identifiable person
  appears, it is sized to the layout and ships as WebP with real `alt` text. Diagrams stay as
  markup or inline SVG. The amendment in `docs/architecture.md` carries the full conditions,
  including the version-stamp trap: images have no `?v=`, so a revision needs a new filename.

### 15. ~~Three leadership profiles were added and need confirmation~~ (confirmed 2026-09-18)

`/who-we-are/leadership/` gained David Lieberman (Chief Information Officer), Sahar Yamini (VP
Enterprise Transformation &amp; Applied AI), and Tim Withum (Chief Technology Officer), each with
a LinkedIn URL. The site previously listed two people.

**Owner checked the LinkedIn profiles and the titles on 2026-09-18 and confirmed both.** No
further verification needed; treat the three as authoritative alongside Trong Bui and Eric
Huang.

**Accepted as they stand, 2026-09-18.** The Lieberman and Withum bios are a single sentence
each against fuller entries for Bui and Huang. The owner has looked at it and is content with
the imbalance; it is a deliberate state, not missing copy. Do not re-raise it.

Related, and accepted on the same terms: `/vail/` describes who the lab is for in two ways
&mdash; &ldquo;college graduates&rdquo; in the body copy and &ldquo;juniors and new hires&rdquo;
in the flow diagram, which came from the owner&rsquo;s own artwork. Both readings are correct;
no reconciliation wanted.

Structural note for whoever next touches the page: each person&rsquo;s LinkedIn link lives in the
shared biography panel, so it is visible only while that person is open. Before the September
rebuild it sat in the card and was visible at all times.

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

### 18. ~~The capability statement PDF still lists 8(a) STARS III~~ (resolved 2026-09-18)

The PDF was a hand-made artefact that had drifted: it advertised STARS III after that vehicle
was retired, omitted FAA eFAST, listed Data Management as a core competency after that page
was removed, and routed contracting officers to a different person than the site did.

It is now generated by `tools/build_capability_statement.py` from a `CONTENT` block at the top
of the script &mdash; Python 3 standard library only, like the rest of `tools/`, so there is
nothing to install. The base-14 Helvetica fonts are referenced rather than embedded and the
logo is a JPEG XObject, which took the file from 110 KB to 27 KB.

Owner reviewed and adopted it on 2026-09-18. All sixteen items from the review were applied:
contact is now Haley Kubal at `contracts@vidoori.com` with no personal mobile, the vehicles are
GSA MAS / SeaPort-NxG / FAA eFAST, Software Development replaced Data Management, the lead copy
is the site boilerplate covering Government *and* Commercial, the unverified DCMA claim is gone,
VAIL is a differentiator, the two run-together bullets are split, and the footer carries a
revision date.

**Two things remain open.**

- **NAICS `519190` may be stale.** It was &ldquo;All Other Information Services&rdquo; under
  NAICS 2017 and was reclassified in the 2022 revision. It was carried over from the previous
  PDF and now also appears on `/who-we-are/contract-vehicles/`, so a correction means both
  places. Check the SAM.gov registration.
- ~~**Nothing enforces agreement between the PDF and the site.**~~ (resolved 2026-09-18)
  `python3 tools/build_capability_statement.py --check` now runs in
  `.github/workflows/verify.yml` beside the other two checks. It fails if the committed PDF
  does not match the generator, if the contract vehicles or core competencies disagree with the
  built site, if a UEI, CAGE or NAICS value on the sheet is missing from
  `/who-we-are/contract-vehicles/`, or if the layout overruns the footer. Verified against all
  three drift cases before shipping: an extra vehicle on the sheet, a practice removed from the
  site, and a `CONTENT` edit without a regenerate.

### 19. `build_capability_statement.py` has not migrated to `tools/pdfkit.py`

`tools/pdfkit.py` was factored out on 2026-09-18 so the capability statement and the SEWP
ordering guide would not become the kind of near-copy that `contact.js` and `referral.js`
already are. The ordering guide uses it. The capability statement still carries its own inline
copy of the same primitives &mdash; Helvetica metrics, wrapping, the object writer.

Left deliberately rather than done in passing: migrating changes the committed PDF's bytes
(the header version and object order differ), which `build_capability_statement.py --check`
would correctly flag, so it wants its own change with its own regenerate rather than riding
along with the SEWP work. Until then, a fix to the shared primitives has to be made twice.

### 20. The SEWP ordering guide is a draft with eight open placeholders

`assets/docs/Vidoori_SEWP_VI_Ordering_Guide.pdf` is linked from
`/who-we-are/contract-vehicles/nasa-sewp-vi/` and carries a DRAFT banner. It is structurally
complete and validates clean against PDF/UA-1, but eight values await the program manager:
the contract number, the effective date, the guide's own version and effective date, and the
name, title, direct telephone and direct email for each named contact.

`python3 tools/build_sewp_ordering_guide.py --check` lists what is still outstanding. The
banner disappears when none remain. **Do not issue to SEWP before then** &mdash; and note the
contract requires the guide to be live before the first delivery order, and republished within
ten business days of every contract modification.

### 21. PDF/UA conformance is not checked in CI

The ordering guide validates clean locally &mdash; veraPDF reports 106 rules passed, 0 failed,
`isCompliant: true` &mdash; but veraPDF is a Java tool that is not installed on the GitHub
runner, so CI only verifies the committed PDF matches the generator. A change to
`tools/pdfkit.py` could break conformance without CI noticing. Re-run veraPDF by hand after
touching the PDF code:

```bash
verapdf -f ua1 --format text assets/docs/Vidoori_SEWP_VI_Ordering_Guide.pdf
```
