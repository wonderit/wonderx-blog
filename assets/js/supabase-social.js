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

  // Clap hand SVG (matches Lyket's clap icon style)
  var CLAP_SVG = '<svg viewBox="0 0 24 24" width="22" height="22"><path d="M8.005 6.435l-.768-2.869a1.5 1.5 0 0 1 2.898-.776l1.345 5.023M11.48 7.813l-.939-3.507a1.5 1.5 0 0 1 2.898-.776l.94 3.507M14.379 8.59l-.47-1.753a1.5 1.5 0 0 1 2.899-.776l.47 1.753M7.022 14.615L5.237 7.953a1.5 1.5 0 0 1 2.898-.776l1.785 6.662M16.778 10.36a1.5 1.5 0 0 1 1.061 1.837l-1.785 6.662a5 5 0 0 1-6.124 3.537l-2.07-.555a5 5 0 0 1-3.537-6.124" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  var CLAP_SVG_FILLED = '<svg viewBox="0 0 24 24" width="22" height="22"><path d="M8.005 6.435l-.768-2.869a1.5 1.5 0 0 1 2.898-.776l1.345 5.023M11.48 7.813l-.939-3.507a1.5 1.5 0 0 1 2.898-.776l.94 3.507M14.379 8.59l-.47-1.753a1.5 1.5 0 0 1 2.899-.776l.47 1.753M7.022 14.615L5.237 7.953a1.5 1.5 0 0 1 2.898-.776l1.785 6.662M16.778 10.36a1.5 1.5 0 0 1 1.061 1.837l-1.785 6.662a5 5 0 0 1-6.124 3.537l-2.07-.555a5 5 0 0 1-3.537-6.124" fill="currentColor" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>';

  function renderClapButton(container, slug) {
    var clapped = localStorage.getItem('clap_' + slug);
    var btn = document.createElement('button');
    btn.className = 'sb-clap-btn' + (clapped ? ' clapped' : '');
    btn.setAttribute('aria-label', 'Clap');
    btn.innerHTML = '<span class="sb-clap-icon">' + (clapped ? CLAP_SVG_FILLED : CLAP_SVG) + '</span>' +
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
          btn.querySelector('.sb-clap-icon').innerHTML = CLAP_SVG_FILLED;
          localStorage.setItem('clap_' + slug, '1');
          var countEl = btn.querySelector('.sb-clap-count');
          countEl.textContent = parseInt(countEl.textContent || '0', 10) + 1;
          setTimeout(function () { btn.classList.remove('sb-clap-pop'); }, 500);
        } else if (r.status === 409) {
          btn.classList.add('clapped');
          btn.querySelector('.sb-clap-icon').innerHTML = CLAP_SVG_FILLED;
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
