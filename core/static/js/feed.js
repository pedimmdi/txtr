/* ============================================================
   txtr — feed.js
   Compose box, character counter, post creation via API,
   post menu, follow toggle in sidebar
   ============================================================ */

'use strict';

const MAX_LENGTH = 1000;

/* ── Compose Box ─────────────────────────────────────────── */
const textarea  = document.getElementById('compose-textarea');
const counter   = document.getElementById('char-counter');
const submitBtn = document.getElementById('compose-submit');

if (textarea) {
  textarea.addEventListener('input', () => {
    const remaining = MAX_LENGTH - textarea.value.length;
    counter.textContent = remaining;

    counter.classList.remove('warn', 'danger');
    if (remaining <= 50)  counter.classList.add('danger');
    else if (remaining <= 150) counter.classList.add('warn');

    submitBtn.disabled = textarea.value.trim().length === 0 || remaining < 0;

    // Auto-grow
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
  });

  // Cmd/Ctrl + Enter to submit
  textarea.addEventListener('keydown', e => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      if (!submitBtn.disabled) submitBtn.click();
    }
  });
}

// Hashtag button inserts # at cursor
const hashtagBtn = document.getElementById('compose-hashtag');
if (hashtagBtn && textarea) {
  hashtagBtn.addEventListener('click', () => {
    textarea.focus();
    const pos = textarea.selectionStart;
    const before = textarea.value.slice(0, pos);
    const after  = textarea.value.slice(pos);
    const insert = before.endsWith(' ') || before === '' ? '#' : ' #';
    textarea.value = before + insert + after;
    textarea.selectionStart = textarea.selectionEnd = pos + insert.length;
    textarea.dispatchEvent(new Event('input'));
  });
}

