const form = document.getElementById('reset-form');
const submitBtn = document.getElementById('submit-btn');
const btnText = document.getElementById('btn-text');
const loading = document.getElementById('loading');
const statusContainer = document.getElementById('status-container');
const curlSection = document.getElementById('curl-section');
const curlOutput = document.getElementById('curl-output');
const responseOutput = document.getElementById('response-output');

const API_KEY_STORAGE_KEY = 'reset_demo_api_key';
const KNOWLEDGE_ID_MANUAL_KEY = 'reset_demo_knowledge_id_manual';

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

function restoreKnowledgeIdSelect() {
    const select = document.getElementById('knowledge_id');
    if (!select) return;
    const currentValue = localStorage.getItem('reset_demo_knowledge_id');
    if (currentValue && [...select.options].some((o) => o.value === currentValue)) {
        select.value = currentValue;
    }
}

function getKnowledgeIdBase() {
    const manualEl = document.getElementById('knowledge_id_manual');
    const manual = manualEl && manualEl.value ? manualEl.value.trim() : '';
    if (manual) {
        return manual;
    }
    const select = document.getElementById('knowledge_id');
    const fromSelect = select && select.value ? select.value.trim() : '';
    return fromSelect;
}

window.addEventListener('DOMContentLoaded', () => {
    const apiKeyInput = document.getElementById('api_key');
    const storedKey = localStorage.getItem(API_KEY_STORAGE_KEY);
    if (storedKey !== null && apiKeyInput) {
        apiKeyInput.value = storedKey;
    }
    updateApiKeyStatus();
    restoreKnowledgeIdSelect();

    const manualKidEl = document.getElementById('knowledge_id_manual');
    const storedManualKid = localStorage.getItem(KNOWLEDGE_ID_MANUAL_KEY);
    if (storedManualKid !== null && manualKidEl) {
        manualKidEl.value = storedManualKid;
    }
    if (manualKidEl) {
        manualKidEl.addEventListener('input', (e) => {
            const v = e.target.value;
            if (v) {
                localStorage.setItem(KNOWLEDGE_ID_MANUAL_KEY, v);
            } else {
                localStorage.removeItem(KNOWLEDGE_ID_MANUAL_KEY);
            }
        });
    }

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

    const sectionEl = document.getElementById('section_name');
    const storedSection = localStorage.getItem('reset_demo_section_name');
    if (storedSection !== null && sectionEl) {
        sectionEl.value = storedSection;
    }
    if (sectionEl) {
        sectionEl.addEventListener('input', (e) => {
            localStorage.setItem('reset_demo_section_name', e.target.value);
        });
    }

    const kidSelect = document.getElementById('knowledge_id');
    if (kidSelect) {
        kidSelect.addEventListener('change', (e) => {
            localStorage.setItem('reset_demo_knowledge_id', e.target.value);
        });
    }
});

function generateCurl(body) {
    const baseUrl = window.location.origin;
    return `curl -X POST "${baseUrl}/reset" \\
-H "Content-Type: application/json" \\
-H "Authorization: Bearer ${getApiKey()}" \\
-d '${JSON.stringify(body)}'`;
}

function copyCurl() {
    const text = curlOutput.textContent;
    navigator.clipboard.writeText(text).then(() => {
        alert('CURL copied to clipboard!');
    });
}

form.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (!getApiKey()) {
        responseOutput.textContent = 'Enter your API key first';
        responseOutput.className = 'empty-state';
        responseOutput.style.color = '#ef4444';
        statusContainer.innerHTML = '<span class="status-badge status-error">Missing API key</span>';
        return;
    }

    const knowledgeId = getKnowledgeIdBase();
    if (!knowledgeId) {
        responseOutput.textContent = 'Select a Knowledge ID from the list or enter one in the manual field';
        responseOutput.className = 'empty-state';
        responseOutput.style.color = '#ef4444';
        statusContainer.innerHTML = '<span class="status-badge status-error">Missing Knowledge ID</span>';
        return;
    }

    const sectionName = document.getElementById('section_name').value;
    const fullKnowledgeId = sectionName ? `${knowledgeId}!${sectionName}` : knowledgeId;

    const confirmed = window.confirm(
        `Reset knowledge base "${fullKnowledgeId}"? This removes the Weaviate collection and local markdown / index-time artifacts.`
    );
    if (!confirmed) {
        return;
    }

    const body = { knowledge_id: fullKnowledgeId };

    submitBtn.disabled = true;
    btnText.style.display = 'none';
    loading.style.display = 'block';
    statusContainer.innerHTML = '';
    curlOutput.textContent = generateCurl(body);
    curlSection.style.display = 'block';
    responseOutput.textContent = 'Requesting...';
    responseOutput.className = '';
    responseOutput.style.color = '';

    try {
        const response = await fetch('/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getApiKey()}`
            },
            body: JSON.stringify(body)
        });

        const data = await response.json();
        responseOutput.textContent = JSON.stringify(data, null, 2);

        if (response.ok) {
            statusContainer.innerHTML = '<span class="status-badge status-success">Success</span>';
        } else {
            statusContainer.innerHTML = `<span class="status-badge status-error">HTTP ${response.status}</span>`;
        }
    } catch (error) {
        responseOutput.textContent = error.message || String(error);
        statusContainer.innerHTML = '<span class="status-badge status-error">Error</span>';
    } finally {
        submitBtn.disabled = false;
        btnText.style.display = 'block';
        loading.style.display = 'none';
    }
});
