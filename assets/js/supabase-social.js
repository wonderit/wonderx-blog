/**
 * Supabase Social Features: Clap + Comments
 * Uses Supabase anon key (safe for public repos, protected by RLS)
 */

(function () {
  const SUPABASE_URL = 'https://aqtdbzmaxhrwtgdhipnu.supabase.co';
  const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFxdGRiem1heGhyd3RnZGhpcG51Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA3NTUyMTMsImV4cCI6MjA4NjMzMTIxM30.RxzMXc6cOi1BXiKGDpWZ9xDVa844geggNLLOMQdLpd8';
  const API = SUPABASE_URL + '/rest/v1';
  const HEADERS = {
    'apikey': SUPABASE_ANON_KEY,
    'Authorization': 'Bearer ' + SUPABASE_ANON_KEY,
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
  };

  // Generate visitor ID (fingerprint-lite, stored in localStorage)
  function getVisitorId() {
    var id = localStorage.getItem('wx_visitor_id');
    if (!id) {
      id = 'v_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 8);
      localStorage.setItem('wx_visitor_id', id);
    }
    return id;
  }

  // ─── CLAP ───────────────────────────────────────────────

  function initClaps() {
    var clapBtns = document.querySelectorAll('.clap-btn');
    if (!clapBtns.length) return;

    clapBtns.forEach(function (el) {
      var slug = el.dataset.postSlug;
      if (!slug) return;

      var button = el.querySelector('.clap-button');
      var countEl = el.querySelector('.clap-count');

      // Load count
      loadClapCount(slug, countEl);

      // Check if already clapped
      var clapped = localStorage.getItem('clap_' + slug);
      if (clapped) {
        button.classList.add('clapped');
      }

      // Click handler
      button.addEventListener('click', function () {
        if (button.classList.contains('clapped')) return;
        submitClap(slug, button, countEl);
      });
    });
  }

  function loadClapCount(slug, countEl) {
    fetch(API + '/claps?post_slug=eq.' + encodeURIComponent(slug) + '&select=id', {
      headers: { 'apikey': SUPABASE_ANON_KEY, 'Authorization': 'Bearer ' + SUPABASE_ANON_KEY }
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (countEl) countEl.textContent = data.length || 0;
      })
      .catch(function () { /* silent */ });
  }

  function submitClap(slug, button, countEl) {
    var visitorId = getVisitorId();

    fetch(API + '/claps', {
      method: 'POST',
      headers: HEADERS,
      body: JSON.stringify({ post_slug: slug, visitor_id: visitorId })
    })
      .then(function (r) {
        if (r.ok || r.status === 201) {
          button.classList.add('clapped', 'clap-animate');
          localStorage.setItem('clap_' + slug, '1');
          var count = parseInt(countEl.textContent || '0', 10);
          countEl.textContent = count + 1;
          setTimeout(function () { button.classList.remove('clap-animate'); }, 600);
        } else if (r.status === 409) {
          // Already clapped (unique constraint)
          button.classList.add('clapped');
          localStorage.setItem('clap_' + slug, '1');
        }
      })
      .catch(function () { /* silent */ });
  }

  // ─── COMMENTS ───────────────────────────────────────────

  function initComments() {
    var commentsSection = document.getElementById('supabase-comments');
    if (!commentsSection) return;

    var slug = commentsSection.dataset.postSlug;
    if (!slug) return;

    loadComments(slug);

    var form = document.getElementById('comment-form');
    if (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        submitComment(slug);
      });
    }
  }

  function loadComments(slug) {
    var listEl = document.getElementById('comments-list');
    var badgeEl = document.getElementById('comments-count-badge');
    if (!listEl) return;

    fetch(API + '/comments?post_slug=eq.' + encodeURIComponent(slug) + '&order=created_at.asc&select=id,nickname,content,created_at', {
      headers: { 'apikey': SUPABASE_ANON_KEY, 'Authorization': 'Bearer ' + SUPABASE_ANON_KEY }
    })
      .then(function (r) { return r.json(); })
      .then(function (comments) {
        if (badgeEl) {
          badgeEl.textContent = comments.length > 0 ? comments.length : '';
        }

        if (comments.length === 0) {
          listEl.innerHTML = '<p class="no-comments text-muted">' +
            (document.documentElement.lang === 'en' ? 'No comments yet. Be the first!' : '아직 댓글이 없습니다. 첫 댓글을 남겨보세요!') +
            '</p>';
          return;
        }

        var html = '';
        comments.forEach(function (c) {
          var date = new Date(c.created_at);
          var dateStr = date.getFullYear() + '.' +
            String(date.getMonth() + 1).padStart(2, '0') + '.' +
            String(date.getDate()).padStart(2, '0') + ' ' +
            String(date.getHours()).padStart(2, '0') + ':' +
            String(date.getMinutes()).padStart(2, '0');

          html += '<div class="comment-item">' +
            '<div class="comment-header">' +
            '<strong class="comment-author">' + escapeHtml(c.nickname) + '</strong>' +
            '<time class="comment-date">' + dateStr + '</time>' +
            '</div>' +
            '<div class="comment-body">' + escapeHtml(c.content).replace(/\n/g, '<br>') + '</div>' +
            '</div>';
        });

        listEl.innerHTML = html;
      })
      .catch(function () {
        listEl.innerHTML = '<p class="text-muted">Failed to load comments.</p>';
      });
  }

  function submitComment(slug) {
    var nicknameEl = document.getElementById('comment-nickname');
    var contentEl = document.getElementById('comment-content');
    var submitBtn = document.getElementById('comment-submit-btn');
    var hpField = document.querySelector('.hp-field');

    // Honeypot check
    if (hpField && hpField.value) return;

    var nickname = (nicknameEl.value || '').trim();
    var content = (contentEl.value || '').trim();

    if (!nickname || !content) return;
    if (nickname.length > 30 || content.length > 2000) return;

    // Rate limit: 1 comment per 10 seconds
    var lastComment = parseInt(localStorage.getItem('last_comment_ts') || '0', 10);
    if (Date.now() - lastComment < 10000) {
      alert(document.documentElement.lang === 'en' ? 'Please wait a moment before posting again.' : '잠시 후에 다시 시도해주세요.');
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = '...';

    fetch(API + '/comments', {
      method: 'POST',
      headers: HEADERS,
      body: JSON.stringify({ post_slug: slug, nickname: nickname, content: content })
    })
      .then(function (r) {
        if (r.ok || r.status === 201) {
          localStorage.setItem('last_comment_ts', String(Date.now()));
          localStorage.setItem('wx_nickname', nickname);
          contentEl.value = '';
          loadComments(slug);
        } else {
          r.json().then(function(err) {
            console.error('Comment error:', err);
          });
        }
      })
      .catch(function (err) {
        console.error('Comment submit failed:', err);
      })
      .finally(function () {
        submitBtn.disabled = false;
        submitBtn.textContent = document.documentElement.lang === 'en' ? 'Post' : '등록';
      });
  }

  function escapeHtml(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  // ─── INIT ───────────────────────────────────────────────

  // Restore saved nickname
  function restoreNickname() {
    var saved = localStorage.getItem('wx_nickname');
    var el = document.getElementById('comment-nickname');
    if (saved && el && !el.value) {
      el.value = saved;
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      initClaps();
      initComments();
      restoreNickname();
    });
  } else {
    initClaps();
    initComments();
    restoreNickname();
  }
})();
