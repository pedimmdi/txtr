/* ============================================================
   txtr — dm.js
   DM list modal + conversation: send, delete, poll, reply
   ============================================================ */

'use strict';

/* ════════════════════════════════════════════════════════════
   DM LIST PAGE — New conversation modal
   ════════════════════════════════════════════════════════════ */

const newDmBtn    = document.getElementById('new-dm-btn');
const newDmModal  = document.getElementById('new-dm-modal');
const newDmClose  = document.getElementById('new-dm-close');
const newDmCancel = document.getElementById('new-dm-cancel');
const newDmGo     = document.getElementById('new-dm-go');
const dmInput     = document.getElementById('dm-username-input');
const dmError     = document.getElementById('dm-username-error');
const suggestionsEl = document.getElementById('dm-user-suggestions');

let selectedUsername = null;
let searchTimer = null;

function openNewDm() {
  if (newDmModal) {
    newDmModal.style.display = 'flex';
    selectedUsername = null;
    if (dmInput) {
      dmInput.value = '';
      dmInput.focus();
    }
    hideSuggestions();
    if (dmError) dmError.style.display = 'none';
  }
}

function closeNewDm() {
  if (newDmModal) {
    newDmModal.style.display = 'none';
    hideSuggestions();
  }
}

function hideSuggestions() {
  if (!suggestionsEl) return;
  suggestionsEl.style.display = 'none';
  suggestionsEl.innerHTML = '';
}

function pickUser(username) {
  selectedUsername = username;
  if (dmInput) dmInput.value = username;
  hideSuggestions();
  if (dmError) dmError.style.display = 'none';
}

async function searchUsers(query) {
  if (!suggestionsEl) return;

  if (!query || query.length < 1) {
    hideSuggestions();
    return;
  }

  try {
    const res = await window.txtr.apiFetch(
      `/api/v1/accounts/users/?search=${encodeURIComponent(query)}&page_size=8`
    );
    if (!res.ok) return;

    const data = await res.json();
    const users = data.results || data;

    if (!Array.isArray(users) || users.length === 0) {
      suggestionsEl.style.display = 'block';
      suggestionsEl.innerHTML =
        '<div class="dm-suggestion-item" style="cursor:default;color:var(--text-muted);">No users found</div>';
      return;
    }

    suggestionsEl.style.display = 'block';
    suggestionsEl.innerHTML = users.map(u => {
      const name = u.username;
      const initial = (name || '?')[0].toUpperCase();
      const avatar = u.image
        ? `<img src="${u.image}" class="avatar avatar-sm" alt="" />`
        : `<div class="avatar-placeholder avatar-sm">${initial}</div>`;
      return `
        <div class="dm-suggestion-item" data-username="${name}">
          ${avatar}
          <div>
            <div class="dm-suggestion-name">${name}</div>
            <div class="dm-suggestion-handle">@${name}</div>
          </div>
        </div>`;
    }).join('');

    suggestionsEl.querySelectorAll('.dm-suggestion-item[data-username]').forEach(item => {
      item.addEventListener('click', () => {
        pickUser(item.dataset.username);
      });
    });
  } catch {
    // silent — search is best-effort
  }
}

if (newDmBtn)    newDmBtn.addEventListener('click', openNewDm);
if (newDmClose)  newDmClose.addEventListener('click', closeNewDm);
if (newDmCancel) newDmCancel.addEventListener('click', closeNewDm);
if (newDmModal) {
  newDmModal.addEventListener('click', e => {
    if (e.target === newDmModal) closeNewDm();
  });
}

document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && newDmModal?.style.display !== 'none') closeNewDm();
});

if (dmInput) {
  dmInput.addEventListener('input', () => {
    selectedUsername = null;
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      searchUsers(dmInput.value.trim());
    }, 250);
  });

  dmInput.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      e.preventDefault();
      newDmGo?.click();
    }
  });
}

