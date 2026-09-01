/* ==========================================================================
   Vidoori — site.js
   Plain ES2019. No modules, no bundler, no dependencies. Loaded with `defer`.

   Everything here is progressive enhancement: with JS disabled the nav
   renders as a plain expanded link list and the contact form posts natively
   to /api/contact, which returns a readable HTML fallback page.

   Sections
     1. Mobile nav
     2. Desktop submenu keyboard support
     3. Contact form (validation + async submit + Turnstile)
     4. Footer year
   ========================================================================== */

(function () {
  'use strict';

  var DESKTOP = window.matchMedia('(min-width: 60rem)');

  /* ========================================================================
     1. Mobile nav
     ======================================================================== */

  function initNav() {
    var toggle = document.querySelector('.nav-toggle');
    var nav = document.getElementById('site-nav');
    if (!toggle || !nav) return;

    function setOpen(open) {
      toggle.setAttribute('aria-expanded', String(open));
      nav.classList.toggle('is-open', open);
      // Lock body scroll only while the mobile panel covers the viewport.
      document.body.style.overflow = open && !DESKTOP.matches ? 'hidden' : '';
    }

    toggle.addEventListener('click', function () {
      setOpen(toggle.getAttribute('aria-expanded') !== 'true');
    });

    // Close on Escape, returning focus to the toggle.
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
        setOpen(false);
        toggle.focus();
      }
    });

    // Close when a link inside the panel is followed.
    nav.addEventListener('click', function (e) {
      if (e.target.closest('a') && !DESKTOP.matches) setOpen(false);
    });

    // Close when tapping outside the header.
    document.addEventListener('click', function (e) {
      if (
        toggle.getAttribute('aria-expanded') === 'true' &&
        !e.target.closest('.site-header')
      ) {
        setOpen(false);
      }
    });

    // Reset state when crossing the breakpoint so the desktop bar is never
    // left in a mobile "open" state (and vice versa).
    var onChange = function () { setOpen(false); };
    if (DESKTOP.addEventListener) DESKTOP.addEventListener('change', onChange);
    else DESKTOP.addListener(onChange);
  }

  /* ========================================================================
     2. Submenus

     Markup is <button class="nav__disclosure" aria-expanded> + <ul>.
     - Mobile: the button expands/collapses the list (CSS keys off aria-expanded).
     - Desktop: CSS opens the list on hover/focus-within; the button still
       works for keyboard and touch users, so we keep the same handler.
     ======================================================================== */

  function initSubmenus() {
    var buttons = document.querySelectorAll('.nav__disclosure');

    Array.prototype.forEach.call(buttons, function (btn) {
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        var open = btn.getAttribute('aria-expanded') === 'true';

        // On desktop only one submenu should be open at a time.
        if (DESKTOP.matches) {
          Array.prototype.forEach.call(buttons, function (other) {
            if (other !== btn) other.setAttribute('aria-expanded', 'false');
          });
        }
        btn.setAttribute('aria-expanded', String(!open));
      });

      // Escape closes just this submenu.
      var item = btn.closest('.nav__item');
      if (item) {
        item.addEventListener('keydown', function (e) {
          if (e.key === 'Escape' && btn.getAttribute('aria-expanded') === 'true') {
            e.stopPropagation();
            btn.setAttribute('aria-expanded', 'false');
            btn.focus();
          }
        });
      }
    });

    // Clicking away closes any open desktop submenu.
    document.addEventListener('click', function (e) {
      if (!DESKTOP.matches) return;
      if (e.target.closest('.nav__item')) return;
      Array.prototype.forEach.call(buttons, function (btn) {
        btn.setAttribute('aria-expanded', 'false');
      });
    });
  }

  /* ========================================================================
     3. Contact form

     Validation mirrors the server's rules in functions/api/contact.js.
     The server is authoritative; this layer exists purely so people get
     feedback without a round trip.
     ======================================================================== */

  var VALIDATORS = {
    required: function (v) { return v.trim().length > 0; },
    email: function (v) { return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v.trim()); },
    minlen: function (v, n) { return v.trim().length >= n; }
  };

  function fieldOf(el) { return el.closest('.field'); }

  function setError(el, message) {
    var field = fieldOf(el);
    if (!field) return;
    var slot = field.querySelector('.field__error');
    field.classList.toggle('is-invalid', Boolean(message));
    el.setAttribute('aria-invalid', message ? 'true' : 'false');
    if (slot) slot.textContent = message || '';
  }

  function validateField(el) {
    var value = el.value || '';
    var label = el.getAttribute('data-label') || 'This field';

    if (el.hasAttribute('required')) {
      if (el.type === 'checkbox' && !el.checked) {
        setError(el, 'Please confirm to continue.');
        return false;
      }
      if (el.type !== 'checkbox' && !VALIDATORS.required(value)) {
        setError(el, label + ' is required.');
        return false;
      }
    }
    if (value.trim() && el.type === 'email' && !VALIDATORS.email(value)) {
      setError(el, 'Enter a valid email address.');
      return false;
    }
    if (value.trim() && el.name === 'message' && !VALIDATORS.minlen(value, 10)) {
      setError(el, 'Please give us a little more detail (at least 10 characters).');
      return false;
    }
    setError(el, '');
    return true;
  }

  function initContactForm() {
    var form = document.getElementById('contact-form');
    if (!form) return;

    var status = document.getElementById('form-status');
    var submit = form.querySelector('[type="submit"]');
    var submitLabel = submit ? submit.textContent : 'Send Message';
    var controls = form.querySelectorAll('.input, .select, .textarea, [type="checkbox"][required]');

    // Timestamp the render. The server rejects submissions faster than a
    // few seconds, which no human can beat but scripted bots routinely do.
    var startedAt = form.querySelector('input[name="started_at"]');
    if (startedAt) startedAt.value = String(Date.now());

    function say(kind, message) {
      if (!status) return;
      status.hidden = false;
      status.className = 'form-status is-' + kind;
      status.textContent = message;
      // Errors get focus so screen readers and keyboard users land on them.
      if (kind === 'error') status.setAttribute('tabindex', '-1'), status.focus();
    }

    // Validate on blur, and clear errors as the user fixes them.
    Array.prototype.forEach.call(controls, function (el) {
      el.addEventListener('blur', function () { validateField(el); });
      el.addEventListener('input', function () {
        if (fieldOf(el) && fieldOf(el).classList.contains('is-invalid')) validateField(el);
      });
      if (el.type === 'checkbox') {
        el.addEventListener('change', function () { validateField(el); });
      }
    });

    form.addEventListener('submit', function (e) {
      e.preventDefault();

      // Validate everything, focus the first problem.
      var firstBad = null;
      Array.prototype.forEach.call(controls, function (el) {
        if (!validateField(el) && !firstBad) firstBad = el;
      });
      if (firstBad) {
        say('error', 'Please correct the highlighted fields and try again.');
        firstBad.focus();
        return;
      }

      // Turnstile renders a hidden input with this name. If the widget is
      // configured but unsolved, stop here with a clear message.
      var hasWidget = form.querySelector('.cf-turnstile');
      var tsField = form.querySelector('[name="cf-turnstile-response"]');
      if (hasWidget && (!tsField || !tsField.value)) {
        say('error', 'Please complete the verification challenge below, then send again.');
        return;
      }

      if (submit) {
        submit.setAttribute('aria-disabled', 'true');
        submit.disabled = true;
        submit.textContent = 'Sending…';
      }
      say('pending', 'Sending your message…');

      var payload = {};
      new FormData(form).forEach(function (value, key) {
        // Checkbox groups would collide; we only have single checkboxes.
        payload[key] = value;
      });

      fetch(form.action, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify(payload)
      })
        .then(function (res) {
          return res.json().then(function (data) {
            return { ok: res.ok, data: data };
          }).catch(function () {
            return { ok: res.ok, data: {} };
          });
        })
        .then(function (result) {
          if (result.ok && result.data.ok) {
            form.reset();
            say(
              'success',
              result.data.message ||
                'Thank you — your message has been sent. We aim to respond within three business days.'
            );
            // Remove the form controls from the tab order after success so
            // the confirmation is the end of the interaction.
            if (window.turnstile && typeof window.turnstile.reset === 'function') {
              try { window.turnstile.reset(); } catch (err) { /* non-fatal */ }
            }
          } else {
            say(
              'error',
              (result.data && result.data.error) ||
                'Sorry — we could not send your message. Please email info@vidoori.com instead.'
            );
          }
        })
        .catch(function () {
          say(
            'error',
            'Network error. Please check your connection, or email info@vidoori.com directly.'
          );
        })
        .then(function () {
          if (submit) {
            submit.removeAttribute('aria-disabled');
            submit.disabled = false;
            submit.textContent = submitLabel;
          }
        });
    });
  }

  /* ========================================================================
     4. Footer year
     ======================================================================== */

  function initYear() {
    var el = document.getElementById('year');
    if (el) el.textContent = String(new Date().getFullYear());
  }

  /* ======================================================================== */

  function init() {
    initNav();
    initSubmenus();
    initContactForm();
    initYear();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
