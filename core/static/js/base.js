/* ============================================================
   txtr — base.js
   Global utilities: CSRF, flash messages, active nav,
   dropdown menus, notification count polling
   ============================================================ */

'use strict';

/* ── CSRF Token ─────────────────────────────────────────── */
function getCookie(name) {
  let value = null;
  document.cookie.split(';').forEach(part => {
    const [key, val] = part.trim().split('=');
    if (key === name) value = decodeURIComponent(val);
  });
  return value;
}

const CSRF_TOKEN = getCookie('csrftoken');

/**
 * Wrapper around fetch that automatically attaches the CSRF token
 * and Content-Type for JSON requests.
 */
function apiFetch(url, options = {}) {
  const defaults = {
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': CSRF_TOKEN,
    },
    credentials: 'same-origin',
  };
  return fetch(url, {
    ...defaults,
    ...options,
    headers: { ...defaults.headers, ...(options.headers || {}) },
  });
}

/* ── Flash Messages ─────────────────────────────────────── */
function showFlash(message, type = 'info') {
  const container = document.getElementById('flash-container');
  if (!container) return;

  const el = document.createElement('div');
  el.className = `flash flash-${type}`;
  el.textContent = message;

  container.appendChild(el);

  setTimeout(() => {
    el.style.animation = 'flashOut 0.2s ease forwards';
    el.addEventListener('animationend', () => el.remove());
  }, 3000);
}

/* Auto-dismiss Django messages on page load */
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.flash[data-auto]').forEach(el => {
    setTimeout(() => {
      el.style.animation = 'flashOut 0.2s ease forwards';
      el.addEventListener('animationend', () => el.remove());
    }, 3000);
  });
});

/* ── Active Nav Link ─────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  const currentPath = window.location.pathname;

  // Desktop sidebar
  document.querySelectorAll('.nav-item').forEach(item => {
    const href = item.getAttribute('href');
    if (!href) return;
    if (href === '/' ? currentPath === '/' : currentPath.startsWith(href)) {
      item.classList.add('active');
    }
  });

  // Mobile bottom nav
  document.querySelectorAll('.mobile-nav-item').forEach(item => {
    const href = item.getAttribute('href');
    if (!href) return;
    if (href === '/' ? currentPath === '/' : currentPath.startsWith(href)) {
      item.classList.add('active');
    }
  });
});

/* ── User Dropdown ───────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  const userCard  = document.getElementById('user-card');
  const dropdown  = document.getElementById('user-dropdown');

  if (!userCard || !dropdown) return;

  userCard.addEventListener('click', (e) => {
    e.stopPropagation();
    dropdown.classList.toggle('open');
  });

  document.addEventListener('click', () => {
    dropdown.classList.remove('open');
  });
});

/* ── Notification Count Polling ──────────────────────────── */
function updateNotificationBadge(count) {
  document.querySelectorAll('.notif-badge').forEach(badge => {
    if (count > 0) {
      badge.textContent = count > 99 ? '99+' : count;
      badge.style.display = 'flex';
    } else {
      badge.style.display = 'none';
    }
  });
}

async function fetchNotificationCount() {
  try {
    const res = await apiFetch('/api/v1/notifications/unread-count/');
    if (!res.ok) return;
    const data = await res.json();
    updateNotificationBadge(data.unread_count || 0);
  } catch {
    // Silently fail — not critical
  }
}

// Poll every 60 seconds if user is logged in
document.addEventListener('DOMContentLoaded', () => {
  if (document.body.dataset.authenticated === 'true') {
    fetchNotificationCount();
    setInterval(fetchNotificationCount, 60000);
  }
});

/* ── Like Toggle ─────────────────────────────────────────── */
/**
 * Generic like toggle handler.
 * Button must have:
 *   data-post-id="<pk>"
 *   data-liked="true|false"
 * Children with class .like-count for the counter.
 */
function attachLikeHandlers() {
  document.querySelectorAll('[data-action="like"]').forEach(btn => {
    if (btn._likeAttached) return;
    btn._likeAttached = true;

    btn.addEventListener('click', async () => {
      const postId   = btn.dataset.postId;
      const isLiked  = btn.dataset.liked === 'true';
      const countEl  = btn.querySelector('.like-count');

      // Optimistic update
      const newLiked = !isLiked;
      btn.dataset.liked = newLiked;
      btn.classList.toggle('liked', newLiked);
      if (countEl) {
        countEl.textContent = parseInt(countEl.textContent || 0) + (newLiked ? 1 : -1);
      }

      try {
        const res = await apiFetch(`/api/v1/posts/${postId}/like/`, { method: 'POST' });
        if (!res.ok) throw new Error();
      } catch {
        // Revert on failure
        btn.dataset.liked = isLiked;
        btn.classList.toggle('liked', isLiked);
        if (countEl) {
          countEl.textContent = parseInt(countEl.textContent || 0) + (isLiked ? 1 : -1);
        }
        showFlash('Something went wrong.', 'error');
      }
    });
  });
}

/* ── Bookmark Toggle ─────────────────────────────────────── */
function attachBookmarkHandlers() {
  document.querySelectorAll('[data-action="bookmark"]').forEach(btn => {
    if (btn._bookmarkAttached) return;
    btn._bookmarkAttached = true;

    btn.addEventListener('click', async () => {
      const postId      = btn.dataset.postId;
      const isBookmarked = btn.dataset.bookmarked === 'true';

      btn.dataset.bookmarked = !isBookmarked;
      btn.classList.toggle('bookmarked', !isBookmarked);

      try {
        const res = await apiFetch(`/api/v1/posts/${postId}/bookmark/`, { method: 'POST' });
        if (!res.ok) throw new Error();
        showFlash(
          isBookmarked ? 'Removed from bookmarks' : 'Saved to bookmarks',
          'info'
        );
      } catch {
        btn.dataset.bookmarked = isBookmarked;
        btn.classList.toggle('bookmarked', isBookmarked);
        showFlash('Something went wrong.', 'error');
      }
    });
  });
}

/* ── Repost Toggle ───────────────────────────────────────── */
function attachRepostHandlers() {
  document.querySelectorAll('[data-action="repost"]').forEach(btn => {
    if (btn._repostAttached) return;
    btn._repostAttached = true;

    btn.addEventListener('click', async () => {
      const postId    = btn.dataset.postId;
      const isReposted = btn.dataset.reposted === 'true';
      const countEl   = btn.querySelector('.repost-count');

      btn.dataset.reposted = !isReposted;
      btn.classList.toggle('reposted', !isReposted);
      if (countEl) {
        countEl.textContent = parseInt(countEl.textContent || 0) + (isReposted ? -1 : 1);
      }

      try {
        const res = await apiFetch(`/api/v1/posts/${postId}/repost/`, { method: 'POST' });
        if (!res.ok) throw new Error();
        showFlash(
          isReposted ? 'Repost removed' : 'Reposted',
          'info'
        );
      } catch {
        btn.dataset.reposted = isReposted;
        btn.classList.toggle('reposted', isReposted);
        if (countEl) {
          countEl.textContent = parseInt(countEl.textContent || 0) + (isReposted ? 1 : -1);
        }
        showFlash('Something went wrong.', 'error');
      }
    });
  });
}

/* ── Init all handlers ───────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  attachLikeHandlers();
  attachBookmarkHandlers();
  attachRepostHandlers();
});

/* Expose globally for dynamic content (e.g., after loading new posts) */
window.txtr = {
  apiFetch,
  showFlash,
  attachLikeHandlers,
  attachBookmarkHandlers,
  attachRepostHandlers,
};
