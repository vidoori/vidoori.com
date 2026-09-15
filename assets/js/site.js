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
     5. Leadership strip
   ========================================================================== */

(function () {
  'use strict';

  var DESKTOP = window.matchMedia('(min-width: 60rem)');
  var REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)');

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
     3. Async forms (contact, referral)

     Any <form data-async> is enhanced: inline validation, JSON submit, and a
     status line. Without JavaScript the same form posts normally and the
     Function returns a readable HTML confirmation page.

     Validation mirrors the server's rules in functions/api/contact.js and
     functions/api/referral.js. The server is authoritative; this layer exists
     purely so people get feedback without a round trip.
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
    var min = parseInt(el.getAttribute('data-minlen'), 10);
    if (value.trim() && min > 0 && !VALIDATORS.minlen(value, min)) {
      setError(el, 'Please give us a little more detail (at least ' + min + ' characters).');
      return false;
    }
    if (value.trim() && el.type === 'url' && !/^https?:\/\/[^\s]+\.[^\s]{2,}/i.test(value.trim())) {
      setError(el, 'Enter a full URL starting with http:// or https://.');
      return false;
    }
    setError(el, '');
    return true;
  }

  function initAsyncForm(form) {
    if (!form) return;

    var status = form.querySelector('.form-status');
    var submit = form.querySelector('[type="submit"]');
    var submitLabel = submit ? submit.textContent : 'Send';
    var fallbackError = form.getAttribute('data-error-message') ||
      'Sorry — we could not send this. Please email info@vidoori.com instead.';
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
            say('success', result.data.message || 'Thank you — your submission has been sent.');
            // Remove the form controls from the tab order after success so
            // the confirmation is the end of the interaction.
            if (window.turnstile && typeof window.turnstile.reset === 'function') {
              try { window.turnstile.reset(); } catch (err) { /* non-fatal */ }
            }
          } else {
            say('error', (result.data && result.data.error) || fallbackError);
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
     5. Leadership strip
     ======================================================================== */

  function initYear() {
    var el = document.getElementById('year');
    if (el) el.textContent = String(new Date().getFullYear());
  }

  /* ========================================================================
     5. Leadership strip

     /who-we-are/leadership/ ships five <details> profiles. They work on their
     own: with JS off each bio opens in place, which is what a disclosure is
     for. When JS is available they are upgraded into one strip of buttons
     sharing a single full-width panel, so a bio reads across the row instead
     of down a 200px grid cell.

     The panel is a grid child, re-inserted after the last person in the
     selected person's row. That keeps the caret pointing at the person it
     belongs to whatever the column count — and at the narrowest width, where
     the grid is two columns, the panel still sits directly beneath the pair
     it describes.
     ======================================================================== */

  function initLeadershipStrip() {
    var grid = document.querySelector('.leadership-grid');
    if (!grid) return;

    var items = Array.prototype.slice.call(
      grid.querySelectorAll('details.profile--expandable'));
    if (items.length < 2) return;

    function el(tag, cls, text) {
      var node = document.createElement(tag);
      node.className = cls;
      if (text) node.textContent = text;
      return node;
    }

    var panel = document.createElement('div');
    panel.className = 'leadership-panel';
    panel.id = 'leadership-panel';
    panel.hidden = true;

    var people = items.map(function (item, i) {
      var avatar = item.querySelector('.profile__avatar');
      var nameEl = item.querySelector('.profile__name');
      var roleEl = item.querySelector('.profile__role');
      var bio = item.querySelector('.profile__bio');
      var link = item.querySelector('.profile__link');
      var name = nameEl ? nameEl.textContent : '';
      var role = roleEl ? roleEl.textContent : '';

      // The trigger. A heading may live inside <summary>, but not inside a
      // <button>, so the name is rebuilt as a span here and the real heading
      // moves into the panel, where the biography it titles actually is.
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'profile-tab';
      btn.id = 'profile-tab-' + i;
      btn.setAttribute('aria-expanded', 'false');
      btn.setAttribute('aria-controls', 'leadership-panel');
      if (avatar) btn.appendChild(avatar.cloneNode(true));
      btn.appendChild(el('span', 'profile__name', name));
      btn.appendChild(el('span', 'profile__role', role));
      btn.appendChild(el('span', 'profile__toggle', 'Read bio'));

      var body = el('div', 'leadership-panel__person');
      body.hidden = true;
      body.appendChild(el('h3', 'profile__name', name));
      body.appendChild(el('p', 'profile__role', role));
      if (bio) body.appendChild(bio);
      if (link) body.appendChild(link);
      panel.appendChild(body);

      return { btn: btn, body: body };
    });

    items.forEach(function (item, i) { grid.replaceChild(people[i].btn, item); });
    grid.classList.add('leadership-grid--enhanced');

    var openIndex = -1;

    function columnCount() {
      var cols = window.getComputedStyle(grid).gridTemplateColumns;
      return cols ? cols.split(' ').filter(Boolean).length : 1;
    }

    // Put the panel immediately after the row holding person i.
    function placePanel(i) {
      var cols = columnCount();
      var next = (Math.floor(i / cols) + 1) * cols;
      grid.insertBefore(panel, people[next] ? people[next].btn : null);
    }

    // Point the caret at the selected avatar, clamped clear of the corners.
    function placeCaret(i) {
      var b = people[i].btn.getBoundingClientRect();
      var p = panel.getBoundingClientRect();
      if (!p.width) return;
      var edge = 28;
      var x = b.left + b.width / 2 - p.left;
      panel.style.setProperty(
        '--caret-x', Math.max(edge, Math.min(p.width - edge, x)) + 'px');
    }

    // Only scroll when the panel actually landed out of sight — an
    // unconditional scroll is jarring on a wide screen where it never moved.
    function nudgeIntoView() {
      var r = panel.getBoundingClientRect();
      var h = window.innerHeight || document.documentElement.clientHeight;
      if (r.top >= 0 && r.bottom <= h) return;
      panel.scrollIntoView({
        block: 'nearest',
        behavior: REDUCED_MOTION.matches ? 'auto' : 'smooth'
      });
    }

    function setState(i) {
      people.forEach(function (person, n) {
        var on = n === i;
        person.btn.setAttribute('aria-expanded', on ? 'true' : 'false');
        person.btn.querySelector('.profile__toggle').textContent =
          on ? 'Close bio' : 'Read bio';
        person.body.hidden = !on;
      });
    }

    function show(i) {
      openIndex = i;
      setState(i);
      panel.hidden = false;
      placePanel(i);
      placeCaret(i);
      nudgeIntoView();
    }

    function hide() {
      openIndex = -1;
      setState(-1);
      panel.hidden = true;
    }

    grid.addEventListener('click', function (e) {
      var btn = e.target.closest('.profile-tab');
      if (!btn) return;
      var i = -1;
      people.forEach(function (person, n) { if (person.btn === btn) i = n; });
      if (i < 0) return;
      if (i === openIndex) { hide(); } else { show(i); }
    });

    // Crossing a breakpoint changes the column count, which changes which row
    // the panel belongs to — so it is re-placed, not merely re-measured.
    var queued = false;
    window.addEventListener('resize', function () {
      if (openIndex < 0 || queued) return;
      queued = true;
      window.requestAnimationFrame(function () {
        queued = false;
        if (openIndex < 0) return;
        placePanel(openIndex);
        placeCaret(openIndex);
      });
    });
  }

  /* ======================================================================== */

  function init() {
    initNav();
    initSubmenus();
    Array.prototype.forEach.call(
      document.querySelectorAll('form[data-async]'), initAsyncForm);
    initYear();
    initLeadershipStrip();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
