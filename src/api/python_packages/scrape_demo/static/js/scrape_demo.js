const form = document.getElementById('scrape-form');
const resultsList = document.getElementById('results-list');
const navQueryItem = document.getElementById('nav-query-item');
const submitBtn = document.getElementById('submit-btn');
const sidebarExecuteBtn = document.getElementById('sidebar-execute-btn');
const btnText = document.getElementById('btn-text');
const loading = document.getElementById('loading');
const statusContainer = document.getElementById('status-container');
const curlSection = document.getElementById('curl-section');
const curlOutput = document.getElementById('curl-output');
const copyCurlBtn = document.getElementById('copy-curl-btn');

const API_KEY_STORAGE_KEY = 'scrape_api_key';
const persistFields = ['url', 'contentType', 'headers'];

function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return String(unsafe)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function escapeHTMLTags(content) {
    if (typeof content !== 'string') return '';
    const targetTagsRegex = /<(html|body|title|style|script|noscript|\/html|\/body|\/title|\/style|\/script|\/noscript)>/gi;
    return content.replace(targetTagsRegex, (match) => {
        return match.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    });
}

function getApiKey() {
    const el = document.getElementById('api_key');
    return el && el.value ? el.value.trim() : '';
}

function updateApiKeyStatus() {
    const badge = document.getElementById('api-key-status');
    if (!badge) return;
    if (!getApiKey()) {
        badge.textContent = 'Not set';
        badge.className = 'status-badge status-muted';
    } else {
        badge.textContent = 'Saved locally';
        badge.className = 'status-badge status-success';
    }
}

function normalizeOptionalString(s) {
    if (s === null || s === undefined) return null;
    const v = String(s).trim();
    return v.length ? v : null;
}

function buildPayloadFromForm() {
    const url = normalizeOptionalString(document.getElementById('url').value);
    const contentTypeRaw = document.getElementById('contentType').value;
    const contentType = normalizeOptionalString(contentTypeRaw);
    const headers = normalizeOptionalString(document.getElementById('headers').value);

    const payload = { url };
    if (contentType) payload.contentType = contentType;
    if (headers) payload.headers = headers;
    return payload;
}

function generateCurl(payload) {
    const baseUrl = window.location.origin;
    return `curl -X POST "${baseUrl}/scrape" \\\n` +
        `-H "Content-Type: application/json" \\\n` +
        `-H "Authorization: Bearer ${getApiKey()}" \\\n` +
        `-d '${JSON.stringify(payload, null, 2)}'`;
}

function setCurl(payload) {
    if (!curlOutput || !curlSection) return;
    curlOutput.textContent = generateCurl(payload);
    curlSection.style.display = 'block';
}

function setLoadingState(isLoading) {
    submitBtn.disabled = isLoading;
    if (sidebarExecuteBtn) sidebarExecuteBtn.disabled = isLoading;
    btnText.style.display = isLoading ? 'none' : 'block';
    loading.style.display = isLoading ? 'block' : 'none';
}

function renderBodyContent(data) {
    const content = data.content;
    if (content === undefined || content === null || content === '') {
        return '<div class="result-content"><em>No content field in response</em></div>';
    }
    if (window.marked && typeof data.content === 'string') {
        const md = window.marked.parse(String(data.content));
        return `<div class="result-content">${escapeHTMLTags(md)}</div>`;
    }
    return `<div class="result-content"><pre>${escapeHtml(JSON.stringify(data.content, null, 2))}</pre></div>`;
}

function displaySuccess(data) {
    const title = data.title || data.url || 'Scrape result';
    const url = data.url || '';
    const author = data.author ? String(data.author) : '';
    const datePublished = data.date_published ? String(data.date_published) : '';

    resultsList.innerHTML = `
<div class="result-card" id="result-0">
  <div class="result-meta">
    ${author ? `<span>${escapeHtml(author)}</span>` : ''}
    ${datePublished ? `<span>${escapeHtml(datePublished)}</span>` : ''}
  </div>
  <div class="result-title">
    ${url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(title)}</a>` : escapeHtml(title)}
  </div>
  ${renderBodyContent(data)}
  <details style="margin-top: 1rem;">
    <summary style="cursor: pointer; color: var(--text-dim);">Raw JSON</summary>
    <pre>${escapeHtml(JSON.stringify(data, null, 2))}</pre>
  </details>
