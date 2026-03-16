// extension/background.js
// Handles communication with the Deepscan Backend to bypass CORS in content scripts

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "analyze_email") {
        analyzeEmailContent(request.payload)
            .then(data => sendResponse({ success: true, data }))
            .catch(error => sendResponse({ success: false, error: error.message }));

        return true; // Keep the message channel open for async response
    }
});

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
