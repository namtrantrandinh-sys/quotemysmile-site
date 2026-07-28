/* QuoteMySmile — waitlist / founding-practice reservation form handler.
 * Static-site friendly. No framework, no build step.
 *
 * ── HOW TO CAPTURE SUBMISSIONS ───────────────────────────────────────────
 * Until you set an endpoint below, every form falls back to opening the
 * visitor's email app pre-addressed to us (works everywhere, zero setup).
 *
 * To capture to a database + get an email per signup (recommended, ~2 min):
 *   1. Create a free form at https://formspree.io  (one for patients, one for
 *      dentists), or use any endpoint that accepts a JSON/form POST.
 *   2. Paste each endpoint URL into ENDPOINTS below.
 * That's the only change needed — the forms start posting immediately.
 *
 * Prefer your own Supabase instead? See outreach/WAITLIST-SETUP.md for the
 * table + RLS SQL and how to point ENDPOINTS at the REST insert URL.
 * ─────────────────────────────────────────────────────────────────────────
 */
(function () {
  'use strict';

  var ENDPOINTS = {
    patient: '',   // e.g. 'https://formspree.io/f/xxxxxxxx'
    dentist: ''    // e.g. 'https://formspree.io/f/yyyyyyyy'
  };

  var FALLBACK_EMAIL = {
    patient: 'hello@quotemysmile.com.au',
    dentist: 'clinics@quotemysmile.com.au'
  };

  var SUBJECT = {
    patient: 'QuoteMySmile waitlist — patient',
    dentist: 'QuoteMySmile founding-practice reservation'
  };

  function labelFor(input) {
    var f = input.closest('.field');
    var l = f && f.querySelector('label');
    var t = (l ? l.textContent : input.name) || input.name;
    return t.replace(/\s*\(optional\)\s*/i, '').replace(/[:\s]+$/, '').trim();
  }

  function collect(form) {
    var data = {};
    var pretty = [];
    var inputs = form.querySelectorAll('input, select, textarea');
    for (var i = 0; i < inputs.length; i++) {
      var el = inputs[i];
      if (!el.name || el.type === 'submit') continue;
      if (el.classList.contains('hp')) { data[el.name] = el.value; continue; } // honeypot
      var val = (el.value || '').trim();
      data[el.name] = val;
      if (val) pretty.push(labelFor(el) + ': ' + val);
    }
    return { data: data, pretty: pretty };
  }

  function mailtoFallback(kind, pretty) {
    var body =
      'Hi QuoteMySmile team,\n\n' +
      (kind === 'dentist'
        ? 'I\'d like to reserve a founding-practice spot.\n\n'
        : 'I\'d like to join the patient waitlist.\n\n') +
      pretty.join('\n') +
      '\n\n(Sent from quotemysmile.com.au)';
    return 'mailto:' + FALLBACK_EMAIL[kind] +
      '?subject=' + encodeURIComponent(SUBJECT[kind]) +
      '&body=' + encodeURIComponent(body);
  }

  function showDone(form, kind) {
    var msg = form.getAttribute('data-done') ||
      (kind === 'dentist'
        ? 'Your founding spot is reserved. We\'ll verify your AHPRA registration and invite you the moment we open to patients in your area.'
        : 'You\'re on the list. We\'ll email you the moment QuoteMySmile opens near you.');
    var done = document.createElement('div');
    done.className = 'signup-done';
    done.innerHTML = '<div class="tick" aria-hidden="true">✓</div>' +
      '<h3>You\'re in.</h3><p></p>';
    done.querySelector('p').textContent = msg;
    form.replaceWith(done);
  }

  function wire(form) {
    var kind = form.getAttribute('data-qms-form'); // 'patient' | 'dentist'
    var status = form.querySelector('.form-status');
    var btn = form.querySelector('button[type="submit"]');
    var btnText = btn ? btn.textContent : '';

    form.addEventListener('submit', function (e) {
      e.preventDefault();

      // Honeypot: silently succeed for bots without sending anything.
      var hp = form.querySelector('.hp');
      if (hp && hp.value) { showDone(form, kind); return; }

      var picked = collect(form);
      if (status) { status.textContent = ''; status.className = 'form-status'; }

      var endpoint = ENDPOINTS[kind];

      if (!endpoint) {
        // No backend configured yet → open the visitor's mail app, prefilled.
        window.location.href = mailtoFallback(kind, picked.pretty);
        if (status) {
          status.className = 'form-status ok';
          status.textContent = 'Opening your email app — press send to finish. ' +
            'Not opening? Email us at ' + FALLBACK_EMAIL[kind] + '.';
        }
        return;
      }

      if (btn) { btn.disabled = true; btn.textContent = 'Sending…'; }

      fetch(endpoint, {
        method: 'POST',
        headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' },
        body: JSON.stringify(picked.data)
      })
        .then(function (res) {
          if (res.ok) { showDone(form, kind); return; }
          throw new Error('bad status ' + res.status);
        })
        .catch(function () {
          if (btn) { btn.disabled = false; btn.textContent = btnText; }
          // Network/endpoint failure → offer the email fallback so no lead is lost.
          window.location.href = mailtoFallback(kind, picked.pretty);
          if (status) {
            status.className = 'form-status err';
            status.textContent = 'We couldn\'t submit just then, so we\'ve opened your email app instead. ' +
              'Or email ' + FALLBACK_EMAIL[kind] + '.';
          }
        });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var forms = document.querySelectorAll('form[data-qms-form]');
    for (var i = 0; i < forms.length; i++) wire(forms[i]);
  });
})();
