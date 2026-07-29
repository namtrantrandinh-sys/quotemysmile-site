# Reservation capture — how it works

**The site is on GitHub Pages, which is static-only.** There is no server we can
run alongside it, so form capture has to post to an external endpoint. (An
earlier attempt used a Cloudflare Pages Function — that can never execute on
GitHub Pages, which is why the form appeared to fail and fell back to opening a
mail client.)

## Current setup — no account, no keys

Both forms post to **FormSubmit**, configured in `waitlist.js`. Each reservation
is emailed as a table. Nothing to sign up for and no API key in the repo.

The target is currently **`namtrantrandinh@gmail.com`** — deliberately, because
it is an inbox that EXISTS. It was previously addressed to
`hello@quotemysmile.com.au`, which has no mailbox behind it, so every
reservation was posted into nothing. Move it once that mailbox is real; see
`EMAIL-SETUP.md`.

### ⚠️ One-time step before this captures anything

The **first** submission triggers a confirmation email to that address. **Click
the link in it once.** Until you do, submissions are held and not delivered. Do
this before sending any traffic: submit the form yourself once, then check the
inbox.

## Moving to something sturdier later

FormSubmit is right for a pre-launch waitlist: zero friction, and volumes are
low. Two reasons you would move:

- **Volume or reliability.** It is a free third-party service with no SLA.
- **Data handling.** Reservations pass through their servers. The fields are
  business contact details plus an AHPRA number (public register data), not
  health information — but it is still a third party in the path.

To switch, change `ENDPOINT` in `waitlist.js`. Everything else is
provider-agnostic. Options in rough order of effort:

| Option | Setup | Notes |
|---|---|---|
| Formspree | Free account, ~2 min | 50 submissions/month free, dashboard, spam filtering |
| Basin / Getform | Free account | Similar, exports to CSV |
| Move hosting to Cloudflare Pages | ~15 min | Then a Pages Function can store to KV and email via your own Resend key, keeping data in your own infrastructure |

## AHPRA number

Deliberately optional on the reservation form. Verification happens **before a
practice goes live**, not at reservation, and the page copy says so. Supplying
the number early lets us check ahead of launch; if it is absent we ask at
activation. Do not reword this to imply verification happens at signup — it does
not, and a practice could otherwise believe it has been checked when it has not.
