# QuoteMySmile — Deploy runbook

End-to-end checklist for first production deploy. Follow top to bottom.

## 0. Pre-reqs (one-off)

- Apple Developer Program enrolment + Team ID
- App Store Connect record for `com.quotemysmile.app`
- Apple Pay merchant id `merchant.com.quotemysmile.app` provisioned + linked in Stripe Dashboard
- Google Play Console organisation
- Stripe Australia account, KYC complete (capabilities: card_payments, AU bank_transfer)
- Resend account, sender domain `mail.quotemysmile.com.au` verified (DKIM + SPF + DMARC)
- Twilio Verify service SID (AU sender id approved if needed)
- Sentry org `lordly-gp`, project `quotemysmile` exists, DSN copied
- Supabase project linked, region `ap-southeast-2`
- Google Cloud Console project, Maps SDK for iOS + Android enabled, two keys (each restricted to its bundle ID + the matching SDK)
- ABR GUID (`abr.business.gov.au/Tools/WebServices`)
- `quotemysmile.com.au` DNS + hosting (`web/` is shippable static)

## 1. Backend (Supabase)

```bash
# Link + push schema
supabase link --project-ref mqlaoxcjebzsihiocmzm
supabase db push --linked
```

Set every required secret:

```bash
supabase secrets set \
  STRIPE_SECRET_KEY="sk_live_…" \
  STRIPE_WEBHOOK_SECRET="whsec_…" \
  RESEND_API_KEY="re_…" \
  ABR_GUID="…" \
  PURGE_CRON_SECRET="$(openssl rand -hex 24)"
```

Deploy every edge function + smoke-test:

```bash
./scripts/deploy.sh
```

Schedule the two crons in Dashboard → Edge Functions → Cron:

| Function           | Cron        | Header                            |
| ------------------ | ----------- | --------------------------------- |
| purge-stale-data   | `0 14 * * *`| `X-QMS-Cron-Secret: <secret>`     |
| expire-requests    | `3 * * * *` | `X-QMS-Cron-Secret: <secret>`     |

Register the Stripe webhook (Dashboard → Webhooks):

- URL: `https://mqlaoxcjebzsihiocmzm.supabase.co/functions/v1/stripe-deposit-webhook`
- Subscribe to: `payment_intent.succeeded`, `payment_intent.payment_failed`, `charge.refunded`
- Paste the signing secret into `STRIPE_WEBHOOK_SECRET`

Verify migrations against a clean DB (sanity, optional):

```bash
./scripts/verify-migrations.sh
```

## 2. App config

Fill in the `REPLACE_…` placeholders in:

- `app.json` — `updates.url`, `extra.eas.projectId`, `owner`, `ios.config.googleMapsApiKey`, `android.config.googleMaps.apiKey`
- `.env.local` — `EXPO_PUBLIC_STRIPE_PUBLISHABLE_KEY`, `EXPO_PUBLIC_GOOGLE_MAPS_KEY_IOS`, `EXPO_PUBLIC_GOOGLE_MAPS_KEY_ANDROID`
- `eas.json` — `ascAppId`, `appleTeamId`, Play `serviceAccountKeyPath`

Generate icon + splash PNGs (see `assets/README.md`):

```bash
npx -y svgexport assets/source/icon.svg              assets/icon.png            1024:1024
npx -y svgexport assets/source/adaptive-icon-fg.svg  assets/adaptive-icon.png   1024:1024
npx -y svgexport assets/source/splash.svg            assets/splash.png          2048:2048
npx -y svgexport assets/source/notification-icon.svg assets/notification-icon.png 96:96
```

## 3. App Review demo account

Supabase Dashboard → Authentication → Users → Add user:

- Email: `review@quotemysmile.com.au`
- Enable email OTP

In `app/sign-in.tsx` the bypass branch is already wired: typing the review
email triggers the email-OTP path, no Twilio. Forward the inbox to a real
person before submission.

In App Store Connect → Submission → Sign-in information:

- Email: `review@quotemysmile.com.au`
- Password: leave blank
- Notes: "OTP via email. Enter the email; tap Email code; paste the code."

## 4. EAS build + submit

```bash
eas login
eas init                    # writes the projectId — paste it back into app.json
eas update:configure
eas build:configure
```

First TestFlight build:

```bash
./scripts/deploy.sh --eas preview
```

After QA, production submission:

```bash
eas build --profile production --platform all
eas submit --profile production --platform ios
eas submit --profile production --platform android
```

## 5. Marketing site

Static files in `web/`. Drop the directory onto any static host (Cloudflare
Pages / Vercel / GitHub Pages / S3) at `quotemysmile.com.au`. The legal
copy must stay in sync with `app/legal/privacy.tsx` and `app/legal/terms.tsx`.

```bash
# Example: rsync to an S3 bucket
aws s3 sync web/ s3://quotemysmile-www/ --delete --acl public-read
```

## 6. Smoke test the live system

Run through the patient flow on a TestFlight build:

1. Sign in with a real AU mobile (Twilio sends OTP)
2. Pick a category → guided photos → symptoms → location → urgency → submit
3. Confirm a demo dentist (seed 0015) appears on the live feed and map
4. Open quote detail, book consult, complete Stripe PaymentSheet with the
   Stripe test card `4242 4242 4242 4242`
5. Verify booking shows `confirmed`, deposit shows `paid`, push + email
   arrive
6. Cancel ≥24h before → deposit appears `refunded`
7. Re-create booking, dentist marks Attended → deposit appears `credited`,
   patient sees A$5 fee in the explainer

If any of these fail, check `/admin/events` for the audit row and the
Sentry breadcrumb trail.

## 7. Roll-back

- DB migration: `supabase migration repair --status reverted <version>`
  then `supabase db push --linked` (or hand-write the inverse SQL).
- Edge function: `supabase functions deploy <name> --import-map <prev>`
- App build: EAS Update — `eas update --branch production --message "rollback"`
