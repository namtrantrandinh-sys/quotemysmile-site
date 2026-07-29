/* QuoteMySmile — waitlist / founding-practice reservation handler.
 *
 * The site is served by GITHUB PAGES, which is static-only: there is no server
 * we can run, so capture has to go to an external endpoint. It posts to
 * FormSubmit, which needs no account and no API key — the reservation is
 * emailed straight to INBOX below.
 *
 * ONE-TIME STEP: the very first submission triggers a confirmation email to
 * that address. Click the link in it once and every submission after that is
 * delivered automatically. Until it is clicked, submissions are held.
 *
 * To move to a different provider later (Formspree, Basin, your own API), just
 * change ENDPOINT — everything else here is provider-agnostic.
 */
(function () {
  'use strict';

  var INBOX = 'hello@quotemysmile.com.au';
  var ENDPOINT = 'https://formsubmit.co/ajax/' + INBOX;

  function collect(form) {
    var data = {};
    var inputs = form.querySelectorAll('input, select, textarea');
    for (var i = 0; i < inputs.length; i++) {
      var el = inputs[i];
      if (!el.name || el.type === 'submit') continue;
      data[el.name] = (el.value || '').trim();
    }
    return data;
  }

  function showDone(form, kind) {
    var msg = kind === 'dentist'
      ? 'Your founding spot is reserved. We\'ll verify your AHPRA registration before you go live, and email you the moment we open to patients in your area.'
      : 'You\'re on the list. We\'ll email you the moment QuoteMySmile opens near you.';
    var done = document.createElement('div');
    done.className = 'signup-done';
    done.innerHTML = '<div class="tick" aria-hidden="true">&#10003;</div><h3>You\'re in.</h3><p></p>';
    done.querySelector('p').textContent = msg;
    // Hide rather than destroy: if this ever needs to be retried there is still
    // a form to retry into.
    form.hidden = true;
    form.parentNode.insertBefore(done, form);
    done.querySelector('h3').setAttribute('tabindex', '-1');
    done.querySelector('h3').focus();
  }

  function wire(form) {
    var kind = form.getAttribute('data-qms-form'); // 'patient' | 'dentist'
    var status = form.querySelector('.form-status');
    var btn = form.querySelector('button[type="submit"]');
    var label = btn ? btn.textContent : '';

    form.addEventListener('submit', function (e) {
      e.preventDefault();

      // Native validation first, so required fields are caught before we post.
      if (typeof form.checkValidity === 'function' && !form.checkValidity()) {
        form.reportValidity();
        return;
      }

      var data = collect(form);
      if (data._gotcha) { showDone(form, kind); return; }   // bot

      if (status) { status.textContent = ''; status.className = 'form-status'; }
      if (btn) { btn.disabled = true; btn.textContent = 'Reserving…'; }

      data._subject = kind === 'dentist'
        ? 'Founding practice reservation — ' + (data.clinic || data.name || data.email)
        : 'Patient waitlist — ' + (data.suburb || data.email);
      data._template = 'table';
      data.kind = kind;
      data.source = 'quotemysmile.com.au';

      fetch(ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify(data)
      })
        .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
        .then(function () { showDone(form, kind); })
        .catch(function () {
          // Tell them plainly and give them a way through. No mail-client
          // detour — that read as an error and most people abandoned there.
          if (btn) { btn.disabled = false; btn.textContent = label; }
          if (status) {
            status.className = 'form-status err';
            status.innerHTML = 'Something went wrong saving that. Please email us at ' +
              '<a href="mailto:' + INBOX + '">' + INBOX + '</a> and we\'ll reserve your spot manually.';
          }
        });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    var forms = document.querySelectorAll('form[data-qms-form]');
    for (var i = 0; i < forms.length; i++) wire(forms[i]);
  });
})();
