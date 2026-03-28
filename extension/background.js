// extension/background.js
// Handles communication with the Deepscan Backend to bypass CORS in content scripts

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "analyze_email") {
        analyzeEmailContent(request.payload)
            .then(data => sendResponse({ success: true, data }))
            .catch(error => sendResponse({ success: false, error: error.message }));

        return true; // Keep the message channel open for async response
    }

    if (request.action === "capture_and_analyze") {
        captureAndAnalyzeScreen()
            .then(data => sendResponse(data))
            .catch(error => sendResponse({ error: error.message }));
        return true;
    }

    if (request.action === "capture_visible") {
        chrome.tabs.captureVisibleTab(null, { format: "png" }, (imgUrl) => {
            if (chrome.runtime.lastError) {
                sendResponse(null);
            } else {
                sendResponse(imgUrl);
            }
        });
        return true;
    }

    if (request.action === "analyze_custom_image") {
        analyzeCustomImage(request.payload.imageBase64)
            .then(data => sendResponse(data))
            .catch(error => sendResponse({ error: error.message }));
        return true;
    }
});

// Helper function to convert dataURL to Blob
async function dataUrlToBlob(dataUrl) {
    const res = await fetch(dataUrl);
    return await res.blob();
}

async function captureAndAnalyzeScreen() {
    const dataUrl = await new Promise((resolve, reject) => {
        chrome.tabs.captureVisibleTab(null, { format: "png" }, (imgUrl) => {
            if (chrome.runtime.lastError) return reject(new Error(chrome.runtime.lastError.message));
            resolve(imgUrl);
        });
    });

    if (!dataUrl) throw new Error("Failed to capture screenshot");
    return await analyzeCustomImage(dataUrl);
}

async function analyzeCustomImage(dataUrl) {
    // 2. Convert to Blob for File upload
    const blob = await dataUrlToBlob(dataUrl);
    const formData = new FormData();
    formData.append("file", blob, "screenshot.png");

    // 3. Send to Deepscan Backend
    const backendUrl = "http://127.0.0.1:8000/api/v1/analyze";
    
    const response = await fetch(backendUrl, {
        method: "POST",
        body: formData
    });

    if (!response.ok) {
        throw new Error(`Backend API error. Status: ${response.status}`);
    }

    const result = await response.json();
    const analysisId = result.id || result.analysis_id;

    if (!analysisId) {
        throw new Error("Backend did not return an analysis ID.");
    }

    const frontendUrl = `http://localhost:3002/analysis/${analysisId}`;
    chrome.tabs.create({ url: frontendUrl });

    return { success: true };
}

async function analyzeEmailContent(payload) {
    const backendUrl = "http://127.0.0.1:8000/api/v1/analyze/text";

    // Fetch AI Analysis
    const aiPromise = fetch(backendUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: payload.body, mode: "ai" })
    });

    // Fetch Phishing Analysis
    const phishPromise = fetch(backendUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: payload.body, mode: "phishing" })
    });

    const [aiResponse, phishResponse] = await Promise.all([aiPromise, phishPromise]);

    if (!aiResponse.ok || !phishResponse.ok) {
        throw new Error(`Backend API error. AI: ${aiResponse.status}, Phishing: ${phishResponse.status}`);
    }

    const aiData = await aiResponse.json();
    const phishData = await phishResponse.json();

    // Map the percentage scores (0-100) from backend to decimals (0.0-1.0) expected by content.js
    return {
        phishing_score: (phishData.overall_score || 0) / 100,
        ai_probability: (aiData.overall_score || 0) / 100,
        analysis: [
            ...(aiData.details?.reasons || []),
            ...(phishData.details?.reasons || [])
        ]
    };
}
