/* ============================================================
   txtr — post_detail.js
   AJAX comment loading, creation, replies, like, delete
   ============================================================ */

'use strict';

const POST_ID    = window.POST_ID;
const IS_AUTH    = window.IS_AUTH;
const ME         = window.CURRENT_USER;
const MY_AVATAR  = window.CURRENT_AVATAR;
const MAX_COMMENT = 500;

/* ── Comment Compose Counter ─────────────────────────────── */
const commentInput   = document.getElementById('comment-input');
const commentCounter = document.getElementById('comment-char-counter');
const commentSubmit  = document.getElementById('comment-submit');

if (commentInput) {
  commentInput.addEventListener('input', () => {
    const remaining = MAX_COMMENT - commentInput.value.length;
    commentCounter.textContent = remaining;
    commentCounter.classList.toggle('warn',   remaining <= 100 && remaining > 30);
    commentCounter.classList.toggle('danger', remaining <= 30);
    commentSubmit.disabled = commentInput.value.trim().length === 0 || remaining < 0;

    commentInput.style.height = 'auto';
    commentInput.style.height = commentInput.scrollHeight + 'px';
  });

  commentInput.addEventListener('keydown', e => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter' && !commentSubmit.disabled) {
      submitComment();
    }
  });

  commentSubmit.addEventListener('click', submitComment);
}

/* ── Load Comments ───────────────────────────────────────── */
async function loadComments() {
  const section = document.getElementById('comments-section');

  try {
    const res  = await fetch(`/api/v1/posts/${POST_ID}/comments/`);
    const data = await res.json();
    const comments = data.results || data;

    // Update comments count in stats
    const countEl = document.getElementById('comments-count');
    if (countEl) countEl.textContent = comments.length;

    if (comments.length === 0) {
      section.innerHTML = `
        <div class="empty-state" style="padding:40px 20px;">
          <div class="empty-state-icon">💬</div>
          <div class="empty-state-title">No replies yet</div>
          <p class="empty-state-text">Be the first to reply to this post.</p>
        </div>`;
      return;
    }

    section.innerHTML = comments.map(renderComment).join('');

  } catch {
    section.innerHTML = `
      <div class="empty-state" style="padding:40px;">
        <div class="empty-state-text">Could not load replies.</div>
      </div>`;
  }
}

/* ── Render a Comment ────────────────────────────────────── */
function renderComment(c, isReply = false) {
  const avatarHTML = c.author.image
    ? `<img src="${c.author.image}" alt="${c.author.username}" class="avatar avatar-md" />`
    : `<div class="avatar-placeholder avatar-md">${c.author.username[0].toUpperCase()}</div>`;

  const likedClass = c.is_liked ? 'liked' : '';
  const likedFill  = c.is_liked ? 'var(--like)' : 'none';
  const likedStroke = c.is_liked ? 'var(--like)' : 'currentColor';

  const timeAgo = formatRelativeTime(c.created_date);

  const deleteBtn = (IS_AUTH && c.author.username === ME)
    ? `<button class="comment-action-btn delete-btn" onclick="deleteComment(${c.id}, this)">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/>
          <path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/>
        </svg>
        Delete
       </button>`
    : '';

  const replyBtn = IS_AUTH && !isReply
    ? `<button class="comment-action-btn reply-btn" onclick="toggleReplyCompose(${c.id}, this)">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
        </svg>
        Reply
       </button>`
    : '';

  const repliesSection = !isReply && c.replies_count > 0
    ? `<button class="show-replies-btn" onclick="toggleReplies(${c.id}, this)">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
          <polyline points="6 9 12 15 18 9"/>
        </svg>
        Show ${c.replies_count} repl${c.replies_count === 1 ? 'y' : 'ies'}
       </button>
       <div class="reply-thread" id="replies-${c.id}" style="display:none;"></div>`
    : !isReply
    ? `<div class="reply-thread" id="replies-${c.id}" style="display:none;"></div>`
    : '';

  const wrapperClass = isReply ? 'reply-card' : 'comment-card';

  return `
    <div class="${wrapperClass}" id="comment-${c.id}">
      <div class="comment-inner">
        <a href="/profile/${c.author.username}/">${avatarHTML}</a>
        <div class="comment-body">
          <div class="comment-header">
            <a href="/profile/${c.author.username}/" class="comment-author-name">
              ${escHtml(c.author.username)}
            </a>
            <span class="comment-author-handle">@${escHtml(c.author.username)}</span>
            <span class="comment-date">${timeAgo}</span>
          </div>
          <div class="comment-content">${escHtml(c.content)}</div>
          <div class="comment-actions">
            ${IS_AUTH ? `
              <button class="comment-action-btn like-btn ${likedClass}"
                      data-comment-id="${c.id}"
                      data-liked="${c.is_liked}"
                      onclick="likeComment(${c.id}, this)">
                <svg width="14" height="14" viewBox="0 0 24 24"
                     fill="${likedFill}" stroke="${likedStroke}" stroke-width="1.8" stroke-linecap="round">
                  <path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/>
                </svg>
                <span class="comment-like-count">${c.likes_count}</span>
              </button>` : ''}
            ${replyBtn}
            ${deleteBtn}
          </div>
        </div>
      </div>
      ${repliesSection}
      <div id="reply-compose-${c.id}" style="display:none;"></div>
    </div>`;
}

