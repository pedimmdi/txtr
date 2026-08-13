/* ============================================================
   txtr — profile.js
   Tab switching, follow toggle, edit modal, avatar preview
   ============================================================ */

'use strict';

/* ── Tabs ────────────────────────────────────────────────── */
document.querySelectorAll('.profile-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    // Deactivate all tabs and hide all panels
    document.querySelectorAll('.profile-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.style.display = 'none');

    // Activate clicked tab and show its panel
    tab.classList.add('active');
    const panel = document.getElementById(`tab-${tab.dataset.tab}`);
    if (panel) panel.style.display = 'block';
  });
});

/* ── Follow Toggle ───────────────────────────────────────── */
const followBtn = document.getElementById('follow-btn');

if (followBtn) {
  followBtn.addEventListener('click', async () => {
    const username    = followBtn.dataset.username;
    const isFollowing = followBtn.dataset.following === 'true';

    followBtn.disabled = true;

    try {
      const res = await window.txtr.apiFetch(
        `/api/v1/accounts/follow/${username}/`,
        { method: 'POST' }
      );
      if (!res.ok) throw new Error();
      const data = await res.json();

      const nowFollowing = data.is_following;
      followBtn.dataset.following = nowFollowing;
      followBtn.textContent = nowFollowing ? 'Following' : 'Follow';
      followBtn.classList.toggle('btn-primary', !nowFollowing);
      followBtn.classList.toggle('btn-outline',  nowFollowing);

      // Update followers count in stats
      const statEls = document.querySelectorAll('.profile-stat-count');
      // statEls[0] = following, [1] = followers
      if (statEls[1]) {
        const current = parseInt(statEls[1].textContent || 0);
        statEls[1].textContent = nowFollowing ? current + 1 : Math.max(0, current - 1);
      }

      window.txtr.showFlash(
        nowFollowing ? `Following ${username}` : `Unfollowed ${username}`,
        'info'
      );

    } catch {
      window.txtr.showFlash('Could not update follow status.', 'error');
    } finally {
      followBtn.disabled = false;
    }
  });
}

/* ── Edit Profile Modal ──────────────────────────────────── */
const editBtn   = document.getElementById('edit-profile-btn');
const modal     = document.getElementById('edit-modal');
const closeBtn  = document.getElementById('edit-modal-close');
const cancelBtn = document.getElementById('edit-cancel-btn');

function openModal() {
  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  modal.style.display = 'none';
  document.body.style.overflow = '';
}

if (editBtn)   editBtn.addEventListener('click', openModal);
if (closeBtn)  closeBtn.addEventListener('click', closeModal);
if (cancelBtn) cancelBtn.addEventListener('click', closeModal);

// Close on overlay click
if (modal) {
  modal.addEventListener('click', e => {
    if (e.target === modal) closeModal();
  });
}

// Close on Escape
document.addEventListener('keydown', e => {
  if (e.key === 'Escape' && modal && modal.style.display !== 'none') closeModal();
});

/* ── Avatar Preview ──────────────────────────────────────── */
window.previewAvatar = function(input) {
  const file = input.files?.[0];
  if (!file) return;

  if (file.size > 2 * 1024 * 1024) {
    window.txtr.showFlash('Image must be under 2MB.', 'error');
    input.value = '';
    return;
  }

  const reader = new FileReader();
  reader.onload = e => {
    const preview = document.getElementById('avatar-preview');
    if (!preview) return;

    // Replace placeholder div with img if needed
    if (preview.tagName !== 'IMG') {
      const img = document.createElement('img');
      img.id        = 'avatar-preview';
      img.className = 'avatar-upload-preview';
      img.alt       = '';
      preview.replaceWith(img);
    }
    document.getElementById('avatar-preview').src = e.target.result;
  };
  reader.readAsDataURL(file);
};

/* ── Hover effect on "Following" button → show "Unfollow" ── */
if (followBtn && followBtn.dataset.following === 'true') {
  followBtn.addEventListener('mouseenter', () => {
    followBtn.textContent = 'Unfollow';
    followBtn.classList.add('btn-danger');
    followBtn.classList.remove('btn-outline');
  });

  followBtn.addEventListener('mouseleave', () => {
    if (followBtn.dataset.following === 'true') {
      followBtn.textContent = 'Following';
      followBtn.classList.remove('btn-danger');
      followBtn.classList.add('btn-outline');
    }
  });
}