const tabs = document.querySelectorAll('.tab');
const panels = document.querySelectorAll('.tab-panel');
const textInput = document.getElementById('textInput');
const fileInput = document.getElementById('fileInput');
const fileName = document.getElementById('fileName');
const analyzeBtn = document.getElementById('analyzeBtn');
const errorMsg = document.getElementById('errorMsg');
const emptyState = document.getElementById('emptyState');
const resultEl = document.getElementById('result');

let activeTab = 'text';

tabs.forEach(tab => {
  tab.addEventListener('click', () => {
    tabs.forEach(t => { t.classList.remove('active'); t.setAttribute('aria-selected', 'false'); });
    tab.classList.add('active');
    tab.setAttribute('aria-selected', 'true');
    activeTab = tab.dataset.tab;
    panels.forEach(p => p.classList.toggle('hidden', p.dataset.panel !== activeTab));
  });
});

fileInput.addEventListener('change', () => {
  fileName.textContent = fileInput.files.length ? fileInput.files[0].name : 'No file chosen';
});

// Minimal markdown -> HTML renderer for the fixed section structure we expect back.
function renderMarkdown(raw) {
  const lines = raw.split('\n');
  let html = '';
  let inList = false;

  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('## ')) {
      if (inList) { html += '</ul>'; inList = false; }
      html += `<h2>${escapeHtml(trimmed.slice(3))}</h2>`;
    } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      if (!inList) { html += '<ul>'; inList = true; }
      html += `<li>${inlineFormat(escapeHtml(trimmed.slice(2)))}</li>`;
    } else if (trimmed === '') {
      if (inList) { html += '</ul>'; inList = false; }
    } else {
      if (inList) { html += '</ul>'; inList = false; }
      html += `<p>${inlineFormat(escapeHtml(trimmed))}</p>`;
    }
  }
  if (inList) html += '</ul>';
  return html;
}

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function inlineFormat(str) {
  return str.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
}

async function analyze() {
  errorMsg.textContent = '';

  const hasText = textInput.value.trim().length > 0;
  const hasFile = fileInput.files.length > 0;

  if (activeTab === 'text' && !hasText) {
    errorMsg.textContent = 'Paste some text first, or switch to the upload tab.';
    return;
  }
  if (activeTab === 'file' && !hasFile) {
    errorMsg.textContent = 'Choose a PDF or image first, or switch to the text tab.';
    return;
  }

  const formData = new FormData();
  if (activeTab === 'text') {
    formData.append('text', textInput.value.trim());
  } else {
    formData.append('file', fileInput.files[0]);
    if (hasText) formData.append('text', textInput.value.trim());
  }

  analyzeBtn.disabled = true;
  analyzeBtn.querySelector('.btn-label').textContent = 'Reading it over...';
  emptyState.hidden = true;
  resultEl.hidden = false;
  resultEl.innerHTML = '<span class="cursor-blink"></span>';

  try {
    const res = await fetch('/api/analyze', { method: 'POST', body: formData });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Request failed (${res.status})`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let accumulated = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      accumulated += decoder.decode(value, { stream: true });
      resultEl.innerHTML = renderMarkdown(accumulated) + '<span class="cursor-blink"></span>';
      resultEl.scrollTop = resultEl.scrollHeight;
    }
    resultEl.innerHTML = renderMarkdown(accumulated);
  } catch (err) {
    errorMsg.textContent = err.message || 'Something went wrong. Please try again.';
    emptyState.hidden = false;
    resultEl.hidden = true;
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.querySelector('.btn-label').textContent = 'Break it down';
  }
}

analyzeBtn.addEventListener('click', analyze);