</div>`;
}

function displayError(status, data) {
    const msg = (data && (data.error || data.detail)) ? (data.error || data.detail) : `HTTP ${status}`;
    resultsList.innerHTML = `
<div class="result-card" style="border-color: rgba(239, 68, 68, 0.4);">
  <div class="result-title" style="color: #ef4444;">Request failed</div>
  <pre>${escapeHtml(typeof data === 'object' ? JSON.stringify(data, null, 2) : String(data))}</pre>
  <p class="result-content" style="margin-top: 0.75rem;">${escapeHtml(String(msg))}</p>
</div>`;
}

if (sidebarExecuteBtn && form) {
    sidebarExecuteBtn.addEventListener('click', () => form.requestSubmit());
}

if (copyCurlBtn && curlOutput) {
    copyCurlBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(curlOutput.textContent || '').then(() => {
            alert('cURL copied to clipboard!');
        });
    });
}

window.addEventListener('DOMContentLoaded', () => {
    const apiKeyInput = document.getElementById('api_key');
    const storedKey = localStorage.getItem(API_KEY_STORAGE_KEY);
    if (storedKey !== null && apiKeyInput) {
        apiKeyInput.value = storedKey;
    }
    updateApiKeyStatus();

    if (apiKeyInput) {
        apiKeyInput.addEventListener('input', () => {
            const v = apiKeyInput.value;
            if (v) {
                localStorage.setItem(API_KEY_STORAGE_KEY, v);
            } else {
                localStorage.removeItem(API_KEY_STORAGE_KEY);
            }
            updateApiKeyStatus();
        });
    }

    persistFields.forEach((field) => {
        const value = localStorage.getItem(`scrape_${field}`);
        if (value !== null) {
            const el = document.getElementById(field);
            if (el) el.value = value;
        }
    });
});

persistFields.forEach((field) => {
    const el = document.getElementById(field);
    if (el) {
        el.addEventListener('input', (e) => {
            localStorage.setItem(`scrape_${field}`, e.target.value);
        });
    }
});

form.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!getApiKey()) {
        resultsList.innerHTML =
            '<div class="empty-state" style="color: #ef4444;">Enter your API key first</div>';
        statusContainer.innerHTML = '<span class="status-badge status-error">Missing API key</span>';
        return;
    }

    const payload = buildPayloadFromForm();
    if (!payload.url) {
        resultsList.innerHTML =
            '<div class="empty-state" style="color: #ef4444;">Enter a valid URL</div>';
        statusContainer.innerHTML = '<span class="status-badge status-error">Missing URL</span>';
        return;
    }

    setCurl(payload);

    const urlPreview = payload.url.length > 28 ? payload.url.substring(0, 28) + '…' : payload.url;
    const navText = navQueryItem.querySelector('.nav-text');
    navText.textContent = `📄 ${urlPreview}`;
    navText.title = payload.url;

    setLoadingState(true);
    resultsList.innerHTML = '<div class="empty-state">Calling Mercury parser…</div>';
    statusContainer.innerHTML = '';

    try {
        const response = await fetch('/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getApiKey()}`,
            },
            body: JSON.stringify(payload),
        });

        const data = await response.json().catch(() => ({}));

        if (response.ok) {
            displaySuccess(data);
            statusContainer.innerHTML =
                '<span class="status-badge status-success">Success</span>';
        } else {
            displayError(response.status, data);
            statusContainer.innerHTML =
                `<span class="status-badge status-error">HTTP ${response.status}</span>`;
        }
    } catch (err) {
        resultsList.innerHTML =
            `<div class="empty-state" style="color: #ef4444; border-color: #ef4444">Error: ${escapeHtml(err.message || 'Network error')}</div>`;
        statusContainer.innerHTML = '<span class="status-badge status-error">Error</span>';
    } finally {
        setLoadingState(false);
    }
});
