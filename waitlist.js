/* QuoteMySmile — waitlist / founding-practice reservation form handler.
 * Static-site friendly. No framework, no build step.
 *
 * Submissions POST to /api/reserve — our own Cloudflare Pages Function, which
 * stores the reservation in KV and emails a notification. See
 * functions/api/reserve.js for the environment variables it needs.
 *
 * The mailto path below is now only a LAST-RESORT fallback for when that call
 * fails outright (offline, endpoint down). It should never be the normal route:
 * it depends on the visitor having a mail client set up and then pressing send
 * themselves, and most simply do not — which loses the reservation silently.
 */
(function () {
  'use strict';

  // Both forms post to our own Cloudflare Pages Function, which stores the
  // reservation and emails a notification. See functions/api/reserve.js for the
  // environment variables it needs. Overridable per-kind if you ever want to
  // route one of them somewhere else.
  var ENDPOINTS = {
    patient: '/api/reserve',
    dentist: '/api/reserve'
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
        ? 'Your founding spot is reserved. We\'ll verify your AHPRA registration before you go live, and email you the moment we open to patients in your area.'
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

      picked.data.kind = kind;
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
