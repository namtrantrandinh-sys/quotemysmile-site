#!/usr/bin/env python3
"""Swap the contact addresses across the whole site and outreach in one pass.

    python3 set_contact_email.py --live     # switch to the quotemysmile.com.au addresses
    python3 set_contact_email.py --gmail    # switch back to the founder's gmail
    python3 set_contact_email.py --check    # report what is currently in use, change nothing

Addresses were scattered across nine files — page footers, JSON-LD, the support
page, the form handler, both email builders and the sender. Editing them by hand
is how one gets missed, and a missed one is not cosmetic: capture was pointed at
hello@quotemysmile.com.au before that mailbox existed, so every reservation was
posted into nothing.

Run --live the day the mailbox actually receives, not before.
"""
import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GMAIL = "namtrantrandinh@gmail.com"

# role -> live address. Every one of these is an alias on the single hello@
# mailbox, so they all land in the same inbox.
LIVE = {
    "general": "hello@quotemysmile.com.au",
    "clinics": "clinics@quotemysmile.com.au",
    "support": "support@quotemysmile.com.au",
    "privacy": "privacy@quotemysmile.com.au",
    "review": "review@quotemysmile.com.au",
}

# (file, role) pairs — which address each file should carry.
TARGETS = [
    ("index.html", "general"),
    ("waitlist.html", "general"),
    ("how-it-works.html", "general"),
    ("for-dentists.html", "clinics"),
    ("support.html", "support"),
    ("privacy.html", "privacy"),
    ("terms.html", "general"),
    ("waitlist.js", "general"),
    ("outreach/build_qms_email.py", "clinics"),
    ("outreach/build_qms_email_safe.py", "clinics"),
    ("outreach/send_dentist_invite.py", "clinics"),
]

ADDR = re.compile(
    r"\b(?:namtrantrandinh@gmail\.com"
    r"|(?:hello|clinics|support|privacy|review)@quotemysmile\.com\.au)\b"
)


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--live", action="store_true", help="use the quotemysmile.com.au addresses")
    g.add_argument("--gmail", action="store_true", help="use the founder's gmail")
    g.add_argument("--check", action="store_true", help="report only")
    a = ap.parse_args()

    changed = 0
    for name, role in TARGETS:
        p = ROOT / name
        if not p.is_file():
            print(f"  skip (missing): {name}")
            continue
        text = p.read_text("utf-8")
        found = sorted(set(ADDR.findall(text)))

        if a.check:
            print(f"  {name:38} {', '.join(found) if found else '(none)'}")
            continue

        want = LIVE[role] if a.live else GMAIL
        new = ADDR.sub(want, text)
        if new != text:
            p.write_text(new, "utf-8")
            changed += 1
            print(f"  {name:38} -> {want}")

    if a.check:
        print("\nSending domain is separate and NOT touched here: mail.quotemysmile.com.au")
        print("(sending only, no mailbox — see EMAIL-SETUP.md)")
        return 0

    print(f"\n{changed} file(s) updated.")
    if a.live:
        print("Bump the ?v= on waitlist.js in the three pages, or browsers keep")
        print("serving the cached handler with the old address.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
