# Contact form: Postmark and Turnstile

The form at `/contact/` posts to `/api/contact`, which is implemented by
`functions/api/contact.js` — a Cloudflare Pages Function. The file's path *is* the route:
`functions/api/contact.js` serves `/api/contact`. There is no router to configure.

## What happens on submit

1. **Parse.** JSON when JavaScript posts it, `application/x-www-form-urlencoded` on the
   no-JS path. Bodies over 64 KB are rejected.
2. **Bot heuristics.** Honeypot field, then submit timing. See
   [architecture ADR 5](architecture.md#adr-5-cloudflare-turnstile-for-spam-layered-over-cheap-heuristics).
3. **Turnstile.** Server-side verification against Cloudflare's `siteverify` endpoint.
4. **Validation.** Required fields, email shape, length caps, and `region` must be one of
   the eight values from our own `<select>`. This is authoritative — the client-side copy in
   `site.js` exists only so users get feedback without a round trip.
5. **Send.** Postmark REST API (`POST https://api.postmarkapp.com/email`).

Newlines are stripped from every field that reaches a mail header, so the form cannot be
used for header injection.

## Environment variables

Set these in **Cloudflare Pages → your project → Settings → Environment variables**. Add
them to *both* Production and Preview if you want the form working on preview deployments.

| Variable | Type | Value |
|---|---|---|
| `POSTMARK_SERVER_TOKEN` | Secret | Postmark **Server** API token (not the Account token) |
| `TURNSTILE_SECRET_KEY` | Secret | Turnstile secret key |
| `CONTACT_TO_EMAIL` | Plaintext | Where inquiries are delivered, e.g. `info@vidoori.com` |
| `CONTACT_FROM_EMAIL` | Plaintext | Must be a verified Postmark sender signature, or an address on a verified domain |
| `POSTMARK_MESSAGE_STREAM` | Plaintext | Optional; defaults to `outbound` |
| `CONTACT_BCC_EMAIL` | Plaintext | Optional archive copy |

If any of the four required variables is missing, the endpoint returns HTTP 503 with a
generic message and logs the names of the missing variables. Check
**Pages → Deployments → Functions → Real-time logs**.

### Why `From` is not the visitor's address

`From` is always `CONTACT_FROM_EMAIL` (a verified domain) so SPF/DKIM/DMARC pass. The
visitor's address goes in `ReplyTo`, so hitting reply in your mail client answers them
directly. Putting a visitor's address in `From` would get the mail spam-filtered or rejected.

## Turnstile keys

Turnstile has two keys. They are not interchangeable:

- **Site key** — public, safe to commit. It lives in `_src/site.json` as `turnstileSiteKey`
  and `tools/build.py` injects it into the `data-sitekey` attribute at build time.
- **Secret key** — never commit. It goes in the Pages environment variable above.

**The repo ships the live site key `0x4AAAAAAEkCdhTn3knzXCzq`** (widget hostname
`vidoori.com`, which also covers `test.vidoori.com`). The matching **secret key must be set
as the `TURNSTILE_SECRET_KEY` Pages environment variable** — until it is, `/api/contact`
returns 503.

Because this is a real widget rather than the always-passes test key, verification fails on
any hostname not on the widget's list. `localhost` is not on it, so the widget will not
validate under `python3 -m http.server`; test on a preview deployment or `test.vidoori.com`.

If the widget is ever rotated or replaced:

1. Create or edit the widget at <https://dash.cloudflare.com/?to=/:account/turnstile>.
2. Put the new site key in `_src/site.json`.
3. Run `python3 tools/build.py`.
4. Update the secret key in the Pages environment variable.

Cloudflare's other test keys are useful while developing:

| Site key | Behaviour |
|---|---|
| `1x00000000000000000000AA` | always passes |
| `2x00000000000000000000AB` | always blocks |
| `3x00000000000000000000FF` | forces an interactive challenge |

Matching test secret keys: `1x0000000000000000000000000000000AA` (always passes) and
`2x0000000000000000000000000000000AA` (always fails).

## Testing locally

`python3 -m http.server` cannot run Pages Functions — submitting the form against it will
404. To exercise the real function you need Wrangler, which means Node:

```bash
npx wrangler pages dev .
```

That contradicts the project's no-Node rule for *deployment*, which is why Wrangler is not
part of the workflow and is not in any config file. Two practical options:

- **Preferred:** test on a Cloudflare **preview deployment**. Push a branch, let Pages build
  it, and submit the real form with real environment variables. No local Node required.
- **If you do use Wrangler:** it is a transient dev-only tool. Do not add it to the repo, do
  not create a `package.json`, and do not add a build command to the Pages project.

To check the endpoint's shape without Turnstile passing:

```bash
curl -i -X POST https://<your-preview>.pages.dev/api/contact \
  -H 'Content-Type: application/json' \
  -d '{"firstName":"Test","lastName":"User","email":"t@example.com","company":"Acme","region":"United States","message":"This is a test message.","privacyConsent":"yes"}'
```

Expect `403` with `Verification failed` — the request had no Turnstile token, which proves
the guard is active. A `503` instead means environment variables are missing.

## Changing the form fields

Three places must agree, or you will get confusing validation failures:

1. `_src/pages/contact.html` — the input's `name` attribute.
2. `assets/js/site.js` — only if the field needs custom client-side validation.
3. `functions/api/contact.js` — the `LIMITS` object, the loop in `validate()`, and the
   `rows` array in `buildEmail()` so the value actually appears in the email.

The `region` field additionally has an allow-list (`REGIONS`) in the Function that must match
the `<option>` values in the page.

## Legacy field names

The WordPress form (Contact Form 7) used names like `your-name`, `text-company`,
`menu-region`. The rebuild uses clean camelCase (`firstName`, `company`, `region`). Nothing
external consumed the old names — Postmark received rendered email, not field names — so
there was no reason to carry them forward.
