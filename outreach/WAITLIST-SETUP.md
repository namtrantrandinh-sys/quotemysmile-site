# Reservation capture — setup

Both forms (`/waitlist` patient, `/for-dentists` founding practice) POST to
**`/api/reserve`**, a Cloudflare Pages Function that lives in this repo at
`functions/api/reserve.js`. Because the site is already on Cloudflare Pages it
deploys with the site — no form service, no extra hosting, no account to create.

It does two independent things with each submission, so neither is a single
point of failure:

1. **Writes it to KV** — a durable record that survives regardless of email.
2. **Emails you via Resend** — so you hear about it straight away.

## What to set (Cloudflare dashboard → Pages project → Settings)

**Environment variables**

| Name | Value |
|---|---|
| `RESEND_API_KEY` | QuoteMySmile's own Resend key. **Never LORDLY's** — a complaint against one brand would damage the other's sending reputation. |
| `NOTIFY_EMAIL` | Where reservations land, e.g. `hello@quotemysmile.com.au` |
| `FROM_EMAIL` | A verified Resend sender, e.g. `hello@mail.quotemysmile.com.au` |

**Bindings → KV namespace**

| Binding name | Namespace |
|---|---|
| `RESERVATIONS` | Create one (any name) and bind it as `RESERVATIONS` |

Every one of these is optional in the sense that the endpoint still returns
success without them — but then the submission has nowhere to go. **Set at least
the KV binding before sending any traffic to the site.**

## Reading the reservations

Dashboard → Workers & Pages → KV → your namespace. Keys are `dentist:<email>`
and `patient:<email>`, so a repeat submission updates the existing entry instead
of leaving you duplicates to reconcile. Values are JSON with name, clinic,
suburb, AHPRA number, treatments/interest and a received timestamp.

## Why not mailto

The forms previously fell back to opening the visitor's mail client with a
prefilled message. That looked like it worked, but it needed the visitor to
have a mail client configured **and** to press send — most never did, so the
reservation vanished with no trace at either end. mailto now only triggers if
the API call itself fails, and the visitor is told plainly that it happened.

## AHPRA number

Deliberately optional on the reservation form. Verification happens **before a
practice goes live**, not at reservation, and the page copy says so. Supplying
the number early just lets us check ahead of launch; if it is absent we ask at
activation. Do not reword this to imply verification happens at signup — it
does not, and a practice could otherwise believe it has been checked when it
has not.
