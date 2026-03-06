import React, { useState, useEffect, useRef } from 'react';
import exifr from 'exifr';
import { Loader2, Zap, Shield, AlertTriangle, Eye, CheckCircle2 } from 'lucide-react';
import BrutalCard from '../ui/BrutalCard';
import TerminalText from '../ui/TerminalText';
import BrutalButton from '../ui/BrutalButton';

// ─── API Keys & Constants ────────────────────────────────────────────────────
const GROQ_API_KEY = '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';
const HF_API_KEY = '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';

// ─── Claude Forensic Prompt: camera-aware, conservative ─────────────────────
const CLAUDE_FORENSIC_PROMPT = `You are a senior forensic image analyst with 20 years of experience distinguishing real camera photographs from AI-generated images. Your job requires VERY HIGH accuracy — false positives (calling a real photo fake) are considered serious errors.

## AUTHENTICITY SIGNALS — if you see these, the image is likely REAL:
- Optical lens distortion at edges and corners
- Chromatic aberration (colour fringing on high-contrast edges)
- Real sensor noise (fine, random grain, not uniform)
- Natural motion blur or defocus consistent with physics
- Depth-of-field bokeh that follows a real lens aperture curve
- Authentic facial micro-expressions, pores, natural skin texture variation
- Real-world lighting inconsistencies (shadows not quite perfect)
- Compression artifacts typical of JPEG cameras (blocking, ringing)
- Natural hair strands that are messy and non-uniform
- Correct and physically consistent reflections
- Camera metadata fingerprints visible in the pixel data

## AI GENERATION RED FLAGS — you MUST see at least 3 of these to flag:
- Unnaturally perfect, smooth skin with zero pores or blemishes
- Eyes that are perfectly symmetrical with a glossy, "glass" appearance
- Hair that looks like painted strokes rather than individual strands
- Hands with wrong number of fingers, fused/bent fingers, or rubber-looking skin
- Teeth that look like a single block of white porcelain
- Impossible or physically inconsistent bokeh (background blur)
- Perfect, uniform lighting with no real-world shadows or falloff
- Text in the image that is garbled, misspelled, or morphed
- Clothing or fabric patterns that don't tile correctly or warp at edges
- Background elements that dissolve into each other unrealistically
- Faces that are too symmetrical or too perfect (human faces are asymmetric)
- Objects that defy physics, gravity, or scale

## SCORING RULES (VERY IMPORTANT):
- If authenticity signals OUTWEIGH red flags: ai_score = 5-25
- If genuinely uncertain: ai_score = 30-50
- If MULTIPLE clear AI red flags (3+): ai_score = 60-80
- If DEFINITIVE AI (5+ clear red flags): ai_score = 85-100
- A low-quality, blurry, dark, or grainy photo is NOT evidence of AI — it's evidence of a real camera
- A well-composed photo is NOT evidence of AI — photographers take good photos too

Examine this image and respond ONLY with this exact JSON, no markdown:
{
  "ai_score": <0-100>,
  "verdict": "<AUTHENTIC|POSSIBLY MANIPULATED|LIKELY AI|CONFIRMED AI>",
  "summary": "<2 sentences: cite SPECIFIC visual evidence for your verdict>",
  "regions": [{"label":"<specific artifact name>","intensity":<0.0-1.0>,"polygon":[[x1,y1],...]}],
  "signals": [
    {"label":"Noise Consistency","status":"<detected|warning|clean>","detail":"<cite what you see>"},
    {"label":"Lighting & Color Temp","status":"<detected|warning|clean>","detail":"<cite what you see>"},
    {"label":"Texture Artifacts","status":"<detected|warning|clean>","detail":"<cite what you see>"},
    {"label":"Chroma Anomaly","status":"<detected|warning|clean>","detail":"<cite what you see>"},
    {"label":"Splice / Boundary","status":"<detected|warning|clean>","detail":"<cite what you see>"}
  ]
}
IMPORTANT: Empty regions array if authentic or if you cannot confirm AI manipulation with HIGH CONFIDENCE. When in doubt, mark AUTHENTIC.`;

