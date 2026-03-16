// extension/content.js

// This script runs in the context of the email webmail tabs (Gmail/Outlook).
// It looks for opened emails and scans them.

const SCANNED_EMAILS = new Set();

function init() {
    console.log("[Deepscan] Content script initialized.");

    // Set up a MutationObserver to watch for new email nodes being rendered
    // Gmail pushes new emails into the DOM dynamically without page reloads.
    const observer = new MutationObserver(handleDOMChanges);
    observer.observe(document.body, { childList: true, subtree: true });
}

function handleDOMChanges(mutations) {
    // Basic Gmail detection: Look for elements with class 'a3s' or 'ii gt' which usually contain the email body.
    const emailBodies = document.querySelectorAll('.a3s.aiL, .ii.gt');

    emailBodies.forEach(emailNode => {
        // Ensure we only scan an email once per session
        const emailId = emailNode.closest('div[data-message-id]')?.getAttribute('data-message-id') || getHash(emailNode.innerText);

        if (emailId && !SCANNED_EMAILS.has(emailId)) {
            SCANNED_EMAILS.add(emailId);
            processEmail(emailNode);
        }
    });
}

function processEmail(emailNode) {
    const emailText = emailNode.innerText;

    if (emailText.length < 20) return; // Too short to be a real email body

    console.log("[Deepscan] Found new email. Extracting content...");

    // Prepare the container for the Deepscan Banner UI
    const banner = createLoadingBanner();
    emailNode.parentNode.insertBefore(banner, emailNode);

    // Send to background script for analysis
    chrome.runtime.sendMessage(
        { action: "analyze_email", payload: { body: emailText } },
        (response) => {
            if (response && response.success) {
                updateBannerWithResults(banner, response.data);
            } else {
                updateBannerWithError(banner, response?.error || "Unknown error occurred.");
            }
        }
    );
}

function createLoadingBanner() {
    const div = document.createElement("div");
    div.className = "deepscan-banner deepscan-loading";
    div.innerHTML = `
        <div class="deepscan-banner-header">
            <span class="deepscan-title">Deepscan AACS</span>
            <span class="deepscan-status">Scanning Email Content...</span>
        </div>
        <div class="deepscan-progress"></div>
    `;
    return div;
}

function updateBannerWithResults(banner, data) {
    banner.classList.remove("deepscan-loading");

    const isPhishing = data.phishing_score > 0.6;
    const isAiGenerated = data.ai_probability > 0.6;

    let alertClass = "deepscan-safe";
    if (isPhishing || isAiGenerated) {
        alertClass = "deepscan-danger";
    } else if (data.phishing_score > 0.3 || data.ai_probability > 0.3) {
        alertClass = "deepscan-warning";
    }

    banner.classList.add(alertClass);

    banner.innerHTML = `
        <div class="deepscan-banner-header">
            <span class="deepscan-title">Deepscan AACS Report</span>
            <span class="deepscan-status ${alertClass}">${alertClass === 'deepscan-safe' ? 'SAFE' : alertClass === 'deepscan-warning' ? 'SUSPICIOUS' : 'HIGH RISK'}</span>
        </div>
        <div class="deepscan-banner-content">
            <div class="deepscan-metric">
                <span class="deepscan-label">Phishing Risk:</span>
                <span class="deepscan-value font-mono">${(data.phishing_score * 100).toFixed(1)}%</span>
            </div>
            <div class="deepscan-metric">
                <span class="deepscan-label">AI Generated:</span>
                <span class="deepscan-value font-mono">${(data.ai_probability * 100).toFixed(1)}%</span>
            </div>
            <div class="deepscan-reasons">
                ${data.analysis.map(reason => `<span>• ${reason}</span>`).join('')}
            </div>
        </div>
    `;
}

function updateBannerWithError(banner, errorMsg) {
    banner.classList.remove("deepscan-loading");
    banner.classList.add("deepscan-error");
    banner.innerHTML = `
        <div class="deepscan-banner-header">
            <span class="deepscan-title">Deepscan AACS Error</span>
        </div>
        <div class="deepscan-banner-content">
            <p>Failed to analyze email: ${errorMsg}</p>
        </div>
    `;
}

// Simple hash function for deduplication if message-id is missing
function getHash(str) {
    let hash = 0;
    for (let i = 0, len = str.length; i < len; i++) {
        let chr = str.charCodeAt(i);
        hash = (hash << 5) - hash + chr;
        hash |= 0;
    }
    return hash.toString();
}

// Start
init();
