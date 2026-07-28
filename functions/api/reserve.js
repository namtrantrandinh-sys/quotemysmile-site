/**
 * Cloudflare Pages Function — receives waitlist and founding-practice
 * reservations. POST /api/reserve
 *
 * The site is already served by Cloudflare Pages, so this runs with no extra
 * hosting, no third-party form service and no account to create. It replaces
 * the mailto fallback, which depended on the visitor having a mail client
 * configured and having to press send themselves — most never did, so those
 * reservations were simply lost.
 *
 * It does two things with a submission:
 *   1. Writes it to the RESERVATIONS KV namespace, so there is a durable record
 *      independent of email delivery.
 *   2. Emails you a notification via Resend, so you hear about it immediately.
 * Either can be absent and the other still works — a submission is never
 * rejected just because a notification could not be sent.
 *
 * ── SETUP (Cloudflare dashboard → your Pages project → Settings) ────────────
 * Environment variables:
 *   RESEND_API_KEY   your QuoteMySmile Resend key (NOT LORDLY's)
 *   NOTIFY_EMAIL     where reservations should land, e.g. hello@quotemysmile.com.au
 *   FROM_EMAIL       a verified Resend sender, e.g. hello@mail.quotemysmile.com.au
 * Bindings → KV namespace:
 *   RESERVATIONS     bind a KV namespace under this name
 *
 * Everything is optional: with none of it set the endpoint still accepts and
 * acknowledges submissions, it just has nowhere to put them — so set at least
 * one before sending traffic here.
 */

const MAX_FIELD = 400;

function clean(v) {
  return typeof v === 'string' ? v.trim().slice(0, MAX_FIELD) : '';
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' },
  });
}

export async function onRequestPost({ request, env }) {
  let data;
  try {
    data = await request.json();
  } catch {
    return json({ ok: false, error: 'bad_json' }, 400);
  }

  // Honeypot: a bot fills every field it finds. Accept the request so it does
  // not retry, but drop it.
  if (clean(data._gotcha)) return json({ ok: true });

  const email = clean(data.email).toLowerCase();
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
    return json({ ok: false, error: 'invalid_email' }, 400);
  }

  const kind = data.kind === 'dentist' ? 'dentist' : 'patient';
  const record = {
    kind,
    email,
    name: clean(data.name),
    suburb: clean(data.suburb),
    clinic: clean(data.clinic),
    ahpra: clean(data.ahpra),
    treatments: clean(data.treatments),
    interest: clean(data.interest),
    received: new Date().toISOString(),
    ua: clean(request.headers.get('user-agent') || ''),
    country: request.headers.get('cf-ipcountry') || '',
  };

  // 1. Durable record. Keyed by kind+email so a repeat submission updates
  //    rather than creating a duplicate row to de-dupe later.
  if (env.RESERVATIONS) {
    try {
      await env.RESERVATIONS.put(`${kind}:${email}`, JSON.stringify(record));
    } catch (e) {
      console.error('KV write failed', e);
    }
  }

  // 2. Notify. Wrapped so a mail failure never costs us the reservation.
  if (env.RESEND_API_KEY && env.NOTIFY_EMAIL && env.FROM_EMAIL) {
    const rows = Object.entries(record)
      .filter(([k, v]) => v && !['ua', 'country'].includes(k))
      .map(([k, v]) => `<tr><td style="padding:4px 12px 4px 0;color:#6e6457;">${k}</td><td style="padding:4px 0;color:#2a2520;"><strong>${v}</strong></td></tr>`)
      .join('');
    try {
      await fetch('https://api.resend.com/emails', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${env.RESEND_API_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          from: env.FROM_EMAIL,
          to: [env.NOTIFY_EMAIL],
          reply_to: email,
          subject: kind === 'dentist'
            ? `New founding practice: ${record.clinic || record.name || email}`
            : `New patient waitlist: ${record.suburb || email}`,
          html: `<div style="font-family:Helvetica,Arial,sans-serif;font-size:14px;">
            <p style="margin:0 0 12px;">New <strong>${kind}</strong> reservation on quotemysmile.com.au</p>
            <table style="border-collapse:collapse;">${rows}</table>
          </div>`,
        }),
      });
    } catch (e) {
      console.error('Resend failed', e);
    }
  }

  return json({ ok: true });
}

// Anything other than POST — a crawler, someone pasting the URL — gets a plain
// answer rather than a Pages 404 that looks like the endpoint is broken.
export async function onRequest({ request }) {
  if (request.method === 'POST') return;
  return json({ ok: false, error: 'post_only' }, 405);
}