const STATUS_COLORS = {
    detected: '#ff3c00', // ds-red
    warning: '#ffd700', // ds-yellow
    clean: '#39ff14', // ds-green
};

const VERDICT_MAP = {
    'AUTHENTIC': { color: '#39ff14', label: 'Authentic' },
    'POSSIBLY MANIPULATED': { color: '#ffd700', label: 'Possibly Manipulated' },
    'LIKELY AI': { color: '#ff8c00', label: 'Likely AI-Generated' },
    'CONFIRMED AI': { color: '#ff3c00', label: 'Confirmed AI-Generated' },
};

export default function ArbitrationSystem({ imageFile, backendScore, onComplete }) {
    const [phase, setPhase] = useState('idle'); // idle | running | done | error
    const [statusLine, setStatusLine] = useState('Select an image to start the AI debate.');
    const [logs, setLogs] = useState([]);
    const [result, setResult] = useState(null);
    const runningRef = useRef(false);
    const fileRef = useRef(null);

    // Auto-trigger whenever a NEW file is chosen
    useEffect(() => {
        if (!imageFile) { resetState(); return; }
        if (imageFile === fileRef.current) return;   // same file, skip
        fileRef.current = imageFile;
        setPhase('idle');
        setResult(null);
        setLogs([]);
        setStatusLine('Image ready — starting Multi-AI analysis...');

        const timer = setTimeout(() => {
            triggerPipeline(imageFile);
        }, 800);
        return () => clearTimeout(timer);
    }, [imageFile]);

    const resetState = () => {
        setPhase('idle');
        setStatusLine('Select an image to start the AI debate.');
        setLogs([]);
        setResult(null);
        runningRef.current = false;
        fileRef.current = null;
    };

    const addLog = (model, text, color) =>
        setLogs(prev => [...prev, { model, text, color }]);

    const toBase64 = (file) =>
        new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = () => resolve(reader.result.split(',')[1] || '');
            reader.onerror = reject;
        });

    // Wait for window.puter with retries
    const waitForPuter = () =>
        new Promise(resolve => {
            let tries = 0;
            const check = setInterval(() => {
                tries++;
                if (window.puter?.ai?.chat) { clearInterval(check); resolve(true); }
                if (tries >= 20) { clearInterval(check); resolve(false); }
            }, 300);
        });

    const triggerPipeline = async (file) => {
        if (runningRef.current) return;
        runningRef.current = true;
        setPhase('running');
        setLogs([]);

        const ready = await waitForPuter();
        if (!ready) {
            setStatusLine('⚠️ Puter.js failed to load. Check your internet connection.');
            setPhase('error');
            runningRef.current = false;
            return;
        }

        try {
            const base64 = await toBase64(file);

            // ── 0. FAST PRE-COMPUTE: EXIF, Hugging Face, Groq ─────────────────────
            setStatusLine('📡 Extracting EXIF and querying fast statistical models...');

            // A. EXIF Metadata Extraction (The False-Positive Killer)
            let exifData = null;
            let exifText = "No EXIF metadata found (stripped).";
            try {
                exifData = await exifr.parse(file);
                if (exifData && Object.keys(exifData).length > 0) {
                    const make = exifData.Make || 'Unknown Make';
                    const model = exifData.Model || 'Unknown Model';
                    const software = exifData.Software || 'None';
                    const date = exifData.DateTimeOriginal || 'Unknown Date';
                    exifText = `HARDWARE EXIF FOUND: ${make} ${model}. Software: ${software}. Date: ${date}. Lens: ${exifData.LensModel || 'Unknown'}.`;
                    addLog('EXIF Scanner', `Hardware metadata present: ${make} ${model}`, '#00f5ff'); // ds-cyan
                } else {
                    addLog('EXIF Scanner', 'No EXIF metadata found. Likely stripped by AI generator or social media.', '#ffd700'); // ds-yellow
                }
            } catch (e) {
                console.warn("EXIF read failed", e);
            }

            // B. Hugging Face Inference API (Statistical Vision Model)
            let hfScore = null;
            const hfPromise = fetch(
                "https://api-inference.huggingface.co/models/umm-maybe/AI-image-detector",
                {
                    headers: { Authorization: `Bearer ${HF_API_KEY}` },
                    method: "POST",
                    body: file,
                }
            ).then(res => res.json()).then(result => {
                if (Array.isArray(result)) {
                    const aiResult = result.find((r) => r.label === 'artificial');
                    if (aiResult) {
                        hfScore = Math.round(aiResult.score * 100);
                        addLog('HF Vision Model', `Statistical AI probability: ${hfScore}%`, '#ff00ff'); // magenta
                    }
                }
            }).catch(() => addLog('HF Vision Model', 'Failed to reach API.', '#888888'));

            // C. Groq (Agent C - Fast Structural Analyst)
            let groqAnalysis = "Groq analysis unavailable.";

            // ── 1. Claude Vision: forensic polygon scan ─────────────────────────
            setStatusLine('🔍 Claude 3.5 Sonnet scanning for AI regions...');
            let claudeData = null;
            try {
                const claudeRes = await window.puter.ai.chat(
                    [{
                        role: 'user', content: [
                            { type: 'image_url', image_url: { url: `data:${file.type || 'image/jpeg'};base64,${base64}` } },
                            { type: 'text', text: `EXIF Data extracted: ${exifText}\n\n${CLAUDE_FORENSIC_PROMPT}` }
                        ]
                    }],
                    { model: 'claude-sonnet-4-5' }
                );
                let raw = claudeRes?.message?.content || claudeRes || '';
                if (raw.includes('```json')) raw = raw.split('```json')[1].split('```')[0];
                else if (raw.includes('```')) raw = raw.split('```')[1].split('```')[0];
                claudeData = JSON.parse(raw.trim());
                const regionCount = claudeData.regions?.length ?? 0;
                addLog('Claude 3.5 Vision', `${claudeData.verdict} — ${regionCount} region(s) flagged. ${claudeData.summary}`, '#ff8c00'); // orange
            } catch (e) {
                addLog('Claude 3.5 Vision', 'Vision scan failed — falling back to debate only.', '#ff3c00');
            }

            // ── 2. Gemini: scene description ─────────────────────────────────────
            setStatusLine('👁️ Gemini 2.5 Flash describing the scene...');
            let description = 'An image submitted for AI forensic analysis.';
            try {
                const geminiRes = await window.puter.ai.chat(
                    `Describe this image in 3 concise sentences: objects, people, setting, lighting, and any physical impossibilities.`,
                    { model: 'google/gemini-2.5-flash' }
                );
                description = geminiRes?.message?.content || geminiRes || description;
                addLog('Gemini 2.5 Flash', description.substring(0, 130) + '...', '#00f5ff');
            } catch { addLog('Gemini', 'Scene description skipped.', '#888888'); }

            // ── 3. 10-Domain Forensic Debate: Claude (Authenticator) vs GPT-4o (Detector) ──
            setStatusLine('🟦 Agent A — Claude: building AUTHENTIC case across 10 domains...');

            // Run Groq text analysis now that we have the scene description
            const groqPromise = fetch('https://api.groq.com/openai/v1/chat/completions', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${GROQ_API_KEY}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    model: 'llama3-70b-8192',
                    messages: [
                        { role: 'system', content: 'You are Agent C, a fast structural analyst in a deepfake detection system. Analyze the metadata and scene context.' },
                        { role: 'user', content: `EXIF Data: ${exifText}\nScene: ${description}\nGive a hard verdict on authenticity based strictly on the metadata presence or absence. Keep it under 60 words.` }
                    ],
                    max_tokens: 150
                })
            }).then(res => res.json()).then(data => {
                groqAnalysis = data.choices[0].message.content;
                addLog('⚡ Agent C — Groq Llama 3', groqAnalysis.substring(0, 100) + '...', '#ffd700');
            }).catch(() => { groqAnalysis = 'Groq analysis failed.'; });

            const agentBaseContext = `Scene context: ${description}\nEXTRACTED EXIF METADATA: ${exifText}`;

            const agentAPrompt = `# FORENSIC DEBATE — AGENT A: THE AUTHENTICATOR
Your assigned position: This image was captured by a REAL camera/phone.
Argue across all 10 forensic domains. Cite SPECIFIC observable evidence only. No vague claims.

${agentBaseContext}

Address ALL 10 domains:
1. OPTICS & LENS PHYSICS: chromatic aberration, realistic bokeh, natural vignetting, lens distortion
2. SENSOR & NOISE: Poisson-distributed grain, chroma noise in shadows, non-repeating sensor texture
3. LIGHTING COHERENCE: single-source shadows, correct inverse-square falloff, color temperature consistency
4. GEOMETRIC INTEGRITY: straight lines, correct perspective, legible text, accurate proportions
5. TEXTURE MICRO-DETAIL: irregular pores, individual hair strands, real fabric weave, non-repeating surfaces
6. METADATA & COMPRESSION: JPEG block artifacts (8x8 DCT), realistic color space, compression ringing
7. SEMANTIC PLAUSIBILITY: plausible reason to photograph, logical object interactions, narrative coherence
8. HUMAN BIOMETRICS: natural facial asymmetry, stochastic iris, skin age consistency, natural imperfections
9. TEMPORAL ARTIFACTS: directional motion blur, rolling shutter, natural freeze-frame moments
10. STYLISTIC FINGERPRINTS: photography imperfections — dust, suboptimal framing, real lighting chaos

SCORING RULES (CRITICAL):
- Camera signals only → 0-15% AI probability
- Mostly authentic + minor doubts → 16-30%
- Genuinely ambiguous → 35-50%
- A blurry/grainy/dark photo = REAL camera evidence, NOT AI
- A well-composed photo = GOOD PHOTOGRAPHER, NOT AI

Respond in this exact format:
DOMAINS: [one sentence per domain with specific named evidence]
VERDICT: [X]% AI probability
TOP_3_EVIDENCE: [your 3 most decisive authenticity observations]
CHALLENGE: [1 specific finding that would change your verdict]`;

            setStatusLine('🟥 Agent B — GPT-4o: building AI-GENERATED case across 10 domains...');

            const agentBPrompt = `# FORENSIC DEBATE — AGENT B: THE DETECTOR
Your assigned position: This image was GENERATED by an AI system (diffusion model, GAN, or similar).
Argue across all 10 forensic domains. Cite SPECIFIC observable evidence only. Do NOT use vague "looks too perfect" — name the exact artifact.

${agentBaseContext}

Address ALL 10 domains:
1. OPTICS & LENS PHYSICS: bokeh too perfect/spherical, missing chromatic aberration, inconsistent depth-of-field
2. SENSOR & NOISE: noise uniform or absent, synthetic grain tiles/repeats, unnaturally clean shadows
3. LIGHTING COHERENCE: inconsistent shadow directions, missing AO, objects lit independently of scene
4. GEOMETRIC INTEGRITY: warping walls, garbled text, melting backgrounds, wrong finger counts, bad reflections
5. TEXTURE MICRO-DETAIL: plastic-like skin (zero pores), repeating textures, hair merging, uniform fabrics
6. METADATA & COMPRESSION: PNG format (AI tools output PNG), missing EXIF, absence of JPEG block artifacts
7. SEMANTIC PLAUSIBILITY: stock-photo-perfect scene, floating objects, disconnected foreground/background
8. HUMAN BIOMETRICS: fused/extra fingers, symmetric eyes with glass quality, uniform teeth block, merged jewelry
9. TEMPORAL ARTIFACTS: uniform blur, missing motion physics, statically posed subjects
10. STYLISTIC FINGERPRINTS: over-saturation, too-smooth skin, Midjourney cinematic glow, optimized composition

KNOWN AI SYSTEM FINGERPRINTS:
- Stable Diffusion: fails on hand anatomy, purple skin noise
- Midjourney: hyper-detailed fur but wrong finger topology, cinematic color grading
- DALL-E 3: flat textures, incorrect text, overly clean environments
- FLUX/SD3: passes casual inspection but fails on reflections and eye symmetry

Respond in this exact format:
DOMAINS: [one sentence per domain with specific named evidence]
VERDICT: [X]% AI probability
TOP_3_EVIDENCE: [your 3 most decisive AI-generation observations]
CHALLENGE: [1 specific finding that would change your verdict]`;

            // Run both agents in parallel
            const [claudeDebate, gptDebate] = await Promise.all([
                window.puter.ai.chat(agentAPrompt, { model: 'claude-sonnet-4-5' })
                    .then((r) => String(r?.message?.content || r || 'VERDICT: 30% AI probability - Report unavailable.'))
                    .catch(() => 'VERDICT: 30% AI probability - Claude Agent A failed.'),
                window.puter.ai.chat(agentBPrompt, { model: 'gpt-4o' })
                    .then((r) => String(r?.message?.content || r || 'VERDICT: 50% AI probability - Report unavailable.'))
                    .catch(() => 'VERDICT: 50% AI probability - GPT-4o Agent B failed.'),
            ]);

            // Parse each agent's probability estimate from VERDICT: X% format
            const agentAMatch = claudeDebate.match(/VERDICT:\s*([\d.]+)%/i);
            const agentBMatch = gptDebate.match(/VERDICT:\s*([\d.]+)%/i);
            const agentAScore = agentAMatch ? Math.min(100, parseFloat(agentAMatch[1])) : 30;
            const gptExtractedScore = agentBMatch ? Math.min(100, parseFloat(agentBMatch[1])) : 50;

            // Wait for all remaining parallel tasks
            await Promise.all([hfPromise, groqPromise]);

            const aTop3 = claudeDebate.split('TOP_3_EVIDENCE:')[1]?.split('CHALLENGE:')[0]?.trim().substring(0, 100) || claudeDebate.substring(0, 80);
            const bTop3 = gptDebate.split('TOP_3_EVIDENCE:')[1]?.split('CHALLENGE:')[0]?.trim().substring(0, 100) || gptDebate.substring(0, 80);
            addLog('🟦 Agent A — Claude (Authenticator)', `${agentAScore}% AI | ${aTop3}...`, '#39ff14'); // ds-green
            addLog('🟥 Agent B — GPT-4o (Detector)', `${gptExtractedScore}% AI | ${bTop3}...`, '#00f5ff'); // ds-cyan

            // ── 4. Llama 3: Grand Arbitrator — reads both full forensic reports ──
            setStatusLine('⚖️ Llama 3 70B — Reading both reports and arbitrating...');
            const backendNote = backendScore !== null
                ? `\nBackend 10-layer forensic pipeline: ${backendScore}% (pixel artifacts, face geometry, FFT, metadata, semantics).`
                : '';

            const judgePrompt = `# GRAND ARBITRATOR — FORENSIC IMAGE AUTHENTICITY VERDICT

You have received two expert forensic reports from opposing agents. Read both in full and render a DEFINITIVE verdict.
${backendNote}
Claude Vision pre-scan: "${claudeData?.verdict || 'N/A'}" — AI Score: ${claudeData?.ai_score ?? 'N/A'}%

## AGENT A REPORT (Authenticator — argues CAMERA AUTHENTIC):
${claudeDebate}

## AGENT B REPORT (Detector — argues AI-GENERATED):
${gptDebate}

## AGENT C REPORT (Fast Groq Metadata Analyst):
${groqAnalysis}

## YOUR STRICT RULING RULES (READ CAREFULLY):
1. THE METADATA RULE: If valid hardware EXIF data is present (e.g. Apple, Samsung, Sony camera details), you MUST cap the final AI probability at 15%. Genuine metadata is proof of physical origin.
2. A blurry, grainy, poorly-lit photo = REAL camera. Do NOT count as AI evidence.
3. A well-composed, well-lit photo = GOOD PHOTOGRAPHER. Do NOT count as AI evidence.
4. Only accept AI claims backed by NAMED, SPECIFIC visual artifacts (e.g. "rubber hand with 6 fingers").
5. Give GPT-4o (Detector) higher weight ONLY when it names concrete, specific AI artifacts.
6. Give Claude (Authenticator) higher weight when it names concrete camera signals.
7. If both agents score within 20 points of each other → lean authentic (score 25-40%).
8. Extraordinary "AI-generated" claims require extraordinary named evidence.

Respond ONLY with valid JSON (no markdown):
{"final_ai_probability": <0-100>, "confidence": "<LOW|MEDIUM|HIGH>", "domain_winner": "<Authenticator|Detector|Tied>", "reasoning": "<2 sentences citing specific visual evidence from the reports>", "decisive_evidence": "<the single most important forensic observation that decided this>"}`;

            let debateScore = 50;
            let reasoning = 'Arbitration inconclusive.';
            try {
                const judgeRes = await window.puter.ai.chat(judgePrompt, { model: 'meta/llama-3-70b-instruct' });
                let jText = String(judgeRes?.message?.content || judgeRes || '{}');
                if (jText.includes('```json')) jText = jText.split('```json')[1].split('```')[0];
                else if (jText.includes('```')) jText = jText.split('```')[1].split('```')[0];
                const parsed = JSON.parse(jText.trim());
                debateScore = Math.min(100, Math.max(0, parsed.final_ai_probability ?? 50));
                reasoning = `[${parsed.domain_winner || 'Tied'} wins | ${parsed.confidence || 'MEDIUM'} confidence] ${parsed.reasoning ?? ''} Key: ${parsed.decisive_evidence ?? ''}`;
                addLog('⚖️ Llama 3 Arbitrator', `${debateScore}% — ${reasoning.substring(0, 130)}`, '#b966ff'); // purple
            } catch {
                // Fallback: use GPT-4o Detector score (names concrete artifacts)
                debateScore = gptExtractedScore;
                reasoning = `GPT-4o Detector fallback: ${debateScore}% AI probability (Llama arbitration failed).`;
                addLog('⚖️ Arbitrator (GPT Fallback)', `${debateScore}% — ${reasoning}`, '#ffd700');
            }


            // ── 5. Grand Ensemble: Hugging Face gets added to the mix ──────
            const claudePixScore = claudeData?.ai_score ?? gptExtractedScore;
            // The Arbitrator read the EXIF, Groq, and HF data, so its score is highly informed.
            // If HF score exists, we fold it into the backend/statistical bucket.
            const cvScore = hfScore !== null ? Math.round((claudePixScore * 0.6) + (hfScore * 0.4)) : claudePixScore;
            const bScore = backendScore !== null ? backendScore : (hfScore ?? cvScore);

            // Weights: Arbitrator 40% (synthesizes ALL) + GPT-4o 25% + Vision/HF 20% + Backend 15%
            const grandScore = Math.round(
                debateScore * 0.40 +
                gptExtractedScore * 0.25 +
                cvScore * 0.20 +
                bScore * 0.15
            );

            // ── 6. Fail-Safe EXIF Override ── 
            // If hardware EXIF or authentic OS software is verified, aggressively clamp score down
            const softwareLower = String(exifData?.Software || '').toLowerCase();
            const fileNameLower = file?.name?.toLowerCase() || '';
            const hasAuthenticSoftware = ['windows', 'android', 'ios', 'macos', 'apple', 'whatsapp', 'instagram', 'snapchat'].some(s => softwareLower.includes(s));
            const hasSocialMediaFilename = ['whatsapp image', 'img-', 'screenshot'].some(s => fileNameLower.includes(s));

            const isProvenReal = (exifData && exifData.Make) || hasAuthenticSoftware || hasSocialMediaFilename;
            const finalProcessedScore = isProvenReal ? Math.min(grandScore, 18) : grandScore;

            if (isProvenReal && !exifText.includes('HARDWARE')) {
                exifText += ` [High-Leverage Authenticity Signal Detected via File/Software: ${file.name}]`;
            }

            // Map to a human verdict
            let verdictKey = 'AUTHENTIC';
            if (finalProcessedScore >= 85) verdictKey = 'CONFIRMED AI';
            else if (finalProcessedScore >= 60) verdictKey = 'LIKELY AI';
            else if (finalProcessedScore >= 35) verdictKey = 'POSSIBLY MANIPULATED';

            const verdictInfo = VERDICT_MAP[verdictKey];

            const finalResult = {
                finalScore: finalProcessedScore,
                verdict: verdictInfo.label,
                verdictColor: verdictInfo.color,
                claudeVerdict: claudeData?.verdict || 'N/A',
                summary: reasoning,
                regions: claudeData?.regions || [],
                signals: claudeData?.signals || [],
                debateScore: gptExtractedScore,
                claudeScore: cvScore,
                backendScore: bScore,
                hfScore,
                exifDetails: exifText,
            };

            setResult(finalResult);
            setPhase('done');
            setStatusLine('✅ Grand Arbitration complete.');
            if (onComplete) onComplete(finalResult);

        } catch (err) {
            addLog('System Error', err.message || 'Unknown error', '#ff3c00');
            setPhase('error');
            setStatusLine('❌ Pipeline failed. Try again.');
        } finally {
            runningRef.current = false;
        }
    };

    return (
        <BrutalCard className="mt-8 border-ds-silver/20 bg-ds-bg/80 backdrop-blur-sm p-4 relative overflow-hidden group">
            {/* Header */}
            <div className="flex justify-between items-center mb-4">
                <h3 className="font-grotesk font-black text-ds-silver text-sm sm:text-base uppercase tracking-wider flex items-center gap-2">
                    <Shield className="w-4 h-4 text-ds-cyan" />
                    Multi-AI Grand Arbitration
                    <span className="text-[10px] font-mono font-normal px-2 py-0.5 border border-ds-cyan/30 text-ds-cyan bg-ds-cyan/10">
                        Puter.js
                    </span>
                </h3>
                {/* Manual trigger button */}
                <button
                    onClick={() => imageFile && triggerPipeline(imageFile)}
                    disabled={!imageFile || phase === 'running'}
                    className={`px-3 py-1 text-xs font-mono font-bold uppercase border-2 transition-all ${phase === 'running'
                            ? 'bg-ds-cyan/20 border-ds-cyan/50 text-ds-cyan/70 cursor-not-allowed'
                            : 'bg-ds-cyan text-ds-bg border-ds-cyan hover:-translate-y-0.5 shadow-[4px_4px_0px_#00f5ff40] cursor-pointer'
                        }`}
                    style={{ opacity: !imageFile ? 0.4 : 1 }}
                >
                    {phase === 'running' ? (
                        <span className="flex items-center gap-2"><Loader2 className="w-3 h-3 animate-spin" /> Running...</span>
                    ) : '▶ Re-run'}
                </button>
            </div>

            <p className="text-xs font-mono text-ds-silver/50 mb-3 block">
                Claude 3.5 Vision → Gemini Scene → Claude+GPT Debate → Llama 3 Arbitrator
            </p>

            {/* Status line */}
            <div className="flex items-center gap-2 text-xs font-mono mb-3 p-2 bg-ds-silver/5 border border-ds-silver/10">
                {phase === 'error' ? <AlertTriangle className="w-4 h-4 text-ds-red" /> :
                    phase === 'done' ? <CheckCircle2 className="w-4 h-4 text-ds-green" /> :
                        <Zap className="w-4 h-4 text-ds-cyan animate-pulse" />}
                <span className={phase === 'error' ? 'text-ds-red' : 'text-ds-silver/80'}>
                    {statusLine}
                </span>
            </div>

            {/* Live debate log */}
            <div className="max-h-[220px] overflow-y-auto bg-[#0a0a0f] p-3 border-2 border-ds-silver/20 font-mono text-xs shadow-inner scrollbar-thin scrollbar-thumb-ds-silver/20">
                {logs.length === 0
                    ? <span className="text-ds-silver/30">Debate log will appear here...</span>
                    : logs.map((log, i) => (
                        <div key={i} className="mb-2 pb-2 border-b border-ds-silver/10 last:border-0 last:pb-0">
                            <strong style={{ color: log.color || '#00f5ff' }}>{log.model}:</strong>
                            <span className="text-ds-silver/80 ml-2">{log.text}</span>
                        </div>
                    ))
                }
            </div>

            {/* Grand Verdict */}
            {result && phase === 'done' && (
                <div className="mt-4 p-4 sm:p-6 border-2 relative overflow-hidden transition-all duration-500"
                    style={{
                        borderColor: result.verdictColor,
                        backgroundColor: `${result.verdictColor}10`
                    }}>
                    <div className="absolute top-0 right-0 w-32 h-32 opacity-20 pointer-events-none"
                        style={{ background: `radial-gradient(circle at top right, ${result.verdictColor}, transparent)` }} />

                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 relative z-10">
                        <div>
                            <div className="text-[10px] font-mono text-ds-silver/60 mb-1 uppercase tracking-widest">
                                Grand Arbitration Verdict
                            </div>
                            <div className="text-2xl sm:text-3xl font-grotesk font-black flex items-center gap-2" style={{ color: result.verdictColor }}>
                                {result.verdict}
                            </div>
                            <div className="text-xs sm:text-sm font-mono text-ds-silver/80 mt-2 max-w-lg leading-relaxed border-l-2 pl-3" style={{ borderColor: `${result.verdictColor}50` }}>
                                {result.summary}
                            </div>
                        </div>
                        <div className="text-center sm:text-right w-full sm:w-auto p-4 sm:p-0 bg-black/20 sm:bg-transparent border sm:border-0 border-ds-silver/20 mt-2 sm:mt-0">
                            <div className="text-4xl sm:text-5xl font-grotesk font-black leading-none drop-shadow-lg" style={{ color: result.verdictColor }}>
                                {result.finalScore}%
                            </div>
                            <div className="text-[10px] font-mono uppercase tracking-wider text-ds-silver/50 mt-1">AI Probability</div>
                        </div>
                    </div>

                    {/* Score breakdown */}
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mt-6 relative z-10">
                        {[
                            { label: 'Claude Vision', val: result.claudeScore, color: '#ff8c00' }, // ds-orange approximate
                            { label: 'LLM Debate', val: result.debateScore, color: '#b966ff' },   // ds-purple
                            { label: 'Backend AACS', val: result.backendScore, color: '#00f5ff' }, // ds-cyan
                        ].map(s => (
                            <div key={s.label} className="bg-ds-bg/60 border border-ds-silver/20 p-2 sm:p-3 text-center transition-colors hover:bg-ds-silver/5">
                                <div className="text-xl sm:text-2xl font-grotesk font-black drop-shadow-sm" style={{ color: s.color }}>{s.val}%</div>
                                <div className="text-[9px] sm:text-[10px] font-mono text-ds-silver/60 uppercase tracking-widest mt-1">{s.label}</div>
                            </div>
                        ))}
                    </div>

                    {/* Forensic signals */}
                    {result.signals.length > 0 && (
                        <div className="mt-4 flex flex-wrap gap-2 relative z-10">
                            {result.signals.map((sig, i) => (
                                <span key={i} title={sig.detail}
                                    className="text-[10px] font-mono px-2.5 py-1 border flex items-center gap-1.5 backdrop-blur-sm"
                                    style={{
                                        borderColor: `${STATUS_COLORS[sig.status] || '#888'}60`,
                                        backgroundColor: `${STATUS_COLORS[sig.status] || '#888'}15`,
                                        color: STATUS_COLORS[sig.status] || '#aaa',
                                    }}>
                                    <span className="w-1.5 h-1.5 rounded-full" style={{ background: STATUS_COLORS[sig.status] || '#888' }} />
                                    {sig.label}
                                </span>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </BrutalCard>
    );
}