if (newDmGo) {
  newDmGo.addEventListener('click', async () => {
    const username = (selectedUsername || dmInput?.value || '').trim();
    if (!username) return;

    newDmGo.disabled = true;
    newDmGo.textContent = 'Opening…';
    if (dmError) dmError.style.display = 'none';

    try {
      const res = await window.txtr.apiFetch(
        `/api/v1/accounts/users/${encodeURIComponent(username)}/`
      );

      if (res.status === 404) {
        if (dmError) dmError.style.display = 'flex';
        return;
      }
      if (!res.ok) throw new Error();

      window.location.href = `/messages/${encodeURIComponent(username)}/`;
    } catch {
      window.txtr.showFlash('Could not open conversation.', 'error');
    } finally {
      newDmGo.disabled = false;
      newDmGo.textContent = 'Open chat';
    }
  });
}

/* ════════════════════════════════════════════════════════════
   CONVERSATION PAGE — send, delete, poll, reply
   ════════════════════════════════════════════════════════════ */

const messagesArea = document.getElementById('messages-area');
const msgInput     = document.getElementById('msg-input');
const msgSendBtn   = document.getElementById('msg-send-btn');
const OTHER_USER   = window.OTHER_USERNAME;
const ME           = window.MY_USERNAME;

let lastMsgId = 0;
let replyToId = null;

const replyBar     = document.getElementById('reply-bar');
const replyBarUser = document.getElementById('reply-bar-user');
const replyBarText = document.getElementById('reply-bar-text');
const replyBarClose = document.getElementById('reply-bar-close');

function clearReply() {
  replyToId = null;
  if (replyBar) replyBar.style.display = 'none';
  if (replyBarUser) replyBarUser.textContent = '';
  if (replyBarText) replyBarText.textContent = '';
}

function setReply(id, username, text) {
  replyToId = id;
  if (replyBarUser) replyBarUser.textContent = username || '';
  if (replyBarText) replyBarText.textContent = text || '';
  if (replyBar) replyBar.style.display = 'flex';
  msgInput?.focus();
}

if (replyBarClose) {
  replyBarClose.addEventListener('click', clearReply);
}

/* One listener for all current + future Reply / quote clicks */
if (messagesArea) {
  messagesArea.addEventListener('click', e => {
    const replyBtn = e.target.closest('.msg-reply-btn');
    if (replyBtn) {
      e.preventDefault();
      e.stopPropagation();
      setReply(
        replyBtn.dataset.msgId,
        replyBtn.dataset.msgUser,
        replyBtn.dataset.msgText
      );
      return;
    }

    const quote = e.target.closest('.msg-reply-quote[data-reply-to]');
    if (quote) {
      e.preventDefault();
      e.stopPropagation();
      highlightMessage(quote.dataset.replyTo);
    }
  });
}

if (msgInput) {
  msgInput.addEventListener('input', () => {
    msgInput.style.height = 'auto';
    msgInput.style.height = msgInput.scrollHeight + 'px';
    msgSendBtn.disabled = msgInput.value.trim().length === 0;
  });

  msgInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!msgSendBtn.disabled) sendMessage();
    }
  });

  msgSendBtn.addEventListener('click', sendMessage);

  scrollToBottom(false);
  lastMsgId = getLastMessageId();
  setInterval(() => pollMessages(), 15000);
}

