# quotemysmile.com.au — marketing site

Pure static. The active stack is:

> **GoDaddy** (domain registrar only) → **DNS pointed at GitHub Pages**

GitHub Pages is free, HTTPS auto-issued, and the GitHub Actions workflow
at `.github/workflows/pages.yml` redeploys this folder on every push to
`main`. The `web/CNAME` file tells GitHub which custom domain to serve.

**Full runbook with the exact GoDaddy DNS records:**
[`docs/DEPLOY-GITHUB-PAGES.md`](../docs/DEPLOY-GITHUB-PAGES.md)

The Cloudflare Pages path below stays documented as an alternative if
you ever want bot protection / edge analytics / Workers.

---

## Alternative — Cloudflare Pages instead of GitHub Pages

### 1 · Create the Cloudflare Pages project

1. Sign in to <https://dash.cloudflare.com>
2. **Workers & Pages → Create application → Pages → Connect to git**
3. Point at this repo (`quotemysmile`), branch `main`
4. **Build settings**:
   - Framework preset: **None**
   - Build command: *(blank — no build step)*
   - Build output directory: **`web`**
5. Save → first deploy runs in 30 s.

Cloudflare will give you a default URL like
`quotemysmile.pages.dev`. Confirm the site loads there.

### 2 · Add the custom domain in Cloudflare

1. In the Pages project → **Custom domains → Set up a custom domain**
2. Enter `quotemysmile.com.au`
3. Also add the redirect: `www.quotemysmile.com.au`
4. Cloudflare prints the two records you need to add at GoDaddy:
   - A CNAME from `quotemysmile.com.au` → `<project>.pages.dev`
   - A CNAME from `www` → `<project>.pages.dev`

> If GoDaddy doesn't let you CNAME the apex, the cleaner path is to migrate
> nameservers (next step). Otherwise GoDaddy's "Forwarding" record on the
> apex works as a fallback.

### 3 · Point GoDaddy DNS at Cloudflare (one-time)

The fully-managed path is moving nameservers. Cloudflare then handles every
record and gives you instant HTTPS.

1. In Cloudflare, **Domains → Add site** → `quotemysmile.com.au` → Free plan
2. Cloudflare lists the records it found at GoDaddy. Click **Continue**
3. Cloudflare shows you 2 nameservers, e.g.
   `aaron.ns.cloudflare.com` and `mia.ns.cloudflare.com`
4. Open GoDaddy → **My products → Domains → quotemysmile.com.au → DNS →
   Nameservers → Change → Enter my own nameservers**
5. Paste both Cloudflare nameservers, save.
6. Wait 10–60 minutes (sometimes faster). `dig NS quotemysmile.com.au` should
   show Cloudflare.
7. Back in Cloudflare → **DNS → Records**, add:
   - `CNAME  @     <project>.pages.dev   Proxied`
   - `CNAME  www   <project>.pages.dev   Proxied`
8. **SSL/TLS → Overview → Full (strict)**
9. **Rules → Page Rules → Always Use HTTPS** for `*.quotemysmile.com.au/*`

That's it — `https://quotemysmile.com.au` should resolve. Cloudflare also
gives you analytics, bot protection, and Workers if you ever need server-side
logic.

### 4 · Push updates

Every git push to `main` triggers a Pages rebuild and rollout. No FTP.

---

## Option B — Stay on GoDaddy DNS, host on Cloudflare Pages

If you'd rather not move nameservers, you can keep GoDaddy DNS and just add
two records there.

1. Create the Cloudflare Pages project (Option A · step 1).
2. In **Cloudflare Pages → Custom domains → Add** the apex + `www`. Cloudflare
   gives you a TXT verification record and a CNAME target.
3. In **GoDaddy DNS** → add:
   - `CNAME  www   <project>.pages.dev`
   - `TXT    @     <token Cloudflare gives you>` for verification
   - For the apex, use GoDaddy's built-in **Domain Forwarding** to
     `https://www.quotemysmile.com.au` (some GoDaddy plans allow apex CNAME
     directly).
4. Wait for verification (a few minutes).

This works but you lose Cloudflare's apex flattening; for the cleanest setup
prefer Option A.

---

## Option C — Host directly on GoDaddy cPanel (last resort)

Use this only if you've already paid for GoDaddy Web Hosting and want it for
parity.

1. Log in to GoDaddy → **My Products → Web Hosting → cPanel admin**
2. Open **File Manager → public_html**
3. Delete the default `index.html`
4. Upload the contents of `web/` (drag every file, or zip + extract). Keep
   the same directory structure.
5. GoDaddy serves `index.html` automatically.
6. **AutoSSL** in cPanel issues a Let's Encrypt cert (10 min).
7. For clean URLs without `.html`, add `.htaccess`:

   ```apache
   RewriteEngine On
   RewriteCond %{REQUEST_FILENAME} !-f
   RewriteCond %{REQUEST_FILENAME} !-d
   RewriteRule ^([^./]+)$ $1.html [L]
   ErrorDocument 404 /404.html
   ```

This path uses GoDaddy for both the domain and the hosting. Trade-off:
slower edge cache, no auto-deploy from git, manual SSL renewal in some plans.

---

## What's in this folder

| File                  | Purpose                                            |
| --------------------- | -------------------------------------------------- |
| `index.html`          | Marketing landing page                             |
| `how-it-works.html`   | Long-form patient walkthrough                      |
| `for-dentists.html`   | Dentist-targeted page + apply CTA                  |
| `privacy.html`        | Privacy policy (must stay in sync with app)        |
| `terms.html`          | Terms of service                                   |
| `support.html`        | Contact + escalation paths                         |
| `404.html`            | Custom not-found                                   |
| `style.css`           | Shared editorial CSS                               |
| `favicon.svg`         | Allura `m` glyph on bone background                |
| `apple-touch-icon.png`| Home-screen icon (1024×1024 copy of `assets/icon.png`) |
| `og.png` + `og.svg`   | OpenGraph share card (1200×630)                    |
| `site.webmanifest`    | PWA manifest                                       |
| `robots.txt`          | Allows everything, points at sitemap               |
| `sitemap.xml`         | 6 canonical pages                                  |
| `_redirects`          | Clean URLs + 404 fallback (Cloudflare/Netlify)     |
| `_headers`            | Security headers + cache rules                     |

## Local preview

```bash
cd web && python3 -m http.server 3001
# then open http://localhost:3001
```

## Sync from app

The in-app legal screens at `app/legal/privacy.tsx` and `app/legal/terms.tsx`
must match `privacy.html` / `terms.html` word-for-word. When you change one,
update the other.
