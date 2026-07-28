# Waitlist / founding-practice forms — activation

The two landing pages are **live-ready right now**:

- `/waitlist.html` — patient waitlist (also embedded on the homepage `#download` section + the homepage hero).
- `/for-dentists.html` — dentist founding-practice reservation.

Both use the shared handler `waitlist.js`. **Out of the box, with no setup, every
submission opens the visitor's email app pre-addressed to you** (patients →
`hello@quotemysmile.com.au`, dentists → `clinics@quotemysmile.com.au`). That works
immediately and is fine for the concierge stage — every signup lands in your inbox.

To **capture submissions to a database and get a clean email per signup**, do the
2-minute step below. Nothing else on the pages needs to change.

---

## Option A — Formspree (recommended, ~2 min, no code)

1. Go to <https://formspree.io> and create a free account.
2. Create **two** forms: one named `patients`, one named `dentists`.
   Set the notification email to the inbox you want (e.g. `hello@` and `clinics@`).
3. Each form gives you an endpoint like `https://formspree.io/f/abcd1234`.
4. Open `waitlist.js` and paste them into `ENDPOINTS`:

   ```js
   var ENDPOINTS = {
     patient: 'https://formspree.io/f/abcd1234',
     dentist: 'https://formspree.io/f/wxyz5678'
   };
   ```

5. Commit + push. Cloudflare Pages redeploys automatically. Done — the forms now
   POST straight to Formspree (which stores them + emails you), with the email
   fallback still kicking in only if the network call ever fails.

The hidden `_gotcha` field on every form is a honeypot; Formspree drops spam that
fills it, and `waitlist.js` silently no-ops it too.

---

## Option B — Your own Supabase (keeps data in QuoteMySmile infra)

Project ref `mqlaoxcjebzsihiocmzm` (region `ap-southeast-2`).

1. Create the table + insert-only RLS in the SQL editor:

   ```sql
   create table if not exists public.waitlist_signups (
     id          uuid primary key default gen_random_uuid(),
     kind        text not null check (kind in ('patient','dentist')),
     name        text,
     email       text not null,
     suburb      text,
     -- dentist-only
     clinic      text,
     ahpra       text,
     treatments  text,
     -- patient-only
     interest    text,
     created_at  timestamptz not null default now()
   );

   alter table public.waitlist_signups enable row level security;

   -- Anonymous visitors may INSERT only. No SELECT/UPDATE/DELETE for anon,
   -- so the list is never publicly readable.
   create policy "anon can insert waitlist"
     on public.waitlist_signups
     for insert to anon
     with check (true);
   ```

2. In `waitlist.js`, point each endpoint at the REST insert URL **and add the
   Supabase headers** to the `fetch` call (Supabase REST needs `apikey` +
   `Authorization: Bearer <ANON_KEY>` + `Prefer: return=minimal`). The anon
   ("publishable") key is safe to ship in client code — it only grants what RLS
   above allows (insert, no read). Add a `kind` field to the POST body so rows
   are tagged. Ask if you want me to wire this variant; Formspree is simpler
   unless you specifically want the data in Supabase.

---

## Where the pages are wired in

- Homepage (`index.html`): hero CTA → `/waitlist.html`; nav "Join waitlist"; the
  bottom `#download` section is now an inline email waitlist capture.
- `how-it-works.html`: nav + body CTAs → `/waitlist.html`.
- `for-dentists.html`: full reservation form in the `#reserve` section.
- Clean URLs: `/waitlist` and `/for-dentists` (see `_redirects`).

The App Store / Google Play links in `app.html` still contain
`REPLACE_WITH_APP_ID` — swap those in and flip the CTAs back to "Get the app"
once the app is live.
