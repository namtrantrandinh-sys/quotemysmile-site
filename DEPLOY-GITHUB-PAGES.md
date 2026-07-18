# Deploying quotemysmile.com.au via GitHub Pages + GoDaddy DNS

You keep the domain at GoDaddy. GitHub hosts the static site for free.
Every `git push` to `main` redeploys automatically.

## 1 · Push this repo to GitHub

```bash
cd /Users/nam/Projects/quotemysmile

git add -A
git commit -m "Initial commit: QuoteMySmile app + marketing site"

# Create the repo on github.com first (private or public, your call).
# Then add the remote — replace YOUR-USERNAME:
git remote add origin git@github.com:YOUR-USERNAME/quotemysmile.git
git push -u origin main
```

> If you don't have an SSH key on GitHub, use the HTTPS URL instead
> (`https://github.com/YOUR-USERNAME/quotemysmile.git`) — GitHub will
> prompt for a personal-access-token the first time.

## 2 · Enable GitHub Pages in the repo settings

1. Open `https://github.com/YOUR-USERNAME/quotemysmile/settings/pages`
2. Under **Source**, choose **GitHub Actions**
3. The workflow at `.github/workflows/pages.yml` is already in this repo;
   it deploys the `web/` folder on every push to `main`
4. Wait ~60 s for the first run. The Actions tab will show a green check.

After it succeeds, your site is live at
`https://YOUR-USERNAME.github.io/quotemysmile/` — but we want the
`quotemysmile.com.au` domain instead.

## 3 · Tell GitHub Pages about the custom domain

The `web/CNAME` file in this repo already contains:
```
quotemysmile.com.au
```
GitHub reads it on deploy. Once GoDaddy DNS resolves (next step), GitHub
auto-provisions a Let's Encrypt cert (5–15 minutes).

In the **Pages settings page** you should see "Custom domain" populated
with `quotemysmile.com.au` after the first push.

Also tick **Enforce HTTPS** once it appears (it usually appears within
15 min of DNS resolving).

## 4 · Add the GoDaddy DNS records

Log in to GoDaddy → **My Products → Domains → quotemysmile.com.au → DNS**.

Delete any existing `A` or `CNAME` records on `@` and `www` (they'll
conflict). Then add these:

| Type   | Name | Value                            | TTL     |
|--------|------|----------------------------------|---------|
| A      | @    | 185.199.108.153                  | 600     |
| A      | @    | 185.199.109.153                  | 600     |
| A      | @    | 185.199.110.153                  | 600     |
| A      | @    | 185.199.111.153                  | 600     |
| CNAME  | www  | YOUR-USERNAME.github.io          | 600     |

> Replace `YOUR-USERNAME` with your GitHub handle (lowercase, no
> trailing slash, no `https://`).

GitHub's published Pages IP addresses are exactly those four — if they
ever change you'll see a warning in the Pages settings page.

## 5 · Wait for DNS to propagate, then verify

DNS usually settles in 10–60 minutes. Check from your laptop:

```bash
dig +short quotemysmile.com.au
# Should return the four 185.199.x.x addresses

dig +short www.quotemysmile.com.au
# Should return YOUR-USERNAME.github.io and then the IPs
```

When that's clean, open `https://quotemysmile.com.au` — you should see
the marketing site with a valid green padlock.

## 6 · Future updates

Every time you edit anything in `web/` and push to `main`, the workflow
rebuilds and rolls out automatically. Hard refresh (Cmd-Shift-R) to
bypass the CDN cache.

## Common pitfalls

- **"Domain does not resolve to GitHub Pages" warning.** DNS hasn't
  propagated yet. Wait 15 min and click "Verify".
- **Cert pending forever.** Delete the custom domain in Pages settings,
  save, re-add it. GitHub re-issues the cert.
- **Mixed-content warnings.** All assets in `web/` use relative paths or
  HTTPS; there's no `http://` reference left in this site.
- **`www` shows 404 but apex works.** Either you skipped the `CNAME`
  record on `www`, or you typed it as `cname-on-www.github.io.` with a
  trailing dot — GoDaddy doesn't need the dot.
- **The legal copy on the site changes but the app screen still shows
  old text.** Privacy / Terms are duplicated in `app/legal/*.tsx` and
  `web/*.html` — update both in lockstep.

## Reverting to a previous build

```bash
git log --oneline -- web/        # find the commit you want
git revert <sha>
git push
```
The workflow republishes the reverted state.