/* ── Submit New Post ─────────────────────────────────────── */
if (submitBtn) {
  submitBtn.addEventListener('click', async () => {
    const content = textarea.value.trim();
    if (!content) return;

    submitBtn.disabled = true;
    submitBtn.textContent = 'Posting…';

    try {
      const res = await window.txtr.apiFetch('/api/v1/posts/', {
        method: 'POST',
        body: JSON.stringify({ content }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.content?.[0] || 'Something went wrong.');
      }

      const post = await res.json();

      // Prepend the new post card to the feed without reloading
      const postList = document.getElementById('post-list');
      const emptyState = postList.querySelector('.empty-state');
      if (emptyState) emptyState.remove();

      const tempCard = createPostCard(post);
      postList.insertAdjacentHTML('afterbegin', tempCard);

      // Re-attach handlers to the new card
      window.txtr.attachLikeHandlers();
      window.txtr.attachBookmarkHandlers();
      window.txtr.attachRepostHandlers();

      // Reset compose box
      textarea.value = '';
      textarea.style.height = 'auto';
      counter.textContent  = MAX_LENGTH;
      counter.classList.remove('warn', 'danger');
      window.txtr.showFlash('Post published!', 'success');

    } catch (err) {
      window.txtr.showFlash(err.message || 'Could not publish post.', 'error');
    } finally {
      submitBtn.textContent = 'Post';
      submitBtn.disabled = textarea.value.trim().length === 0;
    }
  });
}

/* ── Build a minimal post card HTML from API response ────── */
function createPostCard(post) {
  const avatar = post.author.image
    ? `<img src="${post.author.image}" alt="${post.author.username}" class="avatar avatar-md" />`
    : `<div class="avatar-placeholder avatar-md">${post.author.username[0].toUpperCase()}</div>`;

  const hashtags = (post.hashtags || [])
    .map(t => `<a href="/hashtags/${t}/posts/" style="font-size:13px;color:var(--accent);font-weight:500;">#${t}</a>`)
    .join('');

  return `
    <article class="post-card" data-post-id="${post.id}">
      <div class="post-inner">
        <a href="/profile/${post.author.username}/">${avatar}</a>
        <div class="post-body">
          <div class="post-header">
            <a href="/profile/${post.author.username}/" class="post-author-name">${post.author.username}</a>
            <span class="post-author-handle">@${post.author.username}</span>
            <span class="post-dot">·</span>
            <span class="post-date">just now</span>
          </div>
          <div class="post-content">${escapeHtml(post.content)}</div>
          ${hashtags ? `<div style="display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px;">${hashtags}</div>` : ''}
          <div class="post-actions" onclick="event.stopPropagation()">
            <a href="/posts/${post.id}/" class="action-btn comment-btn">
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
              </svg>
              <span>0</span>
            </a>
            <span class="action-spacer"></span>
            <button class="action-btn" data-action="bookmark"
                    data-post-id="${post.id}" data-bookmarked="false">
              <svg width="17" height="17" viewBox="0 0 24 24" fill="none"
                   stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
                <path d="M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2z"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </article>`;
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/* ── Post Card Click → Detail Page ──────────────────────── */
document.addEventListener('click', e => {
  const card = e.target.closest('.post-card');
  if (!card) return;

  // Don't navigate if clicking a link, button, or interactive element
  if (e.target.closest('a, button, [data-action]')) return;

  const postId = card.dataset.postId;
  if (postId) window.location.href = `/posts/${postId}/`;
});

/* ── Post Menu (edit / delete) ───────────────────────────── */
let currentMenuEl = null;

window.openPostMenu = function(postId, triggerBtn) {
  // Close any open menu
  document.querySelectorAll('.post-context-menu').forEach(m => m.remove());

  const menu = document.createElement('div');
  menu.className = 'dropdown-menu post-context-menu open';
  menu.style.cssText = 'position:fixed; min-width:160px; z-index:200;';
  menu.innerHTML = `
    <a href="/posts/${postId}/edit/" class="dropdown-item">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
        <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
      </svg>
      Edit post
    </a>
    <button class="dropdown-item danger" onclick="deletePost(${postId}, this)">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
        <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/>
        <path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/>
      </svg>
      Delete post
    </button>
  `;

  const rect = triggerBtn.getBoundingClientRect();
  menu.style.top  = (rect.bottom + 4) + 'px';
  menu.style.left = (rect.left - 120) + 'px';
  document.body.appendChild(menu);
  currentMenuEl = menu;
};

document.addEventListener('click', e => {
  if (currentMenuEl && !currentMenuEl.contains(e.target)) {
    currentMenuEl.remove();
    currentMenuEl = null;
  }
});

window.deletePost = async function(postId, btn) {
  if (!confirm('Delete this post?')) return;

  try {
    const res = await window.txtr.apiFetch(`/api/v1/posts/${postId}/`, { method: 'DELETE' });
    if (!res.ok) throw new Error();

    const card = document.querySelector(`[data-post-id="${postId}"].post-card`);
    if (card) card.remove();

    if (currentMenuEl) { currentMenuEl.remove(); currentMenuEl = null; }
    window.txtr.showFlash('Post deleted.', 'info');
  } catch {
    window.txtr.showFlash('Could not delete post.', 'error');
  }
};

/* ── Follow Toggle (sidebar) ─────────────────────────────── */
document.querySelectorAll('.follow-btn').forEach(btn => {
  btn.addEventListener('click', async () => {
    const username = btn.dataset.username;

    try {
      const res = await window.txtr.apiFetch(`/api/v1/accounts/follow/${username}/`, { method: 'POST' });
      if (!res.ok) throw new Error();
      const data = await res.json();

      const isFollowing = data.is_following;
      btn.dataset.following = isFollowing;
      btn.textContent = isFollowing ? 'Following' : 'Follow';
      btn.classList.toggle('btn-primary', isFollowing);
      btn.classList.toggle('btn-outline', !isFollowing);
    } catch {
      window.txtr.showFlash('Could not update follow status.', 'error');
    }
  });
});