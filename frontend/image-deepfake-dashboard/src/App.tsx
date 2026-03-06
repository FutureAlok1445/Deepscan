import React, { useState } from 'react';
import './App.css';
import Article from './Article';
import History from './History';
import ArbitrationSystem from './ArbitrationSystem';
import type { ArbitrationResult } from './ArbitrationSystem';

interface SignalScores {
  metadata_cvs: number;
  visual_forensics_mas: number;
  face_geometry_pps: number;
  frequency: number;
  semantic_context_irs: number;
  diffusion_fingerprint?: number; // Phase 5
}

interface AnalysisResult {
  score: number;
  verdict: string;
  signals: SignalScores;
  explainability: {
    text: string;
    ela_base64_heatmap_prefix: string;
    regions?: any[]; // Phase 4 Claude polygons
  };
}

// ─── Phase 4: High-Fidelity Region Heatmap Port ──────────────────────────────
const THERMAL = [
  [0, 0, 80], [0, 0, 160], [0, 0, 255], [0, 100, 255], [0, 200, 255],
  [0, 255, 180], [0, 255, 80], [120, 255, 0], [230, 255, 0],
  [255, 210, 0], [255, 110, 0], [255, 30, 0], [180, 0, 0],
];
function thermalColor(v: number): number[] {
  v = Math.max(0, Math.min(1, v));
  const idx = v * (THERMAL.length - 1);
  const lo = Math.floor(idx);
  const hi = Math.min(lo + 1, THERMAL.length - 1);
  const t = idx - lo;
  return THERMAL[lo].map((c, i) => Math.round(c * (1 - t) + THERMAL[hi][i] * t));
}

function gaussBlur(src: Float32Array, W: number, H: number, r: number) {
  const sigma = r / 2.2, sz = r * 2 + 1;
  const k = Array.from({ length: sz }, (_, i) => {
    const x = i - r; return Math.exp(-(x * x) / (2 * sigma * sigma));
  });
  const ks = k.reduce((a, b) => a + b, 0);
  k.forEach((_, i) => k[i] /= ks);
  const tmp = new Float32Array(src.length), out = new Float32Array(src.length);
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    let s = 0; for (let n = 0; n < sz; n++) { const nx = Math.min(Math.max(x + n - r, 0), W - 1); s += src[y * W + nx] * k[n]; } tmp[y * W + x] = s;
  }
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    let s = 0; for (let n = 0; n < sz; n++) { const ny = Math.min(Math.max(y + n - r, 0), H - 1); s += tmp[ny * W + x] * k[n]; } out[y * W + x] = s;
  }
  return out;
}

function buildHeatmapFromRegions(regions: any[], W: number, H: number) {
  const mask = new Float32Array(W * H);

  regions.forEach(({ polygon, intensity = 0.8 }) => {
    if (!polygon || polygon.length < 3) return;
    const pts = polygon.map(([px, py]: [number, number]) => [px * W, py * H]);

    const ys = pts.map((p: number[]) => p[1]);
    const yMin = Math.max(0, Math.floor(Math.min(...ys)));
    const yMax = Math.min(H - 1, Math.ceil(Math.max(...ys)));

    for (let y = yMin; y <= yMax; y++) {
      const intersections = [];
      for (let i = 0; i < pts.length; i++) {
        const [x0, y0] = pts[i];
        const [x1, y1] = pts[(i + 1) % pts.length];
        if ((y0 <= y && y1 > y) || (y1 <= y && y0 > y)) {
          intersections.push(x0 + (y - y0) / (y1 - y0) * (x1 - x0));
        }
      }
      intersections.sort((a, b) => a - b);
      for (let j = 0; j < intersections.length - 1; j += 2) {
        const xL = Math.max(0, Math.floor(intersections[j]));
        const xR = Math.min(W - 1, Math.ceil(intersections[j + 1]));
        for (let x = xL; x <= xR; x++) {
          mask[y * W + x] = Math.max(mask[y * W + x], intensity);
        }
      }
    }
  });

  const blurred = gaussBlur(mask, W, H, 22);

  let mx = 0;
  for (let i = 0; i < blurred.length; i++) if (blurred[i] > mx) mx = blurred[i];
  if (mx === 0) mx = 1;

  const rgba = new Uint8ClampedArray(W * H * 4);
  for (let i = 0; i < W * H; i++) {
    const v = blurred[i] / mx;
    const [r, g, b] = thermalColor(v);
    rgba[i * 4] = r;
    rgba[i * 4 + 1] = g;
    rgba[i * 4 + 2] = b;
    rgba[i * 4 + 3] = v < 0.08 ? 0 : Math.round(Math.pow(v, 0.6) * 210);
  }
  return rgba;
}