/* ── Send message ────────────────────────────────────────── */
async function sendMessage() {
  const content = msgInput.value.trim();
  if (!content) return;

  msgSendBtn.disabled = true;
  const savedValue = content;
  const savedReplyId = replyToId;
  const savedReplyUser = replyBarUser?.textContent || '';
  const savedReplyText = replyBarText?.textContent || '';

  const payload = { content: savedValue };
  if (savedReplyId) payload.reply_to = Number(savedReplyId);

  const tempId = `temp-${Date.now()}`;
  const tempMsg = buildBubble({
    id: tempId,
    content: savedValue,
    sender_username: ME,
    created_at: new Date().toISOString(),
    is_read: false,
    reply_to: savedReplyId
      ? {
          id: savedReplyId,
          content: savedReplyText,
          sender_username: savedReplyUser,
        }
      : null,
  }, true);

  messagesArea.insertAdjacentHTML('beforeend', tempMsg);
  msgInput.value = '';
  msgInput.style.height = 'auto';
  clearReply();
  scrollToBottom();

  try {
    const res = await window.txtr.apiFetch(`/api/v1/dm/${OTHER_USER}/`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    if (!res.ok) throw new Error();
    const msg = await res.json();

    const tempEl = document.getElementById(`msg-${tempId}`);
    if (tempEl) tempEl.outerHTML = buildBubble(msg, true);

    // attachReplyButtons();
    // attachQuoteJump();

    const realId = parseInt(msg.id, 10);
    if (!Number.isNaN(realId) && realId > lastMsgId) {
      lastMsgId = realId;
    }
  } catch {
    document.getElementById(`msg-${tempId}`)?.remove();
    msgInput.value = savedValue;
    msgInput.style.height = 'auto';
    if (savedReplyId) {
      setReply(savedReplyId, savedReplyUser, savedReplyText);
    }
    window.txtr.showFlash('Message not sent. Try again.', 'error');
  } finally {
    msgSendBtn.disabled = msgInput.value.trim().length === 0;
  }
}

/* ── Delete message ──────────────────────────────────────── */
window.deleteMessage = async function (msgId, username) {
  if (!confirm('Delete this message?')) return;

  try {
    const res = await window.txtr.apiFetch(
      `/api/v1/dm/${username}/${msgId}/`,
      { method: 'DELETE' }
    );
    if (!res.ok) throw new Error();
    document.getElementById(`msg-${msgId}`)?.remove();
  } catch {
    window.txtr.showFlash('Could not delete message.', 'error');
  }
};

/* ── Poll for new messages ───────────────────────────────── */
async function pollMessages() {
  try {
    const res = await window.txtr.apiFetch(`/api/v1/dm/${OTHER_USER}/`);
    if (!res.ok) return;

    const data = await res.json();
    const all  = data.results || data;
    if (!Array.isArray(all)) return;

    let added = false;

    all.forEach(msg => {
      const el = document.getElementById(`msg-${msg.id}`);
      if (el) {
        if (msg.sender_username === ME) {
          const tick = el.querySelector('.msg-ticks');
          if (tick) {
            if (msg.is_read) {
              tick.classList.add('read');
              tick.textContent = '✓✓';
              tick.title = 'Read';
            } else {
              tick.classList.remove('read');
              tick.textContent = '✓';
              tick.title = 'Sent';
            }
          }
        }
        return;
      }

      if (Number(msg.id) <= lastMsgId) return;
      const isMe = msg.sender_username === ME;
      messagesArea.insertAdjacentHTML('beforeend', buildBubble(msg, isMe));
      added = true;
    });

    if (added) {
      scrollToBottom();
    }

    const ids = all.map(m => Number(m.id)).filter(n => !Number.isNaN(n));
    if (ids.length) {
      const maxId = Math.max(...ids);
      if (maxId > lastMsgId) lastMsgId = maxId;
    }
  } catch {
    // Silently fail — polling is best-effort
  }
}

/* ── Build message bubble HTML ───────────────────────────── */
function buildBubble(msg, isMe) {
  const avatarHtml = !isMe
    ? (window.OTHER_AVATAR
        ? `<img src="${window.OTHER_AVATAR}" alt="${OTHER_USER}" class="avatar avatar-sm" />`
        : `<div class="avatar-placeholder avatar-sm">${(OTHER_USER || '?')[0].toUpperCase()}</div>`)
    : '';

  const canDelete = isMe && String(msg.id).indexOf('temp-') !== 0;
  const deleteBtn = canDelete
    ? `<button class="msg-delete" onclick="deleteMessage(${msg.id}, '${OTHER_USER}')" title="Delete">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
       </button>`
    : '';

  const time = new Date(msg.created_at).toLocaleTimeString('en', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });

  const isRead = !!msg.is_read;
  const ticks = isMe
    ? `<span class="msg-ticks ${isRead ? 'read' : ''}" title="${isRead ? 'Read' : 'Sent'}">${isRead ? '✓✓' : '✓'}</span>`
    : '';

  let quoteHtml = '';
  if (msg.reply_to) {
    const qText = msg.reply_to.content
      || (msg.reply_to.has_forwarded_post ? 'Forwarded post' : '');
    const parentId = msg.reply_to.id || '';
    quoteHtml = `
      <div class="msg-reply-quote" data-reply-to="${parentId}" title="Jump to message">
        <span class="msg-reply-quote-user">${escHtml(msg.reply_to.sender_username || '')}</span>
        <span class="msg-reply-quote-text">${escHtml(qText)}</span>
      </div>`;
  }

  let forwardHtml = '';
  if (msg.forwarded_post) {
    const fp = msg.forwarded_post;
    forwardHtml = `
      <a href="${fp.url || `/posts/${fp.id}/`}" class="msg-forward-card">
        <div class="msg-forward-author">@${escHtml(fp.author_username || '')}</div>
        <div class="msg-forward-content">${escHtml(fp.content || '')}</div>
        <div class="msg-forward-link">View post</div>
      </a>`;
  }

  const textHtml = msg.content
    ? `<span class="msg-bubble-text">${escHtml(msg.content)}</span>`
    : '';

  const previewText = (msg.content || (msg.forwarded_post ? 'Forwarded post' : '')).slice(0, 80);
  const replyBtn = String(msg.id).indexOf('temp-') === 0
    ? ''
    : `<button type="button" class="msg-reply-btn"
         data-msg-id="${msg.id}"
         data-msg-user="${escHtml(msg.sender_username || (isMe ? ME : OTHER_USER))}"
         data-msg-text="${escHtml(previewText)}"
         title="Reply">Reply</button>`;

  return `
    <div class="msg-row ${isMe ? 'me' : ''}" id="msg-${msg.id}">
      ${avatarHtml}
      <div class="msg-stack">
        <div class="msg-bubble">
          ${quoteHtml}
          ${forwardHtml}
          ${textHtml}
          ${deleteBtn}
        </div>
        <div class="msg-meta">
          <span class="msg-time">${time}</span>
          ${ticks}
        </div>
        ${replyBtn}
      </div>
    </div>`;
}

