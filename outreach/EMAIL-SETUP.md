# QuoteMySmile email — full setup

Everything the site and the outreach need, in the order to do it.

**Cost: one mailbox, $3.50/mo.** Every other address is an alias, which is free —
you do not need five mailboxes and should not buy them.

---

## The addresses the site actually uses

Counted from the codebase, not guessed:

| Address | Used by | Needs |
|---|---|---|
| `hello@quotemysmile.com.au` | general contact, JSON-LD, form capture | **real mailbox** |
| `clinics@quotemysmile.com.au` | dentist outreach reply-to, for-dentists page | alias → hello@ |
| `support@quotemysmile.com.au` | support page, App Store listing | alias → hello@ |
| `privacy@quotemysmile.com.au` | privacy policy (required contact) | alias → hello@ |
| `review@quotemysmile.com.au` | App Store review contact | alias → hello@ |
| `hello@mail.quotemysmile.com.au` | **sending only**, via Resend | DNS only, no mailbox |

That last one is the one people get wrong. `mail.quotemysmile.com.au` is a
*sending* subdomain — it never receives anything, so it needs no mailbox, only
DNS records. Keeping sending on a subdomain is deliberate: if a cold-email
campaign ever gets complained about, the damage is contained to the subdomain
and your main domain's reputation survives.

---

## Step 1 — Buy the mailbox (~5 min)

1. **godaddy.com** → sign in → **My Products**
2. Find **quotemysmile.com.au** → **Email & Office** → **Manage** / **Add Email**
3. **Microsoft 365 Email Essentials — $3.50/mailbox/mo**. 10 GB is plenty; you
   can upgrade later without changing the address.
4. Create the mailbox: **hello@quotemysmile.com.au**
5. GoDaddy adds the MX records automatically, because the domain is already
   registered with them.

Send yourself a test message to confirm it receives before moving on.

## Step 2 — Add the four aliases (~5 min, free)

In the same Email & Office manager, open the `hello@` mailbox and look for
**Aliases** / **Email aliases** (Microsoft 365 calls these *proxy addresses*).
Add all four:

```
clinics@quotemysmile.com.au
support@quotemysmile.com.au
privacy@quotemysmile.com.au
review@quotemysmile.com.au
```

Everything sent to any of them lands in the one inbox. You can also *send as*
an alias, which is worth doing: dentist replies should come from `clinics@`,
not `hello@`.

> If your plan hides aliases, the fallback is **Domains → quotemysmile.com.au →
> Email Forwarding**, which forwards each address to `hello@`. Forwarding
> receives fine but cannot send-as, so prefer aliases where available.

## Step 3 — DNS for sending (~10 min)

This is what stops the dentist outreach landing in spam. Records go in
**GoDaddy → My Products → quotemysmile.com.au → DNS → Manage Zones**.

### 3a. Get your values from Resend first

Resend dashboard → **Domains** → **Add Domain** → enter
`mail.quotemysmile.com.au`. It then shows you the exact records. **The DKIM
value is unique to your account — it cannot be written down here in advance, so
copy it from that screen.**

### 3b. Add the records

**DKIM** — Resend gives you a CNAME (sometimes three). Copy them exactly.

```
Type: CNAME
Name: resend._domainkey.mail      ← as shown by Resend
Value: (copy from Resend)
TTL: 1 hour
```

**SPF** — authorises Resend to send as that subdomain:

```
Type: TXT
Name: mail
Value: v=spf1 include:amazonses.com ~all
TTL: 1 hour
```

**DMARC** — tells receivers what to do with mail that fails the checks above.
Start at `p=none`, which only reports and never blocks:

```
Type: TXT
Name: _dmarc.mail
Value: v=DMARC1; p=none; rua=mailto:hello@quotemysmile.com.au
TTL: 1 hour
```

Once you have a few weeks of clean reports, tighten `p=none` to `p=quarantine`.
Do not start at quarantine or reject — a misconfiguration would silently bin
your own mail.

### 3c. Verify

Back in Resend, press **Verify**. DNS usually propagates in minutes, though
GoDaddy can take up to an hour. All three must show verified before you send.

## Step 4 — Test before any real send

```bash
cd ~/quotemysmile-site/outreach
export QMS_RESEND_API_KEY="re_..."          # QuoteMySmile's own key
python3 send_dentist_invite.py --csv leads-wyndham-dental.csv --send --only namtrantrandinh@gmail.com
```

Check it arrives, is not in spam, and that the reply-to lands back in `hello@`.
Then run a batch of 10 before the rest.

## Step 5 — Tell me, and I will switch the code

The moment `hello@` receives, say so and I will change in one pass:

- `waitlist.js` — form capture target (currently your Gmail)
- `index.html` — JSON-LD contact point
- `for-dentists.html`, `support.html` — contact addresses
- `build_qms_email.py`, `build_qms_email_safe.py` — footer + reply-to
- `send_dentist_invite.py` — `FROM` and `REPLY_TO`

---

## Why capture currently goes to Gmail

The forms post to FormSubmit, addressed to `namtrantrandinh@gmail.com` —
deliberately, because it is an inbox that **exists**. It was previously
addressed to `hello@quotemysmile.com.au`, which has no mailbox behind it, so
every reservation was posted into nothing.

**Before any traffic:** submit a form once on the live site, then click the
confirmation link FormSubmit emails you. Until that is clicked, submissions are
held rather than delivered. This is free and takes a minute — do it today,
regardless of the mailbox.
