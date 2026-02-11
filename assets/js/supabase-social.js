/**
 * Supabase Clap Backend
 * Replaces Lyket backend while keeping Lyket's UI rendering.
 * Finds [data-lyket-type="clap"] divs and injects Supabase-powered clap buttons
 * that mimic the original Lyket medium template style.
 */

(function () {
  var SUPABASE_URL = 'https://aqtdbzmaxhrwtgdhipnu.supabase.co';
  var SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFxdGRiem1heGhyd3RnZGhpcG51Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA3NTUyMTMsImV4cCI6MjA4NjMzMTIxM30.RxzMXc6cOi1BXiKGDpWZ9xDVa844geggNLLOMQdLpd8';
  var API = SUPABASE_URL + '/rest/v1';
  var AUTH_HEADERS = { 'apikey': SUPABASE_ANON_KEY, 'Authorization': 'Bearer ' + SUPABASE_ANON_KEY };

  function getVisitorId() {
    var id = localStorage.getItem('wx_visitor_id');
    if (!id) {
      id = 'v_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 8);
      localStorage.setItem('wx_visitor_id', id);
    }
    return id;
  }

  // Lyket official clap hand SVG (from @lyket/widget)
  var CLAP_SVG = '<svg viewBox="0 0 29 29" width="22" height="22" aria-label="clap" fill="currentColor"><path d="M13.74 1l.76 2.97.76-2.97zM18.63 2.22l-1.43-.47-.4 3.03zM11.79 1.75l-1.43.47 1.84 2.56zM24.47 14.3L21.45 9c-.29-.43-.69-.7-1.12-.78a1.16 1.16 0 0 0-.91.22c-.3.23-.48.52-.54.84l.05.07 2.85 5c1.95 3.56 1.32 6.97-1.85 10.14a8.46 8.46 0 0 1-.55.5 5.75 5.75 0 0 0 3.36-1.76c3.26-3.27 3.04-6.75 1.73-8.91M14.58 10.89c-.16-.83.1-1.57.7-2.15l-2.5-2.49c-.5-.5-1.38-.5-1.88 0-.18.18-.27.4-.33.63l4.01 4z"/><path d="M17.81 10.04a1.37 1.37 0 0 0-.88-.6.81.81 0 0 0-.64.15c-.18.13-.71.55-.24 1.56l1.43 3.03a.54.54 0 1 1-.87.61L9.2 7.38a.99.99 0 1 0-1.4 1.4l4.4 4.4a.54.54 0 1 1-.76.76l-4.4-4.4L5.8 8.3a.99.99 0 0 0-1.4 0 .98.98 0 0 0 0 1.39l1.25 1.24 4.4 4.4a.54.54 0 0 1 0 .76.54.54 0 0 1-.76 0l-4.4-4.4a1 1 0 0 0-1.4 0 .98.98 0 0 0 0 1.4l1.86 1.85 2.76 2.77a.54.54 0 0 1-.76.76L4.58 15.7a.98.98 0 0 0-1.4 0 .99.99 0 0 0 0 1.4l5.33 5.32c3.37 3.37 6.64 4.98 10.49 1.12 2.74-2.74 3.27-5.54 1.62-8.56l-2.8-4.94z"/></svg>';

  function renderClapButton(container, slug) {
    var clapped = localStorage.getItem('clap_' + slug);
    var btn = document.createElement('button');
    btn.className = 'sb-clap-btn' + (clapped ? ' clapped' : '');
    btn.setAttribute('aria-label', 'Clap');
    btn.innerHTML = '<span class="sb-clap-icon">' + CLAP_SVG + '</span>' +
      '<span class="sb-clap-count">-</span>';

    container.innerHTML = '';
    container.appendChild(btn);

    // Load count
    fetch(API + '/claps?post_slug=eq.' + encodeURIComponent(slug) + '&select=id', { headers: AUTH_HEADERS })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        btn.querySelector('.sb-clap-count').textContent = data.length || 0;
      })
      .catch(function () {
        btn.querySelector('.sb-clap-count').textContent = '0';
      });

    // Click
    btn.addEventListener('click', function () {
      if (btn.classList.contains('clapped')) return;
      var visitorId = getVisitorId();
      fetch(API + '/claps', {
        method: 'POST',
        headers: Object.assign({}, AUTH_HEADERS, { 'Content-Type': 'application/json', 'Prefer': 'return=representation' }),
        body: JSON.stringify({ post_slug: slug, visitor_id: visitorId })
      }).then(function (r) {
        if (r.ok || r.status === 201) {
          btn.classList.add('clapped', 'sb-clap-pop');
          btn.querySelector('.sb-clap-icon').innerHTML = CLAP_SVG;
          localStorage.setItem('clap_' + slug, '1');
          var countEl = btn.querySelector('.sb-clap-count');
          countEl.textContent = parseInt(countEl.textContent || '0', 10) + 1;
          setTimeout(function () { btn.classList.remove('sb-clap-pop'); }, 500);
        } else if (r.status === 409) {
          btn.classList.add('clapped');
          btn.querySelector('.sb-clap-icon').innerHTML = CLAP_SVG;
          localStorage.setItem('clap_' + slug, '1');
        }
      }).catch(function () {});
    });
  }

  function init() {
    var lyketEls = document.querySelectorAll('[data-lyket-type="clap"]');
    lyketEls.forEach(function (el) {
      var slug = el.getAttribute('data-lyket-id');
      if (slug) renderClapButton(el, slug);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
