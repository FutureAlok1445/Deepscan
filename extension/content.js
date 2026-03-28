// extension/content.js

// This script runs in the context of the email webmail tabs (Gmail/Outlook).
// It looks for opened emails and scans them.

const SCANNED_EMAILS = new Set();

function init() {
    console.log("[Deepscan] Content script initialized.");

    // Inject the global screenshot button with menu
    createScreenshotMenu();

    // Set up a MutationObserver to watch for new email nodes being rendered
    // Gmail pushes new emails into the DOM dynamically without page reloads.
    const observer = new MutationObserver(handleDOMChanges);
    observer.observe(document.body, { childList: true, subtree: true });
}

function createScreenshotMenu() {
    if (document.getElementById("deepscan-fab-container")) return;

    const container = document.createElement("div");
    container.id = "deepscan-fab-container";
    container.className = "deepscan-fab-container";

    const menu = document.createElement("div");
    menu.className = "deepscan-menu";

    const btnPartial = document.createElement("div");
    btnPartial.className = "deepscan-menu-item";
    btnPartial.innerText = "Select Area [Target]";
    btnPartial.onclick = startSelection;

    const btnFull = document.createElement("div");
    btnFull.className = "deepscan-menu-item";
    btnFull.innerText = "Full Page [Scan]";
    btnFull.onclick = captureFullPage;

    menu.appendChild(btnPartial);
    menu.appendChild(btnFull);

    const fab = document.createElement("button");
    fab.id = "deepscan-fab";
    fab.className = "deepscan-screenshot-btn";
    fab.title = "Deepscan Analysis Tools";
    fab.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 7V5a2 2 0 0 1 2-2h2"></path>
            <path d="M17 3h2a2 2 0 0 1 2 2v2"></path>
            <path d="M21 17v2a2 2 0 0 1-2 2h-2"></path>
            <path d="M7 21H5a2 2 0 0 1-2-2v-2"></path>
            <circle cx="12" cy="12" r="3"></circle>
            <path d="m19 19-3-3"></path>
        </svg>
    `;

    container.appendChild(menu);
    container.appendChild(fab);
    document.body.appendChild(container);
}

function captureFullPage() {
    const container = document.getElementById("deepscan-fab-container");
    container.style.display = 'none';

    setTimeout(() => {
        chrome.runtime.sendMessage({ action: "capture_and_analyze" }, (response) => {
            container.style.display = 'block';
            if (response && response.error) alert("DeepScan Error: " + response.error);
        });
    }, 100);
}

function startSelection() {
    const container = document.getElementById("deepscan-fab-container");
    container.style.display = 'none';

    const overlay = document.createElement("div");
    overlay.className = "deepscan-selection-overlay";
    
    const hint = document.createElement("div");
    hint.className = "deepscan-selection-hint";
    hint.innerText = "Drag to select area for Deepscan analysis (ESC to cancel)";
    
    document.body.appendChild(overlay);
    document.body.appendChild(hint);

    let startX, startY, isDragging = false;
    const box = document.createElement("div");
    box.className = "deepscan-selection-box";
    overlay.appendChild(box);

    const cleanup = () => {
        overlay.remove();
        hint.remove();
        container.style.display = 'block';
        document.removeEventListener("keydown", onEsc);
    };

    const onEsc = (e) => { if (e.key === "Escape") cleanup(); };
    document.addEventListener("keydown", onEsc);

    overlay.onmousedown = (e) => {
        startX = e.clientX;
        startY = e.clientY;
        isDragging = true;
        box.style.left = startX + "px";
        box.style.top = startY + "px";
        box.style.width = "0px";
        box.style.height = "0px";
    };

    overlay.onmousemove = (e) => {
        if (!isDragging) return;
        const currentX = e.clientX;
        const currentY = e.clientY;
        
        const x = Math.min(startX, currentX);
        const y = Math.min(startY, currentY);
        const w = Math.abs(startX - currentX);
        const h = Math.abs(startY - currentY);
        
        box.style.left = x + "px";
        box.style.top = y + "px";
        box.style.width = w + "px";
        box.style.height = h + "px";
    };

    overlay.onmouseup = async (e) => {
        isDragging = false;
        const rect = box.getBoundingClientRect();
        
        if (rect.width < 10 || rect.height < 10) {
            cleanup();
            return;
        }

        // Hide overlay for capture
        overlay.style.display = 'none';
        hint.style.display = 'none';

        // Capture visible area
        chrome.runtime.sendMessage({ action: "capture_visible" }, async (dataUrl) => {
            if (!dataUrl) {
                alert("Capture failed");
                cleanup();
                return;
            }

            try {
                const croppedBase64 = await cropImage(dataUrl, rect);
                chrome.runtime.sendMessage({ 
                    action: "analyze_custom_image", 
                    payload: { imageBase64: croppedBase64 } 
                }, (response) => {
                    cleanup();
                    if (response && response.error) alert("DeepScan Error: " + response.error);
                });
            } catch (err) {
                console.error("Crop failed", err);
                cleanup();
            }
        });
    };
}

async function cropImage(dataUrl, rect) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => {
            const canvas = document.createElement("canvas");
            const ctx = canvas.getContext("2d");
            
            // We need to account for dispositivo pixel ratio
            const dpr = window.devicePixelRatio || 1;
            canvas.width = rect.width * dpr;
            canvas.height = rect.height * dpr;

            ctx.drawImage(
                img,
                rect.left * dpr, rect.top * dpr, rect.width * dpr, rect.height * dpr,
                0, 0, rect.width * dpr, rect.height * dpr
            );
            
            resolve(canvas.toDataURL("image/png"));
        };
        img.onerror = reject;
        img.src = dataUrl;
    });
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
