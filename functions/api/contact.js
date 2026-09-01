/**
 * POST /api/contact — contact form handler.
 *
 * A Cloudflare Pages Function. The file path is the route: this file being at
 * functions/api/contact.js is what makes /api/contact work. There is no build
 * step and no npm dependency — Pages compiles this on deploy.
 *
 * Flow
 *   1. Parse JSON (fetch path) or form-encoded (no-JS path) body.
 *   2. Cheap bot checks: honeypot field, submit timing.
 *   3. Cloudflare Turnstile verification.
 *   4. Field validation (authoritative — the client-side copy is only UX).
 *   5. Send through the Postmark REST API.
 *
 * Required environment variables (Pages > Settings > Environment variables):
 *   POSTMARK_SERVER_TOKEN   Postmark *Server* API token (secret).
 *   TURNSTILE_SECRET_KEY    Turnstile secret key (secret).
 *   CONTACT_TO_EMAIL        Where inquiries are delivered.
 *   CONTACT_FROM_EMAIL      Must be a verified Postmark sender signature or
 *                           an address on a verified domain.
 * Optional:
 *   POSTMARK_MESSAGE_STREAM Defaults to "outbound".
 *   CONTACT_BCC_EMAIL       Optional archive copy.
 *
 * See docs/contact-form.md for setup and testing.
 */

const MAX_BODY_BYTES = 64 * 1024;
const MIN_SUBMIT_MS = 3000;        // humans take longer than this to fill it in
const MAX_SUBMIT_MS = 12 * 60 * 60 * 1000; // stale page; make them reload

const REGIONS = [
  'United States', 'Canada', 'Mexico', 'South America',
  'Europe', 'Asia', 'Africa', 'Australia',
];

const LIMITS = {
  firstName: 120,
  lastName: 120,
  email: 200,
  phone: 60,
  company: 200,
  region: 60,
  message: 5000,
};

/* -------------------------------------------------------------------------- */
/* Responses                                                                  */
/* -------------------------------------------------------------------------- */

const SUCCESS_MESSAGE =
  'Thank you — your message has been sent. We aim to respond within three business days.';

function wantsJson(request) {
  const accept = request.headers.get('Accept') || '';
  const ctype = request.headers.get('Content-Type') || '';
  return accept.includes('application/json') || ctype.includes('application/json');
}

function jsonResponse(payload, status) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store',
      'X-Robots-Tag': 'noindex',
    },
  });
}

function escapeHtml(value) {
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/**
 * No-JS fallback page. Kept deliberately self-contained (inline styles) so it
 * renders correctly even if the stylesheet is unavailable.
 */
function htmlResponse(title, body, status) {
  const page = `<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>${escapeHtml(title)} | Vidoori</title>
<link rel="stylesheet" href="/assets/css/site.css">
</head>
<body>
<main id="main" class="section" style="min-height:60vh">
  <div class="container container--narrow">
    <h1>${escapeHtml(title)}</h1>
    <p class="lede mt-5">${body}</p>
    <p class="mt-7"><a class="btn btn--primary" href="/">Return to vidoori.com</a></p>
  </div>
</main>
</body></html>`;
  return new Response(page, {
    status,
    headers: {
      'Content-Type': 'text/html; charset=utf-8',
      'Cache-Control': 'no-store',
      'X-Robots-Tag': 'noindex',
    },
  });
}

function fail(request, message, status) {
  if (wantsJson(request)) {
    return jsonResponse({ ok: false, error: message }, status);
  }
  return htmlResponse(
    'We could not send your message',
    `${escapeHtml(message)} You can also email
     <a href="mailto:info@vidoori.com">info@vidoori.com</a> directly.`,
    status
  );
}

function succeed(request) {
  if (wantsJson(request)) {
    return jsonResponse({ ok: true, message: SUCCESS_MESSAGE }, 200);
  }
  return htmlResponse('Message sent', escapeHtml(SUCCESS_MESSAGE), 200);
}

/* -------------------------------------------------------------------------- */
/* Parsing & validation                                                       */
/* -------------------------------------------------------------------------- */

async function parseBody(request) {
  const ctype = request.headers.get('Content-Type') || '';
  const raw = await request.text();

  if (raw.length > MAX_BODY_BYTES) {
    throw new Error('Your message is too large to submit.');
  }

  if (ctype.includes('application/json')) {
    try {
      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
        throw new Error('bad shape');
      }
      return parsed;
    } catch (err) {
      throw new Error('We could not read the submitted data.');
    }
  }

  // application/x-www-form-urlencoded (the <noscript> path)
  const params = new URLSearchParams(raw);
  const out = {};
  for (const [key, value] of params) out[key] = value;
  return out;
}