function compositeHeatmap(imgEl: HTMLImageElement, regions: any[]): Promise<string> {
  return new Promise(resolve => {
    const MAX = 700;
    let w = imgEl.naturalWidth, h = imgEl.naturalHeight;
    if (w > MAX) { h = Math.round(h * MAX / w); w = MAX; }
    if (h > MAX) { w = Math.round(w * MAX / h); h = MAX; }

    const out = document.createElement("canvas");
    out.width = w; out.height = h;
    const ctx = out.getContext("2d");
    if (!ctx) return resolve("");

    ctx.drawImage(imgEl, 0, 0, w, h);

    // Desaturate slightly
    ctx.globalCompositeOperation = "saturation";
    ctx.fillStyle = "rgba(80,80,80,0.45)";
    ctx.fillRect(0, 0, w, h);
    ctx.globalCompositeOperation = "source-over";

    if (regions && regions.length > 0) {
      const heatData = buildHeatmapFromRegions(regions, w, h);
      const tmp = document.createElement("canvas");
      tmp.width = w; tmp.height = h;
      tmp.getContext("2d")?.putImageData(new ImageData(heatData, w, h), 0, 0);
      ctx.drawImage(tmp, 0, 0);
    }

    resolve(out.toDataURL("image/png"));
  });
}
// ─────────────────────────────────────────────────────────────────────────────

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  // Phase 4 Canvas Heatmap State
  const [heatUrl, setHeatUrl] = useState<string | null>(null);
  const [caption, setCaption] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState('');
  const [sliderPos, setSliderPos] = useState(50);
  const [refreshHistory, setRefreshHistory] = useState(0);

  // Phase 5: Grand Arbitration result (replaces separate debateScore)
  const [arbitrationResult, setArbitrationResult] = useState<ArbitrationResult | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      setFile(selected);
      setPreviewUrl(URL.createObjectURL(selected));
      setResult(null);
      setHeatUrl(null);
      setArbitrationResult(null); // Phase 5
      setError('');
    }
  };

  const handleSelectScan = async (scanId: string) => {
    setLoading(true);
    setError('');
    setHeatUrl(null);
    setArbitrationResult(null); // Phase 5
    const API_BASE = 'http://127.0.0.1:8000/api/v1/analyze';
    try {
      const resp = await fetch(`${API_BASE}/result/${scanId}`);
      if (!resp.ok) throw new Error("Failed to load historical scan");
      const data = await resp.json();
      setResult(data.data);

      // Phase 4: Generate high-fidelity canvas heatmap if Claude returned regions
      const regions = data.data.explainability?.regions;
      if (regions && regions.length > 0) {
        // Need the original image URL from the history to apply the heatmap to.
        // For now, history doesn't store the raw previewUrl, so the heatmap will 
        // fall back to ELA, OR we rely on the previous previewUrl if they just ran it.
        // A full fix would store the image blob in IndexedDB or similar for history.
        if (previewUrl) {
          const img = new Image();
          img.crossOrigin = "anonymous";
          img.onload = async () => {
            const url = await compositeHeatmap(img, regions);
            setHeatUrl(url);
          };
          img.src = previewUrl;
        }
      }

      // Auto-focus the results
      window.scrollTo({ top: 400, behavior: 'smooth' });
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;

    setLoading(true);
    setResult(null);
    setHeatUrl(null);
    setArbitrationResult(null); // Phase 5 — will re-run via useEffect in ArbitrationSystem
    setError('');

    const API_BASE = 'http://127.0.0.1:8000/api/v1/analyze';
    const formData = new FormData();
    formData.append('file', file);
    if (caption) {
      formData.append('context_caption', caption);
    }

    try {
      // 1. Initial Upload -> Get Job ID
      const response = await fetch(`${API_BASE}/image`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status}`);
      }

      const { job_id } = await response.json();

      // 2. Poll for results
      await pollResult(job_id);

    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Error connecting to DeepScan API');
      setLoading(false);
    }
  };

  const pollResult = async (jobId: string) => {
    const API_BASE = 'http://127.0.0.1:8000/api/v1/analyze';

    try {
      const resp = await fetch(`${API_BASE}/result/${jobId}`);
      if (!resp.ok) throw new Error("Polling failed");

      const data = await resp.json();

      if (data.status === 'done') {
        setResult(data.data);

        // Phase 4: Generate high-fidelity canvas heatmap if Claude returned regions
        const regions = data.data.explainability?.regions;
        if (regions && regions.length > 0 && previewUrl) {
          const img = new Image();
          img.crossOrigin = "anonymous";
          img.onload = async () => {
            const url = await compositeHeatmap(img, regions);
            setHeatUrl(url);
          };
          img.src = previewUrl;
        }

        setLoading(false);
        setRefreshHistory(prev => prev + 1); // Update sidebar
      } else if (data.status === 'failed') {
        throw new Error("Analysis failed on server");
      } else {
        // Still pending or processing, wait 1.5s and try again
        setTimeout(() => pollResult(jobId), 1500);
      }
    } catch (err: any) {
      setError(err.message);
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="app-header">
        <h1>DeepScan - 10-Layer Image Forensics</h1>
        <p>Upload an image and provide context to check for deepfakes and semantic misattribution.</p>
      </header>

      <main className="main-content">
        <div className="side-panel">
          <History onSelectScan={handleSelectScan} refreshTrigger={refreshHistory} />
        </div>

        <div className="main-panel">
          <div className="upload-section">
            <div className="input-group">
              <label>1. Select Image</label>
              <input type="file" accept="image/jpeg, image/png, image/webp" onChange={handleFileChange} />
            </div>

            <div className="input-group">
              <label>2. Context/Caption (Optional)</label>
              <textarea
                placeholder="e.g. 'A politician smiling warmly at an orphanage'"
                value={caption}
                onChange={(e) => setCaption(e.target.value)}
                rows={3}
              />
              <small>Used by the Semantic Layer to detect false contexts (real images used for fake news).</small>
            </div>

            <button
              className="analyze-btn"
              onClick={handleAnalyze}
              disabled={!file || loading}
            >
              {loading ? 'Analyzing across 10 layers...' : 'Analyze Image'}
            </button>

            {error && <div className="error-msg">{error}</div>}

            {/* Phase 5: Puter Multi-AI Arbitration — always visible once a file is selected */}
            {file && previewUrl && (
              <ArbitrationSystem
                imageFile={file}
                previewUrl={previewUrl}
                backendScore={result ? result.score : null}
                onComplete={async (arbResult) => {
                  setArbitrationResult(arbResult);
                  // Wire Claude Vision regions into the thermal heatmap canvas
                  if (arbResult.regions.length > 0 && previewUrl) {
                    const img = new Image();
                    img.crossOrigin = 'anonymous';
                    img.onload = async () => setHeatUrl(await compositeHeatmap(img, arbResult.regions));
                    img.src = previewUrl;
                  }
                }}
              />
            )}
          </div>

          <div className="results-section">
            {previewUrl && !result && (
              <div className="preview-box">
                <img src={previewUrl} alt="Preview" />
              </div>
            )}

            {result && (
              <div className="dashboard">

                {/* ── Single Unified Verdict ─────────────────────────── */}
                {arbitrationResult ? (
                  /* Arbitration complete — use Grand Verdict (Arbitrator has majority weight) */
                  <div className="verdict-banner" style={{ backgroundColor: arbitrationResult.verdictColor, padding: '20px 24px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                      <div>
                        <h2 style={{ margin: '0 0 4px 0' }}>⚖️ {arbitrationResult.verdict}</h2>
                        <p style={{ margin: 0, opacity: 0.9, fontSize: '0.9rem' }}>{arbitrationResult.summary}</p>
                      </div>
                      <div style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: '3rem', fontWeight: 'bold', lineHeight: 1 }}>{arbitrationResult.finalScore}%</div>
                        <div style={{ fontSize: '11px', opacity: 0.8 }}>Grand AI Score</div>
                      </div>
                    </div>
                    {/* Sub-scores breakdown */}
                    <div style={{ display: 'flex', gap: '8px', marginTop: '12px', flexWrap: 'wrap' }}>
                      {[
                        { label: 'Arbitrator + EXIF (40%)', val: arbitrationResult.finalScore },
                        { label: 'GPT-4o Direct (25%)', val: arbitrationResult.debateScore },
                        { label: 'Claude Vis + HF (20%)', val: arbitrationResult.claudeScore },
                        { label: 'Backend/HF (15%)', val: result.score },
                      ].map(s => (
                        <div key={s.label} style={{ flex: 1, minWidth: '90px', background: 'rgba(0,0,0,0.25)', borderRadius: '6px', padding: '6px 10px', textAlign: 'center' }}>
                          <div style={{ fontSize: '20px', fontWeight: 'bold' }}>{s.val}%</div>
                          <div style={{ fontSize: '10px', opacity: 0.7 }}>{s.label}</div>
                        </div>
                      ))}
                    </div>
                    <div style={{ marginTop: '10px' }}>
                      <div className="score-meter"><div className="score-fill" style={{ width: `${arbitrationResult.finalScore}%` }}></div></div>
                    </div>
                  </div>
                ) : (
                  /* Arbitration still running — show AACS score as placeholder */
                  <div className="verdict-banner" style={{ backgroundColor: '#1e40af', padding: '16px 24px' }}>
                    <h2 style={{ margin: '0 0 4px 0' }}>⏳ Awaiting Arbitration...</h2>
                    <p style={{ margin: 0, opacity: 0.8, fontSize: '0.9rem' }}>Backend AACS: {result.score}% — Multi-AI debate in progress</p>
                    <div className="score-meter" style={{ marginTop: '8px' }}><div className="score-fill" style={{ width: `${result.score}%`, background: 'rgba(255,255,255,0.4)' }}></div></div>
                  </div>
                )}

                <div className="details-grid">
                  <div className="card explanation">
                    <h3>Analysis Explanation</h3>
                    <div className="typed-text">
                      {/* Show arbitration summary if available, otherwise backend explanation */}
                      {arbitrationResult
                        ? <p>{arbitrationResult.summary}</p>
                        : result.explainability.text.split('\n').map((line, i) => <p key={i}>{line}</p>)
                      }
                    </div>
                  </div>

                  <div className="card heatmaps">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                      <h3 style={{ margin: 0 }}>{heatUrl ? "Claude Vision AI Regions" : "ELA Pixel Anomaly"}</h3>
                      {(heatUrl || result.explainability.ela_base64_heatmap_prefix) && (
                        <div style={{ display: "flex", gap: "6px" }}>
                          <button
                            onMouseEnter={() => setSliderPos(100)} // Using sliderPos as a boolean toggle (100 = show heat, 0 = hide heat)
                            onMouseLeave={() => setSliderPos(0)}
                            onClick={() => setSliderPos(prev => prev === 100 ? 0 : 100)}
                            style={{
                              padding: "6px 14px", fontSize: "12px", letterSpacing: "1px",
                              cursor: "pointer", borderRadius: "4px", fontWeight: "bold",
                              background: sliderPos === 100 ? "#ec4899" : "transparent",
                              border: "1px solid #ec4899",
                              color: sliderPos === 100 ? "#fff" : "#ec4899",
                              transition: "all 0.2s"
                            }}>
                            {sliderPos === 100 ? "HIDE HEATMAP" : "SHOW HEATMAP (HOVER)"}
                          </button>
                        </div>
                      )}
                    </div>

                    <div style={{ position: "relative", background: "#080808", textAlign: "center", borderRadius: "6px", overflow: "hidden" }}>
                      <img
                        src={previewUrl!}
                        alt="Original"
                        style={{ maxWidth: "100%", maxHeight: "500px", display: "block", margin: "0 auto" }}
                      />
                      {/* Heatmap Overlay */}
                      <img
                        src={heatUrl || result.explainability.ela_base64_heatmap_prefix}
                        alt="Heatmap"
                        style={{
                          position: "absolute", inset: 0, width: "100%", height: "100%",
                          objectFit: "contain", /* Ensure it perfectly aligns with the base image */
                          opacity: sliderPos === 100 ? 1 : 0,
                          transition: "opacity 0.3s ease",
                          pointerEvents: "none"
                        }}
                      />
                    </div>
                  </div>

                  <div className="card layers-breakdown">
                    <h3>10-Layer Signal Breakdown</h3>
                    <ul>
                      {arbitrationResult?.hfScore !== null && arbitrationResult?.hfScore !== undefined && (
                        <li><strong style={{ color: '#ec4899' }}>Hugging Face Model:</strong> {arbitrationResult.hfScore}% AI Probability</li>
                      )}
                      <li><strong>Pixel Manipulation (CNN):</strong> {result.signals.visual_forensics_mas.toFixed(1)} MAS</li>
                      <li><strong>Face Geometry (MediaPipe):</strong> {result.signals.face_geometry_pps.toFixed(1)} PPS</li>
                      <li><strong>GAN Frequencies (FFT):</strong> {result.signals.frequency.toFixed(1)} Freq</li>
                      <li><strong>Semantic Context (BART):</strong> {result.signals.semantic_context_irs.toFixed(1)} IRS</li>
                      <li><strong>Metadata Validity (EXIF):</strong> {result.signals.metadata_cvs.toFixed(1)} CVS</li>
                      {result.signals.diffusion_fingerprint !== undefined && (
                        <li><strong style={{ color: '#c084fc' }}>Diffusion Fingerprint (HF):</strong> {result.signals.diffusion_fingerprint.toFixed(1)} DIFF</li>
                      )}
                      {/* Phase 5 Arbitration sub-scores */}
                      {arbitrationResult && (
                        <>
                          <li style={{ borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '6px', marginTop: '6px' }}>
                            <strong style={{ color: '#fb923c' }}>Claude Vision (Puter):</strong> {arbitrationResult.claudeVerdict}
                          </li>
                          <li><strong style={{ color: '#a78bfa' }}>LLM Debate Score:</strong> {arbitrationResult.debateScore}%</li>
                        </>
                      )}
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      <Article />
    </div>
  );
}

export default App;
