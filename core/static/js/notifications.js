/* ============================================================
   txtr — notifications.js
   Mark as read on click, mark all as read
   ============================================================ */

'use strict';

/* ── Mark single notification as read on click ───────────── */
document.querySelectorAll('.notif-item.unread').forEach(item => {
  item.addEventListener('click', async () => {
    const notifId = item.dataset.notifId;

    try {
      await window.txtr.apiFetch(
        `/api/v1/notifications/${notifId}/read/`,
        { method: 'POST' }
      );
      item.classList.remove('unread');
      item.querySelector('.notif-unread-dot')?.remove();

      // Decrement badge in nav
      const badges = document.querySelectorAll('.notif-badge');
      badges.forEach(badge => {
        const current = parseInt(badge.textContent || 0);
        const next    = Math.max(0, current - 1);
        badge.textContent = next;
        if (next === 0) badge.style.display = 'none';
      });

    } catch {
      // Silently fail — navigation still works
    }
  });
});

/* ── Mark all as read ────────────────────────────────────── */
const markAllBtn = document.getElementById('mark-all-read');

if (markAllBtn) {
  markAllBtn.addEventListener('click', async () => {
    try {
      const res = await window.txtr.apiFetch(
        '/api/v1/notifications/read-all/',
        { method: 'POST' }
      );
      if (!res.ok) throw new Error();

      // Remove all unread styles
      document.querySelectorAll('.notif-item.unread').forEach(item => {
        item.classList.remove('unread');
        item.querySelector('.notif-unread-dot')?.remove();
      });

      // Zero out all badges
      document.querySelectorAll('.notif-badge').forEach(badge => {
        badge.textContent = '0';
        badge.style.display = 'none';
      });

      markAllBtn.style.opacity = '0.4';
      markAllBtn.style.pointerEvents = 'none';
      window.txtr.showFlash('All notifications marked as read.', 'info');

    } catch {
      window.txtr.showFlash('Something went wrong.', 'error');
    }
  });
}