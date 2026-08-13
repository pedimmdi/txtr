/* ============================================================
   txtr — dm.js
   DM list modal + conversation: send, delete, poll new msgs
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

function openNewDm()  { if (newDmModal) { newDmModal.style.display = 'flex'; dmInput?.focus(); } }
function closeNewDm() { if (newDmModal) { newDmModal.style.display = 'none'; } }

if (newDmBtn)    newDmBtn.addEventListener('click', openNewDm);
if (newDmClose)  newDmClose.addEventListener('click', closeNewDm);
if (newDmCancel) newDmCancel.addEventListener('click', closeNewDm);
if (newDmModal)  newDmModal.addEventListener('click', e => { if (e.target === newDmModal) closeNewDm(); });

document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && newDmModal?.style.display !== 'none') closeNewDm();
});

if (newDmGo) {
  newDmGo.addEventListener('click', async () => {
    const username = dmInput?.value.trim();
    if (!username) return;

    newDmGo.disabled = true;
    newDmGo.textContent = 'Opening…';
    if (dmError) dmError.style.display = 'none';

    try {
      const res = await window.txtr.apiFetch('/api/v1/dm/', {
        method: 'POST',
        body: JSON.stringify({ username }),
      });

      if (res.status === 404 || res.status === 400) {
        if (dmError) dmError.style.display = 'flex';
        return;
      }

      if (!res.ok) throw new Error();

      // Navigate to the conversation
      window.location.href = `/messages/${username}/`;

    } catch {
      window.txtr.showFlash('Could not open conversation.', 'error');
    } finally {
      newDmGo.disabled = false;
      newDmGo.textContent = 'Open chat';
    }
  });
}

// Enter key in username input
if (dmInput) {
  dmInput.addEventListener('keydown', e => {
    if (e.key === 'Enter') newDmGo?.click();
  });
}

/* ════════════════════════════════════════════════════════════
   CONVERSATION PAGE — send, delete, poll
   ════════════════════════════════════════════════════════════ */

const messagesArea = document.getElementById('messages-area');
const msgInput     = document.getElementById('msg-input');
const msgSendBtn   = document.getElementById('msg-send-btn');
const OTHER_USER   = window.OTHER_USERNAME;
const ME           = window.MY_USERNAME;

// Only run conversation logic if we're on the conversation page
if (msgInput) {

  /* ── Auto-grow textarea ───────────────────────────────── */
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

  /* ── Scroll to bottom on load ─────────────────────────── */
  scrollToBottom(false);

  /* ── Poll for new messages every 15s ─────────────────── */
  let lastMsgId = getLastMessageId();
  setInterval(() => pollMessages(lastMsgId), 15000);
}

/* ── Send message ────────────────────────────────────────── */
async function sendMessage() {
  const content = msgInput.value.trim();
  if (!content) return;

  msgSendBtn.disabled = true;
  const savedValue = content;

  // Optimistic: append immediately
  const tempId  = `temp-${Date.now()}`;
  const tempMsg = buildBubble({ id: tempId, content, sender_username: ME, created_at: new Date().toISOString() }, true);
  messagesArea.insertAdjacentHTML('beforeend', tempMsg);
  msgInput.value = '';
  msgInput.style.height = 'auto';
  scrollToBottom();

  try {
    const res = await window.txtr.apiFetch(`/api/v1/dm/${OTHER_USER}/`, {
      method: 'POST',
      body: JSON.stringify({ content: savedValue }),
    });

    if (!res.ok) throw new Error();
    const msg = await res.json();

    // Replace temp bubble with real one (has correct id for deletion)
    const tempEl = document.getElementById(tempId);
    if (tempEl) tempEl.outerHTML = buildBubble(msg, true);

  } catch {
    // Remove temp bubble on failure
    document.getElementById(tempId)?.remove();
    msgInput.value = savedValue;
    msgInput.style.height = 'auto';
    window.txtr.showFlash('Message not sent. Try again.', 'error');
  } finally {
    msgSendBtn.disabled = msgInput.value.trim().length === 0;
  }
}

/* ── Delete message ──────────────────────────────────────── */
window.deleteMessage = async function(msgId, username) {
  if (!confirm('Delete this message?')) return;

  try {
    const res = await window.txtr.apiFetch(`/api/v1/dm/${username}/${msgId}/`, { method: 'DELETE' });
    if (!res.ok) throw new Error();
    document.getElementById(`msg-${msgId}`)?.remove();
  } catch {
    window.txtr.showFlash('Could not delete message.', 'error');
  }
};

/* ── Poll for new messages ───────────────────────────────── */
async function pollMessages(afterId) {
  try {
    const res  = await fetch(`/api/v1/dm/${OTHER_USER}/`);
    const data = await res.json();
    const msgs = (data.results || data).filter(m => m.id > afterId);

    if (msgs.length === 0) return;

    msgs.forEach(msg => {
      if (document.getElementById(`msg-${msg.id}`)) return;
      const isMe = msg.sender_username === ME;
      messagesArea.insertAdjacentHTML('beforeend', buildBubble(msg, isMe));
    });

    scrollToBottom();
    lastMsgId = msgs[msgs.length - 1].id;

  } catch {
    // Silently fail — polling is best-effort
  }
}

/* ── Build message bubble HTML ───────────────────────────── */
function buildBubble(msg, isMe) {
  const avatarHtml = !isMe
    ? (window.OTHER_AVATAR
        ? `<img src="${window.OTHER_AVATAR}" alt="${OTHER_USER}" class="avatar avatar-sm" />`
        : `<div class="avatar-placeholder avatar-sm">${OTHER_USER[0].toUpperCase()}</div>`)
    : '';

  const deleteBtn = isMe
    ? `<button class="msg-delete" onclick="deleteMessage(${msg.id}, '${OTHER_USER}')" title="Delete">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
          <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
       </button>`
    : '';

  const time = new Date(msg.created_at).toLocaleTimeString('en', { hour: '2-digit', minute: '2-digit', hour12: false });

  return `
    <div class="msg-row ${isMe ? 'me' : ''}" id="msg-${msg.id}">
      ${avatarHtml}
      <div>
        <div class="msg-bubble">
          ${escHtml(msg.content)}
          ${deleteBtn}
        </div>
        <div class="msg-time">${time}</div>
      </div>
    </div>`;
}

/* ── Scroll to bottom ────────────────────────────────────── */
function scrollToBottom(smooth = true) {
  if (!messagesArea) return;
  messagesArea.scrollTo({
    top: messagesArea.scrollHeight,
    behavior: smooth ? 'smooth' : 'auto'
  });
}

/* ── Get last message id (for polling) ───────────────────── */
function getLastMessageId() {
  const rows = messagesArea?.querySelectorAll('[id^="msg-"]') || [];
  if (rows.length === 0) return 0;
  const ids = [...rows].map(el => parseInt(el.id.replace('msg-', '') || 0)).filter(Boolean);
  return ids.length ? Math.max(...ids) : 0;
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}