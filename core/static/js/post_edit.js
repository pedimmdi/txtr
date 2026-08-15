/* ============================================================
   txtr — post_edit.js
   Character counter and auto-grow for the post edit form
   ============================================================ */

'use strict';

(function () {
  const MAX = 1000;
  const textarea = document.getElementById('edit-post-textarea');
  const counter  = document.getElementById('edit-char-counter');
  const submit   = document.getElementById('edit-post-submit');

  if (!textarea || !counter || !submit) return;

  function update() {
    const remaining = MAX - textarea.value.length;
    counter.textContent = remaining;
    counter.classList.toggle('warn', remaining <= 150 && remaining > 50);
    counter.classList.toggle('danger', remaining <= 50);
    submit.disabled = textarea.value.trim().length === 0 || remaining < 0;
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
  }

  textarea.addEventListener('input', update);
  update();
})();