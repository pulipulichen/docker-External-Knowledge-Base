const form = document.getElementById('retrieval-form');
const resultsList = document.getElementById('results-list');
const sidebarNav = document.getElementById('sidebar-nav');
const navQueryItem = document.getElementById('nav-query-item');
const submitBtn = document.getElementById('submit-btn');
const btnText = document.getElementById('btn-text');
const loading = document.getElementById('loading');
const statusContainer = document.getElementById('status-container');
const curlSection = document.getElementById('curl-section');
const curlOutput = document.getElementById('curl-output');

function escapeHtml(unsafe) {
    if (!unsafe) return "";
    return unsafe
        .replace(/&/g, "&")
        .replace(/</g, "<")
        .replace(/>/g, ">")
        .replace(/"/g, "'")
        .replace(/'/g, "&#39;");
}

/**
 * 僅針對特定的 HTML 標籤進行轉義
 * 受影響標籤：<html>, <body>, <title> 及其結束標籤
 * @param {string} content - 需要處理的原始字串
 * @returns {string} - 處理後的字串
 */
const escapeHTMLTags = (content) => {
  if (typeof content !== 'string') {
    return '';
  }

  /**
   * 使用正則表達式匹配特定的標籤
   * < : 匹配左尖括號
   * (\/)? : 匹配選用的斜線（針對結束標籤）
   * (html|body|title) : 匹配指定的標籤名稱
   * > : 匹配右尖括號
   * gi : 全域匹配且不區分大小寫
   */
  const targetTagsRegex = /<(html|body|title|style|script|noscript|\/html|\/body|\/title|\style|\script|\noscript)>/gi;

  console.log(content)

  // 僅對匹配到的特定標籤字串進行內容替換
  const result = content.replace(targetTagsRegex, (match) => {
    return match
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  });

  // console.log(result)

  return result
};

// Fields to persist in localStorage
const persistFields = ['knowledge_id', 'section_name', 'top_k', 'score_threshold', 'query'];

// Load persisted values and fetch knowledge IDs
window.addEventListener('DOMContentLoaded', async () => {
    // 1. Fetch knowledge IDs first
    try {
        const response = await fetch('/knowledge-ids', {
            headers: {
                'Authorization': `Bearer ${API_KEY}`
            }
        });
        if (response.ok) {
            const ids = await response.json();
            const select = document.getElementById('knowledge_id');
            const currentValue = localStorage.getItem('retrieval_knowledge_id');

            while (select.options.length > 1) { select.remove(1); }

            ids.forEach(id => {
                const option = document.createElement('option');
                option.value = id;
                option.textContent = id;
                select.appendChild(option);
            });

            if (currentValue) { select.value = currentValue; }
        }
    } catch (error) {
        console.error('Failed to fetch knowledge IDs:', error);
    }

    // 2. Load other persisted values
    persistFields.forEach(field => {
        if (field === 'knowledge_id') return;
        const value = localStorage.getItem(`retrieval_${field}`);
        if (value !== null) {
            const el = document.getElementById(field);
            if (el) el.value = value;
        }
    });
});

// Save values on change
persistFields.forEach(field => {
    const el = document.getElementById(field);
    if (el) {
        const eventType = el.tagName === 'SELECT' ? 'change' : 'input';
        el.addEventListener(eventType, (e) => {
            localStorage.setItem(`retrieval_${field}`, e.target.value);
        });
    }
});

function generateCurl(payload) {
    const baseUrl = window.location.origin;
    return `curl -X POST "${baseUrl}/retrieval" \\
-H "Content-Type: application/json" \\
-H "Authorization: Bearer ${API_KEY}" \\
-d '${JSON.stringify(payload, null, 2)}'`;
}

function copyCurl() {
    const text = curlOutput.textContent;
    navigator.clipboard.writeText(text).then(() => {
        alert('CURL copied to clipboard!');
    });
}

form.addEventListener('submit', async (e) => {
    e.preventDefault();

    submitBtn.disabled = true;
    btnText.style.display = 'none';
    loading.style.display = 'block';
    resultsList.innerHTML = '<div class="empty-state">Fetching records...</div>';
    statusContainer.innerHTML = '';
    curlSection.style.display = 'none';

    const knowledgeId = document.getElementById('knowledge_id').value;
    const sectionName = document.getElementById('section_name').value;
    const topK = parseInt(document.getElementById('top_k').value);
    const score_threshold = document.getElementById('score_threshold').value;
    const query = document.getElementById('query').value;

    // Update sidebar query item
    const queryPreview = query.length > 15 ? query.substring(0, 15) + '...' : query;
    navQueryItem.querySelector('.nav-text').textContent = `🔍 [${knowledgeId}] ${queryPreview}`;

    // Reset sidebar results
    const resultItems = sidebarNav.querySelectorAll('.nav-item:not(#nav-query-item)');
    resultItems.forEach(item => item.remove());

    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    navQueryItem.classList.add('active');

    const fullKnowledgeId = sectionName ? `${knowledgeId}!${sectionName}` : knowledgeId;

    const payload = {
        knowledge_id: fullKnowledgeId,
        query: query,
        retrieval_setting: {
            top_k: topK,
            score_threshold: score_threshold ? parseFloat(score_threshold) : null
        }
    };

    curlOutput.textContent = generateCurl(payload);
    curlSection.style.display = 'block';

    try {
        const response = await fetch('/retrieval', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_KEY}`
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (response.ok) {
            const records = Array.isArray(data) ? data : (data.records || []);
            displayResults(records);
            updateSidebar(records);
            statusContainer.innerHTML = `<span class="status-badge status-success">Success: ${records.length || 0} records found</span>`;
        } else {
            throw new Error(data.error || 'Failed to fetch results');
        }
    } catch (error) {
        resultsList.innerHTML = `<div class="empty-state" style="color: #ef4444; border-color: #ef4444">Error: ${error.message}</div>`;
        statusContainer.innerHTML = `<span class="status-badge status-error">Error</span>`;
    } finally {
        submitBtn.disabled = false;
        btnText.style.display = 'block';
        loading.style.display = 'none';
    }
});

function updateSidebar(records) {
    records.forEach((record, index) => {
        const content = record.content || record.text || "";
        const preview = content.substring(0, 30) + (content.length > 30 ? "..." : "");
        const score = record.score ? record.score.toFixed(3) : "N/A";

        const navItem = document.createElement('a');
        navItem.href = `#result-${index}`;
        navItem.className = 'nav-item';
        navItem.innerHTML = `
<div class="nav-meta">
<span>Rank #${index + 1}</span>
<span>Score: ${score}</span>
</div>
<span class="nav-text">${escapeHtml(preview) || 'Empty content'}</span>
`;

        navItem.addEventListener('click', (e) => {
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            navItem.classList.add('active');
        });

        sidebarNav.appendChild(navItem);
    });
}

function displayResults(records) {
    if (!records || records.length === 0) {
        resultsList.innerHTML = '<div class="empty-state">No matching records found.</div>';
        return;
    }

    resultsList.innerHTML = records.map((record, index) => {
        const content = record.content || record.text || "";
        let renderedContent = "";

        // Try to parse as JSON first
        try {
            const jsonObj = JSON.parse(content);
            renderedContent = `<pre>${escapeHtml(JSON.stringify(jsonObj, null, 2))}</pre>`;
        } catch (e) {
            // Not JSON, render as Markdown
            renderedContent = marked.parse(content);

            renderedContent = escapeHTMLTags(renderedContent)
        }

        return `
<div class="result-card" id="result-${index}" style="animation: slideIn 0.3s ease forwards; animation-delay: ${index * 0.05}s; opacity: 0;">
<div class="result-meta">
<span>Rank #${index + 1}</span>
${record.score ? `<span>Score: ${record.score.toFixed(4)}</span>` : ''}
</div>
<div class="result-content">${renderedContent}</div>
${record.metadata ? `
<div class="metadata-section">
<span class="metadata-label">Metadata Properties</span>
<pre>${escapeHtml(JSON.stringify(record.metadata, null, 2))}</pre>
</div>
` : ''}
</div>
`;
    }).join('');
}