function str(value) {
  return typeof value === 'string' ? value.trim() : '';
}

function validate(data) {
  const errors = [];
  const clean = {};

  for (const field of ['firstName', 'lastName', 'email', 'phone', 'company', 'region', 'message']) {
    clean[field] = str(data[field]);
    if (clean[field].length > LIMITS[field]) {
      errors.push(`${field} is too long.`);
      clean[field] = clean[field].slice(0, LIMITS[field]);
    }
  }

  if (!clean.firstName) errors.push('First name is required.');
  if (!clean.lastName) errors.push('Last name is required.');
  if (!clean.company) errors.push('Company or organization is required.');

  if (!clean.email) {
    errors.push('Email address is required.');
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(clean.email)) {
    errors.push('Enter a valid email address.');
  }

  if (!clean.region) {
    errors.push('Country or region is required.');
  } else if (!REGIONS.includes(clean.region)) {
    // Reject anything not from our own <select>, rather than echoing it onward.
    errors.push('Select a country or region from the list.');
  }

  if (!clean.message) {
    errors.push('A message is required.');
  } else if (clean.message.length < 10) {
    errors.push('Please provide a little more detail in your message.');
  }

  const consent = str(data.privacyConsent) || (data.privacyConsent === true ? 'yes' : '');
  if (!consent) errors.push('Privacy policy consent is required.');

  clean.mediaInquiry = Boolean(str(data.mediaInquiry) || data.mediaInquiry === true);

  // Header-injection guard: newlines must never reach a mail header.
  for (const field of ['firstName', 'lastName', 'email', 'company', 'region', 'phone']) {
    clean[field] = clean[field].replace(/[\r\n]+/g, ' ');
  }

  return { errors, clean };
}

/** Reject obvious automation before spending a Turnstile or Postmark call. */
function botCheck(data) {
  if (str(data.website)) return 'rejected';           // honeypot was filled

  const startedAt = Number(data.started_at);
  if (Number.isFinite(startedAt) && startedAt > 0) {
    const elapsed = Date.now() - startedAt;
    if (elapsed < MIN_SUBMIT_MS) return 'too-fast';
    if (elapsed > MAX_SUBMIT_MS) return 'stale';
  }
  return null;
}

/* -------------------------------------------------------------------------- */
/* Turnstile                                                                  */
/* -------------------------------------------------------------------------- */

async function verifyTurnstile(token, secret, ip) {
  if (!token) return { ok: false, reason: 'missing-token' };

  const form = new FormData();
  form.append('secret', secret);
  form.append('response', token);
  if (ip) form.append('remoteip', ip);

  let res;
  try {
    res = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
      method: 'POST',
      body: form,
    });
  } catch (err) {
    return { ok: false, reason: 'network' };
  }

  if (!res.ok) return { ok: false, reason: 'http-' + res.status };

  const body = await res.json().catch(() => null);
  if (!body || body.success !== true) {
    return { ok: false, reason: (body && body['error-codes'] || []).join(',') || 'unknown' };
  }
  return { ok: true };
}

/* -------------------------------------------------------------------------- */
/* Postmark                                                                   */
/* -------------------------------------------------------------------------- */

