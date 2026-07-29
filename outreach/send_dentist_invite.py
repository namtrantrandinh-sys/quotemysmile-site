#!/usr/bin/env python3
"""Send the QuoteMySmile founding-practice invite to a CSV of dental practices.

SAFETY: dry-run by default. Nothing leaves the machine unless you pass --send.

    # 1. see exactly what would go out, to whom
    python3 send_dentist_invite.py --csv leads-wyndham.csv

    # 2. send to yourself first — ALWAYS do this
    python3 send_dentist_invite.py --csv leads-wyndham.csv --send --only you@example.com

    # 3. small real batch, then widen
    python3 send_dentist_invite.py --csv leads-wyndham.csv --send --limit 10

CSV columns used: name, suburb, email  (extra columns are ignored)

Requires QMS_RESEND_API_KEY. QuoteMySmile keeps its own Resend account, sender
domain and suppression list — never reuse LORDLY credentials or senders, or a
complaint against one brand damages the other's deliverability.

Compliance (Spam Act 2003 (Cth)):
  - B2B inferred consent: only send to a PUBLISHED BUSINESS address, where the
    message relates to that business's functions. Do not send to addresses that
    belong to an individual rather than the practice.
  - Sender must be identified (in the footer) and reachable for 30 days.
  - A functional unsubscribe is mandatory; honour it within 5 working days.
    Every send records to sent.log and every opt-out belongs in suppress.txt.
"""
import argparse
import csv
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
TEMPLATE = HERE / "dentist-onboarding-email.SAFE.html"
SENT_LOG = HERE / "sent.log"
SUPPRESS = HERE / "suppress.txt"

FROM = "QuoteMySmile <hello@mail.quotemysmile.com.au>"
REPLY_TO = "namtrantrandinh@gmail.com"
SUBJECT = "Founding practice spot for {practice} in {suburb}"
SUBJECT_NO_SUBURB = "A founding practice spot for {practice}"
UNSUB_MAILTO = "mailto:namtrantrandinh@gmail.com?subject=unsubscribe"
UNSUB_URL = "https://quotemysmile.com.au/unsubscribe"

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def load_suppression() -> set:
    if not SUPPRESS.is_file():
        return set()
    out = set()
    for line in SUPPRESS.read_text("utf-8").splitlines():
        line = line.strip().lower()
        if line and not line.startswith("#"):
            out.add(line)
    return out


def already_sent() -> set:
    if not SENT_LOG.is_file():
        return set()
    out = set()
    for line in SENT_LOG.read_text("utf-8").splitlines():
        try:
            out.add(json.loads(line)["email"].lower())
        except Exception:
            continue
    return out


def personalise(html: str, row: dict) -> str:
    """Only the unsubscribe token is substituted; the body is deliberately generic.

    Mail-merging a practice name into body copy reads as mass mail the moment two
    clinics in the same street compare notes. The subject line carries the
    personalisation instead.
    """
    return html.replace("{{unsubscribe_url}}", UNSUB_URL)


def send_one(api_key: str, to: str, subject: str, html: str) -> tuple:
    payload = {
        "from": FROM,
        "to": [to],
        "reply_to": REPLY_TO,
        "subject": subject,
        "html": html,
        "headers": {
            "List-Unsubscribe": f"<{UNSUB_MAILTO}>, <{UNSUB_URL}>",
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
        },
    }
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return True, json.loads(r.read().decode()).get("id", "?")
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}: {e.read().decode()[:200]}"
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="lead CSV with name,suburb,email")
    ap.add_argument("--send", action="store_true", help="actually send (default: dry run)")
    ap.add_argument("--limit", type=int, default=0, help="cap the number sent")
    ap.add_argument("--only", help="send to this address only (test)")
    ap.add_argument("--delay", type=float, default=2.0, help="seconds between sends")
    args = ap.parse_args()

    if not TEMPLATE.is_file():
        print(f"missing {TEMPLATE.name} — run build_qms_email_safe.py first", file=sys.stderr)
        return 1
    html_base = TEMPLATE.read_text("utf-8")

    api_key = os.environ.get("QMS_RESEND_API_KEY", "")
    if args.send and not api_key:
        print("QMS_RESEND_API_KEY is not set. Refusing to send.", file=sys.stderr)
        print("QuoteMySmile must use its OWN Resend key, never LORDLY's.", file=sys.stderr)
        return 1

    suppressed = load_suppression()
    done = already_sent()

    rows, skipped = [], []
    with open(args.csv, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            email = (row.get("email") or "").strip().lower()
            name = (row.get("name") or "").strip()
            if not email:
                skipped.append((name, "no email"))
                continue
            if not EMAIL_RE.match(email):
                skipped.append((name, f"malformed: {email}"))
                continue
            if email in suppressed:
                skipped.append((name, "suppressed"))
                continue
            if email in done:
                skipped.append((name, "already sent"))
                continue
            if args.only and email != args.only.strip().lower():
                continue
            rows.append({"name": name, "suburb": (row.get("suburb") or "").strip(), "email": email})

    # De-dupe within the file — two branches of one group often share an inbox.
    seen, deduped = set(), []
    for r in rows:
        if r["email"] in seen:
            skipped.append((r["name"], "duplicate in file"))
            continue
        seen.add(r["email"])
        deduped.append(r)
    rows = deduped[: args.limit] if args.limit else deduped

    mode = "SEND" if args.send else "DRY RUN"
    print(f"\n=== {mode} ===")
    print(f"template : {TEMPLATE.name} ({len(html_base) // 1024} KB)")
    print(f"from     : {FROM}")
    print(f"queued   : {len(rows)}   skipped: {len(skipped)}")
    if skipped[:8]:
        for n, why in skipped[:8]:
            print(f"   skip: {n or '(unnamed)'} — {why}")
        if len(skipped) > 8:
            print(f"   … and {len(skipped) - 8} more")
    print()

    ok = fail = 0
    for i, r in enumerate(rows, 1):
        subject = (SUBJECT.format(practice=r["name"], suburb=r["suburb"])
                   if r["suburb"] else SUBJECT_NO_SUBURB.format(practice=r["name"]))
        subject = subject[:120]
        if not args.send:
            print(f"{i:3}. [dry] {r['email']:<42} {subject}")
            continue

        good, info = send_one(api_key, r["email"], subject, personalise(html_base, r))
        if good:
            ok += 1
            with open(SENT_LOG, "a", encoding="utf-8") as lg:
                lg.write(json.dumps({"email": r["email"], "name": r["name"], "id": info,
                                     "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}) + "\n")
            print(f"{i:3}. SENT {r['email']:<42} {info}")
        else:
            fail += 1
            print(f"{i:3}. FAIL {r['email']:<42} {info}")
        time.sleep(args.delay)

    if args.send:
        print(f"\nsent {ok}, failed {fail}. Log: {SENT_LOG.name}")
    else:
        print("\nDry run only. Add --send to actually deliver.")
        print("Send to yourself first:  --send --only you@example.com")
    return 0


if __name__ == "__main__":
    sys.exit(main())
