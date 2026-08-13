/* ============================================================
   txtr — explore.js
   Follow toggle on explore page
   ============================================================ */

'use strict';

window.handleFollow = async function(btn) {
  const username    = btn.dataset.username;
  const isFollowing = btn.dataset.following === 'true';

  btn.disabled = true;

  try {
    const res = await window.txtr.apiFetch(
      `/api/v1/accounts/follow/${username}/`,
      { method: 'POST' }
    );
    if (!res.ok) throw new Error();
    const data = await res.json();

    const nowFollowing = data.is_following;
    btn.dataset.following = nowFollowing;
    btn.textContent = nowFollowing ? 'Following' : 'Follow';
    btn.classList.toggle('btn-primary', !nowFollowing);
    btn.classList.toggle('btn-outline',  nowFollowing);

  } catch {
    window.txtr.showFlash('Could not update follow status.', 'error');
  } finally {
    btn.disabled = false;
  }
};

/* ── Hashtag posts page ──────────────────────────────────── */
// Attach like/bookmark/repost handlers for hashtag post lists too
document.addEventListener('DOMContentLoaded', () => {
  window.txtr.attachLikeHandlers();
  window.txtr.attachBookmarkHandlers();
  window.txtr.attachRepostHandlers();
});