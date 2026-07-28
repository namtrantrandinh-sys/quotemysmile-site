#!/usr/bin/env python3
"""Build the EMAIL-SAFE version of the QuoteMySmile founding-dentist invite.

dentist-onboarding-email.html is a browser preview: it uses flexbox, CSS custom
properties, @supports, background-clip:text and keyframe animation. Gmail strips
custom properties, Outlook (Word engine) ignores flexbox and border-radius, and
nobody animates. Sending that file would land as a broken wall of text.

This emits the version that actually goes down the wire:
  - <table> layout only, no flex/grid
  - every style inlined on the element, no <style> block relied upon
  - explicit `font-family:` (never the `font:` shorthand — Outlook drops it)
  - hosted logo (base64 <img> is blocked or stripped by most clients)
  - bulletproof VML button so the CTA is clickable in Outlook
  - List-Unsubscribe friendly footer with sender identification (Spam Act 2003)

Usage: python3 build_qms_email_safe.py
Out:   outreach/dentist-onboarding-email.SAFE.html
"""
import pathlib

OUT = pathlib.Path(__file__).resolve().parent / "dentist-onboarding-email.SAFE.html"

# Hosted, not embedded. Upload these to the site before sending.
LOGO = "https://quotemysmile.com.au/icon-192.png"
CTA_URL = "https://quotemysmile.com.au/for-dentists"

TEAL = "#2F6F66"
TEAL_DK = "#1F4F47"
MINT = "#A9CFC0"
MINT_BG = "#E6F1EC"
INK = "#1E3A34"
BODY = "#4A5551"
MUTED = "#7F8B86"
LINE = "#D8E7E0"

SANS = "Helvetica,Arial,sans-serif"
SERIF = "Georgia,'Times New Roman',serif"


def step(icon_char: str, title: str, body: str) -> str:
    """One numbered step row. Table, not flex — Outlook ignores flex entirely."""
    return f"""
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="margin:0 0 22px 0;">
                <tr>
                  <td width="46" valign="top" style="width:46px;padding-right:14px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="42" style="width:42px;">
                      <tr><td align="center" valign="middle" height="42" style="height:42px;background-color:{MINT_BG};border:1px solid {MINT};border-radius:21px;font-family:{SERIF};font-size:17px;color:{TEAL_DK};">{icon_char}</td></tr>
                    </table>
                  </td>
                  <td valign="top">
                    <p style="margin:2px 0 4px 0;font-family:{SANS};font-size:16px;font-weight:bold;line-height:1.3;color:{INK};">{title}</p>
                    <p style="margin:0;font-family:{SANS};font-size:14px;line-height:1.6;color:{BODY};">{body}</p>
                  </td>
                </tr>
              </table>"""


def bullet(text: str) -> str:
    return f"""
                <tr>
                  <td width="22" valign="top" style="width:22px;font-family:{SANS};font-size:14px;line-height:1.55;color:{TEAL};">&#10003;</td>
                  <td valign="top" style="font-family:{SANS};font-size:14px;line-height:1.55;color:{BODY};padding-bottom:10px;">{text}</td>
                </tr>"""


FEE_EM = f'<strong style="color:{TEAL_DK};">$5 per attended booking</strong>'
STEP_3 = (
    "Patients book with a refundable deposit, so the ones who reach you are "
    f"serious. You pay a flat {FEE_EM}. No lead fees, no subscription."
)

