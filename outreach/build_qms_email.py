#!/usr/bin/env python3
"""Build the QuoteMySmile founding-dentist onboarding email:
mint + teal palette, real logo (smile mark), and the founding-dentists line."""
import base64, pathlib
HERE = pathlib.Path(__file__).parent
LOGO = "data:image/png;base64," + base64.b64encode((HERE / "qms-logo.png").read_bytes()).decode()

html = f'''<div class="qwrap">
<style>
  .qwrap * {{ box-sizing:border-box; }}
  .qwrap {{
    --mint:#A9CFC0; --mint-soft:#DCEEE6; --mint-bg:#E6F1EC; --teal:#2F6F66; --teal-dk:#1F4F47;
    --teal-mid:#4A8C82; --card:#FFFFFF; --ink:#1E3A34; --body:#4A5551; --muted:#7f8b86; --line:#d8e7e0;
    --serif:"Cormorant Garamond",Georgia,'Times New Roman',serif;
    --script:"Snell Roundhand","Brush Script MT",cursive;
    --sans:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
    background:var(--mint-bg); color:var(--ink);
    -webkit-font-smoothing:antialiased; text-rendering:optimizeLegibility; padding:34px 16px 46px;
  }}
  .qdoc {{ max-width:600px; margin:0 auto; background:var(--card); border-radius:22px; overflow:hidden;
    box-shadow:0 30px 80px rgba(31,79,71,.18), 0 4px 14px rgba(31,79,71,.08); border:1px solid var(--line); }}

  /* header + logo */
  .qhead {{ text-align:center; padding:26px 30px 22px; background:linear-gradient(180deg,#F2F8F5,#fff);
    border-bottom:1px solid var(--line); }}
  .qhead img {{ width:46px; height:46px; display:block; margin:0 auto 12px; border-radius:12px;
    box-shadow:0 8px 20px rgba(31,79,71,.22); }}
  .qmark {{ font:600 22px/1 var(--serif); letter-spacing:.14em; text-transform:uppercase; color:var(--teal-dk); }}
  .qmark em {{ font:400 26px/1 var(--script); font-style:normal; text-transform:none; letter-spacing:0;
    color:var(--teal); margin:0 1px; }}
  .qtag {{ margin-top:8px; font:400 11px/1.4 var(--sans); letter-spacing:.2em; text-transform:uppercase; color:var(--muted); }}

  .eyebrow {{ font:600 11px/1.4 var(--sans); letter-spacing:.2em; text-transform:uppercase; color:var(--teal); }}

  /* hero */
  .qhero {{ padding:44px 34px 40px; text-align:center;
    background:radial-gradient(120% 95% at 50% 0%, var(--mint-soft) 0%, #F3F9F6 55%, #fff 100%); }}
  .qhero h1 {{ font:500 38px/1.12 var(--serif); letter-spacing:0; color:var(--ink); margin:14px auto 14px; max-width:15ch; }}
  .qhero h1 em {{ font-family:var(--script); font-style:normal; color:var(--teal); font-weight:400; font-size:1.05em; }}
  .qhero p {{ font:400 15.5px/1.66 var(--sans); color:var(--body); margin:0 auto; max-width:46ch; }}
  .qhero .who {{ color:var(--ink); font-weight:600; }}

  /* why-now band (teal) with the founding-dentists line */
  .qwhy {{ padding:38px 34px; background:linear-gradient(160deg,var(--teal),var(--teal-dk)); color:#eaf5f0; text-align:center; }}
  .qwhy .eyebrow {{ color:var(--mint); }}
  .qwhy h2 {{ font:500 28px/1.2 var(--serif); color:#fff; margin:12px auto 12px; max-width:20ch; }}
  .qwhy h2 .count {{ display:inline-block; font-weight:800; font-size:1.5em; line-height:1;
    color:#F3FBF8; letter-spacing:.5px; text-shadow:0 0 22px rgba(169,207,192,.75), 0 1px 0 rgba(0,0,0,.14); }}
  @supports ((-webkit-background-clip:text) or (background-clip:text)) {{
    .qwhy h2 .count {{ background:linear-gradient(100deg,#DFF3EB 18%,#FFFFFF 42%,#A9CFC0 58%,#DFF3EB 82%);
      background-size:220% auto; -webkit-background-clip:text; background-clip:text;
      -webkit-text-fill-color:transparent; text-shadow:none;
      filter:drop-shadow(0 0 15px rgba(169,207,192,.6)); animation:qshine 3.4s linear infinite; }}
  }}
  @keyframes qshine {{ to {{ background-position:220% center; }} }}
  .qwhy p {{ font:400 14.5px/1.66 var(--sans); color:rgba(255,255,255,.85); margin:0 auto; max-width:44ch; }}
  .qwhy .pill {{ display:inline-block; margin-top:20px; padding:9px 18px; border-radius:999px;
    background:rgba(169,207,192,.2); border:1px solid rgba(169,207,192,.5);
    font:600 12.5px/1 var(--sans); letter-spacing:.02em; color:#eaf5f0; }}

  /* how it works */
  .qhow {{ padding:44px 34px 30px; }}
  .qhow .eyebrow {{ text-align:center; display:block; }}
  .qhow h2 {{ font:500 27px/1.2 var(--serif); text-align:center; color:var(--ink); margin:12px auto 30px; }}
  .qstep {{ display:flex; gap:16px; align-items:flex-start; padding:0 0 24px; }}
  .qstep:last-child {{ padding-bottom:0; }}
  .qic {{ flex:0 0 auto; width:46px; height:46px; border-radius:50%;
    background:linear-gradient(160deg,#EAF5F0,#D5EAE2); border:1px solid var(--mint);
    display:flex; align-items:center; justify-content:center; }}
  .qic svg {{ width:22px; height:22px; stroke:var(--teal-dk); fill:none; stroke-width:1.6; }}
  .qstep h3 {{ font:600 16px/1.3 var(--sans); color:var(--ink); margin:6px 0 4px; }}
  .qstep p {{ font:400 14px/1.6 var(--sans); color:var(--body); margin:0; }}
  .qstep .fee {{ color:var(--teal-dk); font-weight:700; }}

  /* value bullets */
  .qval {{ margin:8px 34px 0; padding:24px 24px; background:var(--mint-bg); border:1px solid var(--line); border-radius:16px; }}
  .qval .row {{ display:flex; gap:11px; align-items:flex-start; padding:0 0 12px; }}
  .qval .row:last-child {{ padding-bottom:0; }}
  .qval .tick {{ flex:0 0 auto; width:20px; height:20px; border-radius:50%; background:var(--teal); position:relative; margin-top:1px; }}
  .qval .tick::after {{ content:""; position:absolute; left:7px; top:4px; width:4px; height:9px; border:solid #fff; border-width:0 2px 2px 0; transform:rotate(43deg); }}
  .qval .row div {{ font:400 14px/1.55 var(--sans); color:var(--body); }}
  .qval .row b {{ color:var(--ink); font-weight:600; }}

  /* CTA */
  .qcta {{ padding:38px 34px 40px; text-align:center; }}
  .qcta h2 {{ font:500 26px/1.24 var(--serif); color:var(--ink); margin:0 auto 8px; max-width:20ch; }}
  .qcta p {{ font:400 14px/1.6 var(--sans); color:var(--body); margin:0 auto 22px; max-width:40ch; }}
  .qbtn {{ display:inline-block; text-decoration:none; font:600 15px/1 var(--sans); color:#fff;
    background:var(--teal); background:linear-gradient(160deg,var(--teal-mid),var(--teal-dk));
    padding:16px 36px; border-radius:999px; box-shadow:0 16px 34px rgba(31,79,71,.34); }}
  .qcta .rea {{ font:400 12.5px/1.6 var(--sans); color:var(--muted); margin:20px auto 0; max-width:46ch; }}
  .qcta .rea a {{ color:var(--teal); text-decoration:none; }}

  /* footer */
  .qfoot {{ padding:26px 34px 34px; border-top:1px solid var(--line); background:#F2F8F5; }}
  .qsign {{ font:400 13.5px/1.6 var(--sans); color:var(--ink); }}
  .qsign b {{ font-weight:600; }}
  .qsign a {{ color:var(--teal); text-decoration:none; }}
  .qfine {{ margin-top:16px; padding-top:14px; border-top:1px solid var(--line);
    font:400 11px/1.7 var(--sans); color:#9aa8a2; }}
  .qfine a {{ color:#9aa8a2; }}

  @media (max-width:520px){{ .qhero h1{{font-size:31px;}} }}
</style>

  <div class="qdoc">

    <div class="qhead">
      <img src="{LOGO}" alt="QuoteMySmile" width="46" height="46">
      <div class="qmark">Quote<em>my</em>Smile</div>
      <div class="qtag">The live dental quote marketplace</div>
    </div>

    <!-- HERO -->
    <div class="qhero">
      <div class="eyebrow">For dentists &middot; Founding practices</div>
      <h1>Be the practice patients <em>see first.</em></h1>
      <p><span class="who">QuoteMySmile is a live quote marketplace</span> where patients ask for a treatment quote and choose a practice to book with. We&rsquo;re onboarding practices now, before we open it to patients across Australia. Join early, and you&rsquo;re quoting from day one.</p>
    </div>

    <!-- WHY NOW (FOMO: don't miss out, 100s of other dentists) -->
    <div class="qwhy">
      <div class="eyebrow">Don&rsquo;t miss out</div>
      <h2>Join <span class="count">100s</span> of other dentists already on QuoteMySmile.</h2>
      <p>They&rsquo;re claiming their areas before we open to patients across Australia. Once the quote requests start, patients book the practices already here, and founding spots in each area are limited. Miss the window and you&rsquo;re waiting behind them.</p>
      <span class="pill">Founding practices &middot; limited spots per area</span>
    </div>

    <!-- HOW IT WORKS -->
    <div class="qhow">
      <span class="eyebrow">How it works</span>
      <h2>Three steps, no lead fees.</h2>

      <div class="qstep">
        <span class="qic"><svg viewBox="0 0 24 24"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg></span>
        <div><h3>A patient requests a quote</h3><p>Treatment, photos and their area come through to your dashboard. Real patients, actively seeking care near you.</p></div>
      </div>
      <div class="qstep">
        <span class="qic"><svg viewBox="0 0 24 24"><path d="M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg></span>
        <div><h3>You send a price</h3><p>Quote only the cases that suit your books. You are never obligated to quote, and there is nothing to pay to be seen.</p></div>
      </div>
      <div class="qstep">
        <span class="qic"><svg viewBox="0 0 24 24"><path d="M8 2v4M16 2v4M3 9h18M5 4h14a2 2 0 0 1 2 2v13a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z"/><path d="m9 15 2 2 4-4"/></svg></span>
        <div><h3>They book, you pay $5</h3><p>Patients book with a refundable deposit, so the ones who reach you are serious. You pay a <span class="fee">flat $5 per attended booking</span>. No lead fees, no subscription.</p></div>
      </div>
    </div>

    <!-- VALUE -->
    <div class="qval">
      <div class="row"><span class="tick"></span><div><b>Real patients near you</b>, actively seeking treatment, not cold leads.</div></div>
      <div class="row"><span class="tick"></span><div><b>You choose what to quote.</b> Quote the cases you want, ignore the rest.</div></div>
      <div class="row"><span class="tick"></span><div><b>Flat $5 per attended booking.</b> No pay-per-lead, no monthly fee, nothing to pay to quote.</div></div>
      <div class="row"><span class="tick"></span><div><b>Founding practices get in first</b>, before patients start requesting quotes in your area.</div></div>
    </div>

    <!-- CTA -->
    <div class="qcta">
      <h2>Claim your area before it fills.</h2>
      <p>It takes a few minutes to apply. Founding spots per area are limited. No cost to join, and you only ever pay when a patient attends.</p>
      <a class="qbtn" href="https://quotemysmile.com.au/for-dentists">Reserve your founding spot &rarr;</a>
      <p class="rea">Questions first? Reply to this email, it reaches a real person on our team at <a href="mailto:clinics@quotemysmile.com.au">clinics@quotemysmile.com.au</a>.</p>
    </div>

    <!-- FOOTER -->
    <div class="qfoot">
      <div class="qsign">Warm regards,<br><b>The QuoteMySmile team</b><br><a href="https://quotemysmile.com.au">quotemysmile.com.au</a></div>
      <div class="qfine">
        You received this because your practice is publicly listed as providing dental services in Australia, so we thought this founding invitation may be relevant. This is a one-off invite, not a newsletter.<br><br>
        QuoteMySmile Pty Ltd, Australia<br>
        <a href="{{{{unsubscribe_url}}}}">Unsubscribe</a> &middot; or reply with &ldquo;unsubscribe&rdquo;.
      </div>
    </div>

  </div>
</div>'''

out = HERE / "dentist-onboarding-email.html"
out.write_text(html, encoding="utf-8")
print("wrote", out, f"{out.stat().st_size/1024:.0f} KB")