/* ── Scroll to bottom ────────────────────────────────────── */
function scrollToBottom(smooth = true) {
  if (!messagesArea) return;
  messagesArea.scrollTo({
    top: messagesArea.scrollHeight,
    behavior: smooth ? 'smooth' : 'auto',
  });
}

/* ── Get last message id (for polling) ───────────────────── */
function getLastMessageId() {
  const rows = messagesArea?.querySelectorAll('[id^="msg-"]') || [];
  if (rows.length === 0) return 0;
  const ids = [...rows]
    .map(el => parseInt(el.id.replace('msg-', ''), 10))
    .filter(n => !Number.isNaN(n));
  return ids.length ? Math.max(...ids) : 0;
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function highlightMessage(msgId) {
  if (!msgId) return;
  const el = document.getElementById(`msg-${msgId}`);
  if (!el) {
    window.txtr.showFlash('Original message is not loaded.', 'info');
    return;
  }
  document.querySelectorAll('.msg-row.msg-highlight').forEach(r => {
    r.classList.remove('msg-highlight');
  });
  el.classList.add('msg-highlight');
  el.scrollIntoView({ behavior: 'smooth', block: 'center' });
  setTimeout(() => el.classList.remove('msg-highlight'), 1400);
}

// function attachQuoteJump(root = document) {
//   root.querySelectorAll('.msg-reply-quote[data-reply-to]').forEach(quote => {
//     if (quote._jumpAttached) return;
//     quote._jumpAttached = true;
//     quote.addEventListener('click', e => {
//       e.stopPropagation();
//       highlightMessage(quote.dataset.replyTo);
//     });
//   });
// }