function buildEmail(clean, env, meta) {
  const name = `${clean.firstName} ${clean.lastName}`.trim();
  const subjectTag = clean.mediaInquiry ? '[Media Inquiry]' : '[Website Inquiry]';
  const subject = `${subjectTag} ${name} — ${clean.company}`;

  const rows = [
    ['Name', name],
    ['Email', clean.email],
    ['Phone', clean.phone || '—'],
    ['Company', clean.company],
    ['Region', clean.region],
    ['Media inquiry', clean.mediaInquiry ? 'Yes' : 'No'],
  ];

  const textBody = [
    'New inquiry from vidoori.com',
    '',
    ...rows.map(([k, v]) => `${k}: ${v}`),
    '',
    'Message:',
    clean.message,
    '',
    '---',
    `Submitted: ${meta.timestamp}`,
    `Origin IP: ${meta.ip || 'unknown'}`,
    `Country: ${meta.country || 'unknown'}`,
  ].join('\n');

  const htmlBody = `<!doctype html><html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;color:#14152b;line-height:1.6">
  <h2 style="margin:0 0 16px;color:#414372">New inquiry from vidoori.com</h2>
  <table cellpadding="0" cellspacing="0" style="border-collapse:collapse;margin-bottom:20px">
    ${rows.map(([k, v]) => `<tr>
      <td style="padding:6px 18px 6px 0;font-weight:600;vertical-align:top;white-space:nowrap">${escapeHtml(k)}</td>
      <td style="padding:6px 0">${escapeHtml(v)}</td>
    </tr>`).join('')}
  </table>
  <div style="border-left:4px solid #9ad389;padding:4px 0 4px 16px;margin-bottom:24px">
    <div style="font-weight:600;margin-bottom:6px">Message</div>
    <div style="white-space:pre-wrap">${escapeHtml(clean.message)}</div>
  </div>
  <hr style="border:0;border-top:1px solid #e3e5ec">
  <p style="font-size:12px;color:#767c8c;margin:12px 0 0">
    Submitted ${escapeHtml(meta.timestamp)} &middot;
    IP ${escapeHtml(meta.ip || 'unknown')} &middot;
    Country ${escapeHtml(meta.country || 'unknown')}
  </p>
</body></html>`;

  const payload = {
    From: env.CONTACT_FROM_EMAIL,
    To: env.CONTACT_TO_EMAIL,
    Subject: subject,
    TextBody: textBody,
    HtmlBody: htmlBody,
    MessageStream: env.POSTMARK_MESSAGE_STREAM || 'outbound',
    // Replies go to the person who filled in the form, not to the sender
    // signature. The From address stays a verified domain so DMARC passes.
    ReplyTo: `${name} <${clean.email}>`,
    Tag: clean.mediaInquiry ? 'media-inquiry' : 'website-inquiry',
  };

  if (env.CONTACT_BCC_EMAIL) payload.Bcc = env.CONTACT_BCC_EMAIL;
  return payload;
}

async function sendViaPostmark(payload, token) {
  const res = await fetch('https://api.postmarkapp.com/email', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      'X-Postmark-Server-Token': token,
    },
    body: JSON.stringify(payload),
  });

  if (res.ok) return { ok: true };

  const detail = await res.text().catch(() => '');
  return { ok: false, status: res.status, detail: detail.slice(0, 500) };
}

/* -------------------------------------------------------------------------- */
/* Handlers                                                                   */
/* -------------------------------------------------------------------------- */

export async function onRequestPost(context) {
  const { request, env } = context;

  // Fail loudly in the log, generically to the user, if config is missing.
  const missing = ['POSTMARK_SERVER_TOKEN', 'TURNSTILE_SECRET_KEY',
                   'CONTACT_TO_EMAIL', 'CONTACT_FROM_EMAIL']
    .filter((key) => !env[key]);
  if (missing.length) {
    console.error('contact: missing environment variables:', missing.join(', '));
    return fail(request, 'The contact form is temporarily unavailable.', 503);
  }

  let data;
  try {
    data = await parseBody(request);
  } catch (err) {
    return fail(request, err.message, 400);
  }

  // Silently accept bot submissions: a bot that learns it was blocked adapts,
  // and a false positive should never look like an error to a real person.
  const bot = botCheck(data);
  if (bot) {
    console.log('contact: rejected submission (' + bot + ')');
    if (bot === 'stale') {
      return fail(request, 'This form has been open too long. Please reload the page and try again.', 400);
    }
    return succeed(request);
  }

  const { errors, clean } = validate(data);
  if (errors.length) {
    return fail(request, errors[0], 422);
  }

  const ip = request.headers.get('CF-Connecting-IP') || '';
  const country = (request.cf && request.cf.country) || '';

  const turnstile = await verifyTurnstile(
    str(data['cf-turnstile-response']), env.TURNSTILE_SECRET_KEY, ip
  );
  if (!turnstile.ok) {
    console.log('contact: turnstile failed (' + turnstile.reason + ')');
    return fail(request, 'Verification failed. Please reload the page and try again.', 403);
  }

  const payload = buildEmail(clean, env, {
    timestamp: new Date().toISOString(),
    ip,
    country,
  });

  const sent = await sendViaPostmark(payload, env.POSTMARK_SERVER_TOKEN);
  if (!sent.ok) {
    console.error('contact: postmark error', sent.status, sent.detail);
    return fail(
      request,
      'We could not send your message right now. Please try again shortly.',
      502
    );
  }

  return succeed(request);
}

/** Anything other than POST gets a clear answer rather than the SPA shell. */
export async function onRequest(context) {
  if (context.request.method === 'POST') return onRequestPost(context);

  if (context.request.method === 'OPTIONS') {
    return new Response(null, {
      status: 204,
      headers: { Allow: 'POST, OPTIONS' },
    });
  }

  return new Response('Method Not Allowed. Use POST.', {
    status: 405,
    headers: { Allow: 'POST, OPTIONS', 'Content-Type': 'text/plain; charset=utf-8' },
  });
}