/* ── Submit Comment ──────────────────────────────────────── */
async function submitComment() {
  const content = commentInput.value.trim();
  if (!content) return;

  commentSubmit.disabled = true;
  commentSubmit.textContent = 'Replying…';

  try {
    const res = await window.txtr.apiFetch(`/api/v1/posts/${POST_ID}/comments/`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    });

    if (!res.ok) throw new Error();
    const comment = await res.json();

    // Prepend to comments section
    const section = document.getElementById('comments-section');
    const emptyState = section.querySelector('.empty-state');
    if (emptyState) emptyState.remove();
    section.insertAdjacentHTML('afterbegin', renderComment(comment));

    // Update count
    const countEl = document.getElementById('comments-count');
    if (countEl) countEl.textContent = parseInt(countEl.textContent || 0) + 1;

    // Reset
    commentInput.value = '';
    commentInput.style.height = 'auto';
    commentCounter.textContent = MAX_COMMENT;
    window.txtr.showFlash('Reply posted!', 'success');

  } catch {
    window.txtr.showFlash('Could not post reply.', 'error');
  } finally {
    commentSubmit.textContent = 'Reply';
    commentSubmit.disabled = commentInput.value.trim().length === 0;
  }
}

/* ── Like Comment ────────────────────────────────────────── */
async function likeComment(commentId, btn) {
  const isLiked  = btn.dataset.liked === 'true';
  const countEl  = btn.querySelector('.comment-like-count');
  const svg      = btn.querySelector('svg');

  // Optimistic update
  const newLiked = !isLiked;
  btn.dataset.liked = newLiked;
  btn.classList.toggle('liked', newLiked);
  svg.setAttribute('fill', newLiked ? 'var(--like)' : 'none');
  svg.setAttribute('stroke', newLiked ? 'var(--like)' : 'currentColor');
  if (countEl) countEl.textContent = parseInt(countEl.textContent || 0) + (newLiked ? 1 : -1);

  try {
    const res = await window.txtr.apiFetch(
      `/api/v1/posts/${POST_ID}/comments/${commentId}/like/`,
      { method: 'POST' }
    );
    if (!res.ok) throw new Error();
  } catch {
    // Revert
    btn.dataset.liked = isLiked;
    btn.classList.toggle('liked', isLiked);
    svg.setAttribute('fill', isLiked ? 'var(--like)' : 'none');
    svg.setAttribute('stroke', isLiked ? 'var(--like)' : 'currentColor');
    if (countEl) countEl.textContent = parseInt(countEl.textContent || 0) + (isLiked ? 1 : -1);
    window.txtr.showFlash('Something went wrong.', 'error');
  }
}

/* ── Delete Comment ──────────────────────────────────────── */
async function deleteComment(commentId, btn) {
  if (!confirm('Delete this reply?')) return;

  try {
    const res = await window.txtr.apiFetch(
      `/api/v1/posts/${POST_ID}/comments/${commentId}/`,
      { method: 'DELETE' }
    );
    if (!res.ok) throw new Error();

    const card = document.getElementById(`comment-${commentId}`);
    if (card) card.remove();

    const countEl = document.getElementById('comments-count');
    if (countEl) countEl.textContent = Math.max(0, parseInt(countEl.textContent || 0) - 1);

    window.txtr.showFlash('Reply deleted.', 'info');
  } catch {
    window.txtr.showFlash('Could not delete reply.', 'error');
  }
}

/* ── Toggle Replies ──────────────────────────────────────── */
async function toggleReplies(commentId, btn) {
  const thread = document.getElementById(`replies-${commentId}`);

  if (thread.style.display !== 'none') {
    thread.style.display = 'none';
    btn.querySelector('svg').style.transform = '';
    return;
  }

  btn.querySelector('svg').style.transform = 'rotate(180deg)';
  thread.style.display = 'block';

  if (thread.innerHTML.trim() !== '') return; // already loaded

  thread.innerHTML = '<div style="padding:10px;color:var(--text-muted);font-size:13px;">Loading…</div>';

  try {
    const res  = await fetch(`/api/v1/posts/${POST_ID}/comments/${commentId}/replies/`);
    const data = await res.json();
    const replies = data.results || data;

    if (replies.length === 0) {
      thread.innerHTML = '<div style="padding:10px;color:var(--text-muted);font-size:13px;">No replies yet.</div>';
      return;
    }

    thread.innerHTML = replies.map(r => renderComment(r, true)).join('');
  } catch {
    thread.innerHTML = '<div style="padding:10px;color:var(--danger);font-size:13px;">Could not load replies.</div>';
  }
}

