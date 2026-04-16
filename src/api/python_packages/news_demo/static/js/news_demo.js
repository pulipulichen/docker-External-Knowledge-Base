const form = document.getElementById('news-form');
const resultsList = document.getElementById('results-list');
const sidebarNav = document.getElementById('sidebar-nav');
const navQueryItem = document.getElementById('nav-query-item');
const submitBtn = document.getElementById('submit-btn');
const sidebarExecuteBtn = document.getElementById('sidebar-execute-btn');
const btnText = document.getElementById('btn-text');
const loading = document.getElementById('loading');
const statusContainer = document.getElementById('status-container');
const curlSection = document.getElementById('curl-section');
const curlOutput = document.getElementById('curl-output');
const copyCurlBtn = document.getElementById('copy-curl-btn');

const API_KEY_STORAGE_KEY = 'news_api_key';
const persistFields = ['query', 'hl', 'gl', 'ceid', 'limit'];
const persistCheckboxes = ['fulltext', 'disable_cache'];

function escapeHtml(unsafe) {
    if (!unsafe) return "";
    return String(unsafe)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
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

function normalizeLimit(s, fallback, maxCap) {
    if (s === null || s === undefined) return fallback;
    const v = parseInt(String(s), 10);
    if (!Number.isFinite(v) || v < 1) return fallback;
    return Math.min(v, maxCap);
}

function generateCurl(payload) {
    const baseUrl = window.location.origin;
    return `curl -X POST "${baseUrl}/news" \\\n` +
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

const NEWS_LIMIT_MAX = 50;

function buildPayloadFromForm() {
    const query = normalizeOptionalString(document.getElementById('query').value);
    const hl = normalizeOptionalString(document.getElementById('hl').value) || 'zh-TW';
    const gl = normalizeOptionalString(document.getElementById('gl').value) || 'TW';
    const ceid = normalizeOptionalString(document.getElementById('ceid').value) || 'TW:zh-Hant';
    const limit = normalizeLimit(document.getElementById('limit').value, 5, NEWS_LIMIT_MAX);
    const fulltext = !!document.getElementById('fulltext').checked;
    const disable_cache = !!document.getElementById('disable_cache').checked;

    return {
        query,
        hl,
        gl,
        ceid,
        limit,
        fulltext,
        disable_cache,
    };
}

function resetSidebarResults() {
    const resultItems = sidebarNav.querySelectorAll('.nav-item:not(#nav-query-item)');
    resultItems.forEach(item => item.remove());
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    navQueryItem.classList.add('active');
}

function updateSidebar(items) {
    items.forEach((item, index) => {
        const title = item.title || item.url || `Article #${index + 1}`;
        const when = item.pubDate ? String(item.pubDate) : '';

        const navItem = document.createElement('a');
        navItem.href = `#result-${index}`;
        navItem.className = 'nav-item';
        navItem.innerHTML = `
<div class="nav-meta">
<span>#${index + 1}</span>
<span>${escapeHtml(when)}</span>
</div>
<span class="nav-text">${escapeHtml(title)}</span>
`;
        navItem.addEventListener('click', () => {
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            navItem.classList.add('active');
        });
        sidebarNav.appendChild(navItem);
    });
}

function renderResultContent(item) {
    const content = item.content || "";
    if (!content) return '<div class="result-content"><em>No fulltext (RSS title only, or Mercury empty)</em></div>';
    if (window.marked) {
        const md = window.marked.parse(String(content));
        return `<div class="result-content">${escapeHTMLTags(md)}</div>`;
    }
    return `<div class="result-content"><pre>${escapeHtml(content)}</pre></div>`;
}

function displayResults(items) {
    if (!items || items.length === 0) {
        resultsList.innerHTML = '<div class="empty-state">No articles.</div>';
        return;
    }

    resultsList.innerHTML = items.map((item, index) => {
        const title = item.title || item.url || `Article #${index + 1}`;
        const url = item.url || '';
        const pubDate = item.pubDate ? String(item.pubDate) : '';

        return `
<div class="result-card" id="result-${index}">
  <div class="result-meta">
    <span>#${index + 1}</span>
    ${pubDate ? `<span>${escapeHtml(pubDate)}</span>` : ''}
  </div>
  <div class="result-title">
    ${url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(title)}</a>` : escapeHtml(title)}
  </div>
  ${renderResultContent(item)}
  <details style="margin-top: 1rem;">
    <summary style="cursor: pointer; color: var(--text-dim);">Raw JSON</summary>
    <pre>${escapeHtml(JSON.stringify(item, null, 2))}</pre>
  </details>
</div>
`;
    }).join('');
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
        const value = localStorage.getItem(`news_${field}`);
        if (value !== null) {
            const el = document.getElementById(field);
            if (el) el.value = value;
        }
    });
    persistCheckboxes.forEach((id) => {
        const el = document.getElementById(id);
        const stored = localStorage.getItem(`news_${id}`);
        if (el && stored !== null) {
            el.checked = stored === '1';
        }
    });
});

persistFields.forEach((field) => {
    const el = document.getElementById(field);
    if (el) {
        const eventType = el.tagName === 'SELECT' ? 'change' : 'input';
        el.addEventListener(eventType, (e) => {
            localStorage.setItem(`news_${field}`, e.target.value);
        });
    }
});

persistCheckboxes.forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
        el.addEventListener('change', () => {
            localStorage.setItem(`news_${id}`, el.checked ? '1' : '0');
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
    if (!payload.query) {
        resultsList.innerHTML =
            '<div class="empty-state" style="color: #ef4444;">Query is required</div>';
        statusContainer.innerHTML = '<span class="status-badge status-error">Invalid query</span>';
        return;
    }

    setCurl(payload);

    const queryText = payload.query || '';
    const queryPreview = queryText.length > 18 ? queryText.substring(0, 18) + '...' : queryText;
    const navText = navQueryItem.querySelector('.nav-text');
    navText.textContent = `📰 ${queryPreview || 'New query'}`;
    navText.title = queryText;

    resetSidebarResults();
    setLoadingState(true);
    resultsList.innerHTML = '<div class="empty-state">Loading…</div>';
    statusContainer.innerHTML = '';

    try {
        const response = await fetch('/news', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getApiKey()}`,
            },
            body: JSON.stringify(payload),
        });

        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(data.error || data.detail || `Request failed (${response.status})`);
        }

        const items = Array.isArray(data) ? data : [];
        displayResults(items);
        updateSidebar(items);
        statusContainer.innerHTML =
            `<span class="status-badge status-success">Success: ${items.length} article(s)</span>`;
    } catch (err) {
        resultsList.innerHTML = `<div class="empty-state" style="color: #ef4444; border-color: #ef4444">Error: ${escapeHtml(err.message || 'Network error')}</div>`;
        statusContainer.innerHTML = `<span class="status-badge status-error">Error</span>`;
    } finally {
        setLoadingState(false);
    }
});