HTML = f"""<!doctype html>
<html lang="en" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="x-apple-disable-message-reformatting">
<meta name="color-scheme" content="light">
<meta name="supported-color-schemes" content="light">
<title>Reserve your founding practice spot on QuoteMySmile</title>
<!--[if mso]>
<xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml>
<![endif]-->
<style>
  /* Progressive enhancement only — nothing here is load-bearing. */
  @media only screen and (max-width:600px) {{
    .qcol {{ width:100% !important; display:block !important; }}
    .qpad {{ padding-left:22px !important; padding-right:22px !important; }}
    .qh1 {{ font-size:30px !important; }}
  }}
  a {{ color:{TEAL}; }}
</style>
</head>
<body style="margin:0;padding:0;background-color:{MINT_BG};">

<!-- Preheader: first thing shown in the inbox list, hidden in the body -->
<div style="display:none;max-height:0;overflow:hidden;mso-hide:all;font-size:1px;line-height:1px;color:{MINT_BG};">
  Founding practices are claiming their areas before we open to patients. Free to join, $5 per attended booking.
  &#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;
</div>

<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color:{MINT_BG};">
  <tr>
    <td align="center" style="padding:30px 12px 42px 12px;">

      <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="600" style="width:600px;max-width:600px;background-color:#FFFFFF;border:1px solid {LINE};border-radius:16px;">

        <!-- HEADER -->
        <tr>
          <td align="center" class="qpad" style="padding:26px 30px 22px 30px;background-color:#F2F8F5;border-bottom:1px solid {LINE};border-radius:16px 16px 0 0;">
            <img src="{LOGO}" width="44" height="44" alt="QuoteMySmile" style="display:block;margin:0 auto 10px auto;border:0;border-radius:11px;">
            <p style="margin:0;font-family:{SERIF};font-size:20px;letter-spacing:2px;text-transform:uppercase;color:{TEAL_DK};">QUOTE<span style="font-family:{SERIF};font-style:italic;text-transform:none;letter-spacing:0;color:{TEAL};">my</span>SMILE</p>
            <p style="margin:7px 0 0 0;font-family:{SANS};font-size:10px;letter-spacing:2px;text-transform:uppercase;color:{MUTED};">The live dental quote marketplace</p>
          </td>
        </tr>

        <!-- HERO -->
        <tr>
          <td align="center" class="qpad" style="padding:40px 34px 34px 34px;background-color:#FFFFFF;">
            <p style="margin:0 0 12px 0;font-family:{SANS};font-size:11px;font-weight:bold;letter-spacing:2px;text-transform:uppercase;color:{TEAL};">For dentists &middot; Founding practices</p>
            <h1 class="qh1" style="margin:0 0 14px 0;font-family:{SERIF};font-size:34px;line-height:1.15;font-weight:normal;color:{INK};">Be the practice patients see first.</h1>
            <p style="margin:0;font-family:{SANS};font-size:15px;line-height:1.65;color:{BODY};">QuoteMySmile is a live quote marketplace where patients ask for a treatment quote and choose a practice to book with. Reserve a founding spot and you&rsquo;ll be first to get the app when it launches, with your place held for your area.</p>
          </td>
        </tr>

        <!-- FOMO BAND -->
        <tr>
          <td align="center" class="qpad" style="padding:34px 34px 34px 34px;background-color:{TEAL_DK};">
            <p style="margin:0 0 10px 0;font-family:{SANS};font-size:11px;font-weight:bold;letter-spacing:2px;text-transform:uppercase;color:{MINT};">Don&rsquo;t miss out</p>
            <p style="margin:0 0 6px 0;font-family:{SERIF};font-size:52px;line-height:1;color:#FFFFFF;">100s</p>
            <p style="margin:0 0 14px 0;font-family:{SERIF};font-size:24px;line-height:1.25;color:#FFFFFF;">of other dentists are already on QuoteMySmile.</p>
            <p style="margin:0;font-family:{SANS};font-size:14px;line-height:1.65;color:#D8E9E2;">They&rsquo;re claiming their areas before we open to patients. Founding places per area are limited, and once yours fills, new practices wait behind the ones already in.</p>
          </td>
        </tr>

        <!-- HOW IT WORKS -->
        <tr>
          <td class="qpad" style="padding:38px 34px 14px 34px;background-color:#FFFFFF;">
            <p align="center" style="margin:0 0 8px 0;font-family:{SANS};font-size:11px;font-weight:bold;letter-spacing:2px;text-transform:uppercase;color:{TEAL};">How it works</p>
            <p align="center" style="margin:0 0 26px 0;font-family:{SERIF};font-size:25px;line-height:1.25;color:{INK};">Three steps, no lead fees.</p>
{step("1", "A patient requests a quote", "Treatment, photos and their area come through to your dashboard. Real patients, actively seeking care near you.")}
{step("2", "You send a price", "Quote only the cases that suit your books. You are never obligated to quote, and there is nothing to pay to be seen.")}
{step("3", "They book, you pay $5", STEP_3)}
          </td>
        </tr>

        <!-- VALUE -->
        <tr>
          <td class="qpad" style="padding:6px 34px 0 34px;background-color:#FFFFFF;">
            <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color:{MINT_BG};border:1px solid {LINE};border-radius:12px;">
              <tr><td style="padding:20px 22px 12px 22px;">
                <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
{bullet("<strong>Real patients near you</strong>, actively seeking treatment, not cold leads.")}
{bullet("<strong>You choose what to quote.</strong> Quote the cases you want, ignore the rest.")}
{bullet("<strong>Flat $5 per attended booking.</strong> No pay-per-lead, no monthly fee.")}
{bullet("<strong>Founding practices get in first</strong>, before patients start requesting quotes in your area.")}
                </table>
              </td></tr>
            </table>
          </td>
        </tr>

        <!-- CTA -->
        <tr>
          <td align="center" class="qpad" style="padding:34px 34px 38px 34px;background-color:#FFFFFF;">
            <p style="margin:0 0 8px 0;font-family:{SERIF};font-size:24px;line-height:1.3;color:{INK};">Claim your area before it fills.</p>
            <p style="margin:0 0 22px 0;font-family:{SANS};font-size:14px;line-height:1.6;color:{BODY};">Takes a few minutes. No cost to join, and you only ever pay when a patient attends.</p>

            <!--[if mso]>
            <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="{CTA_URL}" style="height:52px;v-text-anchor:middle;width:290px;" arcsize="50%" stroke="f" fillcolor="{TEAL}">
              <w:anchorlock/>
              <center style="color:#ffffff;font-family:{SANS};font-size:15px;font-weight:bold;">Reserve your founding spot</center>
            </v:roundrect>
            <![endif]-->
            <!--[if !mso]><!-- -->
            <a href="{CTA_URL}" style="display:inline-block;padding:17px 34px;background-color:{TEAL};color:#FFFFFF;font-family:{SANS};font-size:15px;font-weight:bold;text-decoration:none;border-radius:26px;">Reserve your founding spot &rarr;</a>
            <!--<![endif]-->

            <p style="margin:20px 0 0 0;font-family:{SANS};font-size:12px;line-height:1.6;color:{MUTED};">Questions first? Just reply to this email &mdash; it reaches a real person at <a href="mailto:clinics@quotemysmile.com.au" style="color:{TEAL};">clinics@quotemysmile.com.au</a>.</p>
          </td>
        </tr>

        <!-- FOOTER -->
        <tr>
          <td class="qpad" style="padding:24px 34px 30px 34px;background-color:#F2F8F5;border-top:1px solid {LINE};border-radius:0 0 16px 16px;">
            <p style="margin:0 0 14px 0;font-family:{SANS};font-size:13px;line-height:1.6;color:{INK};">Warm regards,<br><strong>The QuoteMySmile team</strong><br><a href="https://quotemysmile.com.au" style="color:{TEAL};">quotemysmile.com.au</a></p>
            <p style="margin:0;padding-top:12px;border-top:1px solid {LINE};font-family:{SANS};font-size:11px;line-height:1.7;color:#9AA8A2;">
              You received this because your practice is publicly listed as providing dental services in Australia, so we thought this founding invitation would be relevant to your business. This is a one-off invitation, not a newsletter.<br><br>
              QuoteMySmile is a service of LORDLY PTY LTD &middot; ABN 19 697 848 132<br>Melbourne, Victoria, Australia<br>
              <a href="{{{{unsubscribe_url}}}}" style="color:#9AA8A2;">Unsubscribe</a> &middot; or simply reply with &ldquo;unsubscribe&rdquo; and we&rsquo;ll remove you.
            </p>
          </td>
        </tr>

      </table>

    </td>
  </tr>
</table>
</body>
</html>
"""

OUT.write_text(HTML, "utf-8")
print(f"wrote {OUT.name}  {len(HTML) // 1024} KB")
if len(HTML) > 102_400:
    print("WARNING: over Gmail's 102KB clip threshold")