/* ── Toggle Reply Compose ────────────────────────────────── */
function toggleReplyCompose(commentId, triggerBtn) {
  const container = document.getElementById(`reply-compose-${commentId}`);

  if (container.style.display !== 'none') {
    container.style.display = 'none';
    container.innerHTML = '';
    return;
  }

  container.style.display = 'block';
  container.innerHTML = `
    <div class="reply-compose">
      <div>${MY_AVATAR
        ? `<img src="${MY_AVATAR}" class="avatar avatar-sm" />`
        : `<div class="avatar-placeholder avatar-sm">${ME[0].toUpperCase()}</div>`}
      </div>
      <textarea
        id="reply-input-${commentId}"
        placeholder="Reply to this comment…"
        maxlength="500"
        rows="2"
        oninput="this.style.height='auto';this.style.height=this.scrollHeight+'px';
                 document.getElementById('reply-submit-${commentId}').disabled=this.value.trim().length===0;"
      ></textarea>
      <div class="reply-compose-actions">
        <button class="reply-submit" id="reply-submit-${commentId}" disabled
                onclick="submitReply(${commentId})">Reply</button>
        <button class="reply-cancel" onclick="toggleReplyCompose(${commentId})">Cancel</button>
      </div>
    </div>`;

  document.getElementById(`reply-input-${commentId}`).focus();
}

/* ── Submit Reply ────────────────────────────────────────── */
async function submitReply(commentId) {
  const input  = document.getElementById(`reply-input-${commentId}`);
  const btn    = document.getElementById(`reply-submit-${commentId}`);
  const content = input.value.trim();
  if (!content) return;

  btn.disabled = true;
  btn.textContent = 'Replying…';

  try {
    const res = await window.txtr.apiFetch(
      `/api/v1/posts/${POST_ID}/comments/${commentId}/replies/`,
      { method: 'POST', body: JSON.stringify({ content }) }
    );

    if (!res.ok) throw new Error();
    const reply = await res.json();

    // Make sure reply thread is visible
    const thread = document.getElementById(`replies-${commentId}`);
    if (thread) {
      thread.style.display = 'block';
      thread.insertAdjacentHTML('beforeend', renderComment(reply, true));
    }

    // Update replies count on the show-replies button
    const showBtn = document.querySelector(`.show-replies-btn[onclick*="${commentId}"]`);
    if (showBtn) {
      const current = parseInt(showBtn.textContent.match(/\d+/)?.[0] || 0) + 1;
      showBtn.innerHTML = showBtn.innerHTML.replace(/\d+ repl/, `${current} repl`);
    }

    // Close compose
    toggleReplyCompose(commentId);
    window.txtr.showFlash('Reply posted!', 'success');

  } catch {
    btn.textContent = 'Reply';
    btn.disabled = false;
    window.txtr.showFlash('Could not post reply.', 'error');
  }
}

/* ── Delete Post ─────────────────────────────────────────── */
const deletePostBtn = document.getElementById('delete-post-btn');
if (deletePostBtn) {
  deletePostBtn.addEventListener('click', async () => {
    if (!confirm('Delete this post? This cannot be undone.')) return;

    try {
      const res = await window.txtr.apiFetch(`/api/v1/posts/${POST_ID}/`, { method: 'DELETE' });
      if (!res.ok) throw new Error();
      window.location.href = '/feed/';
    } catch {
      window.txtr.showFlash('Could not delete post.', 'error');
    }
  });
}

/* ── Override like/bookmark stats on detail page ─────────── */
// Update the stats row numbers when liked/bookmarked
const origAttachLike = window.txtr.attachLikeHandlers;
document.querySelectorAll('[data-action="like"]').forEach(btn => {
  btn.addEventListener('click', () => {
    const countEl = document.getElementById('likes-count');
    if (!countEl) return;
    const isLiked = btn.dataset.liked === 'true';
    setTimeout(() => {
      countEl.textContent = parseInt(countEl.textContent || 0) + (isLiked ? -1 : 1);
    }, 0);
  });
});

/* ── Helpers ─────────────────────────────────────────────── */
function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function formatRelativeTime(isoString) {
  const date    = new Date(isoString);
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 60)  return 'just now';
  if (seconds < 3600) return Math.floor(seconds / 60) + 'm';
  if (seconds < 86400) return Math.floor(seconds / 3600) + 'h';
  if (seconds < 604800) return Math.floor(seconds / 86400) + 'd';
  return date.toLocaleDateString('en', { month: 'short', day: 'numeric' });
}

/* ── Init ────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  loadComments();
  window.txtr.attachLikeHandlers();
  window.txtr.attachBookmarkHandlers();
  window.txtr.attachRepostHandlers();
});