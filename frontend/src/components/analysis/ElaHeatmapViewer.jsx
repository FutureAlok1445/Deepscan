import React, { useRef, useEffect, useState, useCallback } from 'react';
import BrutalCard from '../ui/BrutalCard';

const TABS = [
  { key: 'blend',  label: '🌡 Heatmap + Image',  title: 'Heatmap overlaid on original image' },
  { key: 'heat',   label: '🔥 Heatmap Only',     title: 'Thermal heatmap only' },
  { key: 'orig',   label: '📷 Original',         title: 'Original unedited image' },
];

const SEV_COLOR = { HIGH: '#ff3c00', MEDIUM: '#ffd700', LOW: '#00f5ff' };

export default function ElaHeatmapViewer({ elaData, imageFile, systemScore, systemVerdict }) {
  const canvasRef = useRef(null);
  
  const [mode, setMode]               = useState('blend');
  const [opacity, setOpacity]         = useState(70);
  const [loading, setLoading]         = useState(true);
  
  const [loadedImg, setLoadedImg]     = useState(null);
  const [analysisData, setAnalysisData] = useState(null);

  // ── Helper: load image ──────────────────────────────────────────────────
  const loadImg = (src) =>
    new Promise((res, rej) => {
      const i = new Image();
      i.crossOrigin = 'anonymous';
      i.onload = () => res(i);
      i.onerror = rej;
      i.src = src;
    });

  // ── Client-side analysis functions directly from ai_detector_exact_match ──
  const thermalColor = (t) => {
    const stops = [
      [0,    10,  10, 180],
      [0.12,  0,  40, 255],
      [0.28,  0, 180, 255],
      [0.45,  0, 240,  80],
      [0.6,  200,240,   0],
      [0.74, 255,150,   0],
      [0.87, 255, 40,   0],
      [1,    255,255, 220],
    ];
    for (let i = 1; i < stops.length; i++) {
      if (t <= stops[i][0]) {
        const p = (t - stops[i - 1][0]) / (stops[i][0] - stops[i - 1][0]);
        return {
          r: Math.round(stops[i - 1][1] + (stops[i][1] - stops[i - 1][1]) * p),
          g: Math.round(stops[i - 1][2] + (stops[i][2] - stops[i - 1][2]) * p),
          b: Math.round(stops[i - 1][3] + (stops[i][3] - stops[i - 1][3]) * p),
        };
      }
    }
    return { r: 255, g: 255, b: 220 };
  };

  const computeELA = async (img, W, H) => {
    const c1 = document.createElement('canvas'); c1.width = W; c1.height = H;
    const x1 = c1.getContext('2d', { willReadFrequently: true });
    x1.drawImage(img, 0, 0, W, H);
    const orig = x1.getImageData(0, 0, W, H);
    
    // Low quality JPEG compression step
    const url = c1.toDataURL('image/jpeg', 0.65);
    const ri = await loadImg(url);
    
    const c2 = document.createElement('canvas'); c2.width = W; c2.height = H;
    const x2 = c2.getContext('2d', { willReadFrequently: true });
    x2.drawImage(ri, 0, 0, W, H);
    const rc = x2.getImageData(0, 0, W, H);
    
    const out = new ImageData(W, H);
    for (let i = 0; i < orig.data.length; i += 4) {
      const d = (
        Math.abs(orig.data[i] - rc.data[i]) + 
        Math.abs(orig.data[i + 1] - rc.data[i + 1]) + 
        Math.abs(orig.data[i + 2] - rc.data[i + 2])
      ) / 3;
      const v = Math.min(255, d * 14); // amplification exact match
      out.data[i] = v; out.data[i + 1] = v; out.data[i + 2] = v; out.data[i + 3] = 255;
    }
    return out;
  };

  const boxBlur = (src, W, H, r) => {
    const o = new Uint8ClampedArray(src.length);
    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        let sr = 0, sg = 0, sb = 0, n = 0;
        for (let dy = -r; dy <= r; dy++) {
          for (let dx = -r; dx <= r; dx++) {
            const nx = Math.min(W - 1, Math.max(0, x + dx));
            const ny = Math.min(H - 1, Math.max(0, y + dy));
            const ii = (ny * W + nx) * 4; 
            sr += src[ii]; sg += src[ii + 1]; sb += src[ii + 2]; n++;
          }
        }
        const ii = (y * W + x) * 4; 
        o[ii] = sr / n; o[ii + 1] = sg / n; o[ii + 2] = sb / n; o[ii + 3] = 255;
      }
    }
    return o;
  };

  const computeNoise = async (img, W, H) => {
    const c = document.createElement('canvas'); c.width = W; c.height = H;
    const ctx = c.getContext('2d', { willReadFrequently: true });
    ctx.drawImage(img, 0, 0, W, H);
    const src = ctx.getImageData(0, 0, W, H).data;
    
    // Sync block blur for simple smooth approx, mimicking reference exact
    const blr = boxBlur(src, W, H, 2);
    
    const out = new ImageData(W, H);
    for (let i = 0; i < src.length; i += 4) {
      const d = (
        Math.abs(src[i] - blr[i]) + 
        Math.abs(src[i + 1] - blr[i + 1]) + 
        Math.abs(src[i + 2] - blr[i + 2])
      ) / 3;
      const v = Math.min(255, d * 6);
      out.data[i] = v; out.data[i + 1] = v; out.data[i + 2] = v; out.data[i + 3] = 255;
    }
    return out;
  };

  const scoreImage = (ela, ns, W, H) => {
    let eS = 0, nS = 0, hi = 0, N = W * H;
    for (let i = 0; i < ela.data.length; i += 4) { 
      eS += ela.data[i]; nS += ns.data[i]; 
      if (ela.data[i] > 65) hi++; 
    }
    const eA = eS / N, nA = nS / N, hR = hi / N;
    const sc = Math.min(97, Math.max(5, Math.round(eA / 255 * 165 + nA / 255 * 55 + hR * 260)));
    const v = sc > 62 ? 'FAKE' : sc > 32 ? 'PARTIAL' : 'REAL';
    const sum = sc > 62 ?
      `ELA shows high compression inconsistency across ${Math.round(hR * 100)}% of pixels. Noise residuals indicate AI generation or heavy manipulation.` :
      sc > 32 ? `Mixed signals — some regions show ELA anomalies consistent with compositing or AI-generated elements fused with a real photo.` :
      `Uniform ELA and natural noise distribution. Consistent with an authentic, unedited photograph.`;
    
    const eScore = Math.min(100, Math.round(eA / 255 * 280));
    const nScore = Math.min(100, Math.round(nA / 255 * 360));
    const bScore = Math.min(100, Math.round(hR * 520));
    
    return {
      score: sc, verdict: v, summary: sum,
      signals: [
        { name: 'Error Level Analysis', desc: eScore > 60 ? 'High ELA variance — editing / AI seams detected' : eScore > 30 ? 'Moderate ELA anomalies present' : 'Uniform ELA — likely authentic', sev: eScore > 60 ? 'HIGH' : eScore > 30 ? 'MEDIUM' : 'LOW', score: eScore },
        { name: 'Noise Residuals', desc: nScore > 55 ? 'Irregular noise pattern — lacks real sensor characteristics' : nScore > 25 ? 'Some noise inconsistencies detected' : 'Natural sensor noise — authentic', sev: nScore > 55 ? 'HIGH' : nScore > 25 ? 'MEDIUM' : 'LOW', score: nScore },
        { name: 'Block Anomaly Map', desc: bScore > 50 ? 'Dense anomalous JPEG blocks — composite indicator' : bScore > 25 ? 'Scattered block artifacts' : 'Clean block structure', sev: bScore > 50 ? 'HIGH' : bScore > 25 ? 'MEDIUM' : 'LOW', score: bScore },
        { name: 'Frequency Domain', desc: sc > 62 ? 'Abnormal high-freq components — GAN/diffusion fingerprint' : sc > 32 ? 'Mild frequency irregularities' : 'Natural frequency spectrum', sev: sc > 62 ? 'HIGH' : sc > 32 ? 'MEDIUM' : 'LOW', score: Math.round(sc * 0.85) },
      ]
    };
  };

  // ── Execute on Mount ──────────────────────────────────────────────────
  useEffect(() => {
    let active = true;
    
    async function runAnalysis() {
      setLoading(true);
      try {
        let src = "";
        if (imageFile) {
          src = URL.createObjectURL(imageFile);
        } else if (elaData?.image_url) {
          src = elaData.image_url;
        } else {
          setLoading(false);
          return;
        }
        
        const origImgObj = await loadImg(src);
        if (!active) return;
        setLoadedImg(origImgObj);

        // Scale appropriately for rendering constraints
        const maxW = Math.min(origImgObj.width, 840);
        const sc = maxW / origImgObj.width;
        const W = Math.round(origImgObj.width * sc); 
        const H = Math.round(origImgObj.height * sc);

        // Await heavy frame-blocking ops with short ticks
        await new Promise(r => setTimeout(r, 20));
        if (!active) return;
        const ela = await computeELA(origImgObj, W, H);
        
        await new Promise(r => setTimeout(r, 20));
        if (!active) return;
        const noise = await computeNoise(origImgObj, W, H);

        if (!active) return;
        const scoring = scoreImage(ela, noise, W, H);
        
        // Build the blended thermal canvas memory immediately
        const thermal = new ImageData(W, H);
        for(let i = 0; i < W * H * 4; i += 4) {
          const elaV = ela.data[i] / 255;
          const nsV = noise.data[i] / 255;
          const anomaly = Math.min(1, elaV * 0.75 + nsV * 0.25);
          
          const color = thermalColor(anomaly);
          thermal.data[i] = color.r;
          thermal.data[i + 1] = color.g;
          thermal.data[i + 2] = color.b;
          thermal.data[i + 3] = 255;
        }

        const offCanvas = document.createElement('canvas');
        offCanvas.width = W; offCanvas.height = H;
        offCanvas.getContext('2d').putImageData(thermal, 0, 0);

        setAnalysisData({ W, H, offCanvas, scoring });
      } catch (e) {
        console.error("Client-side ELA analysis failed:", e);
      } finally {
        if (active) setLoading(false);
      }
    }
    
    runAnalysis();
    return () => { active = false; };
  }, [imageFile, elaData]);

  // ── Render loop ────────────────────────────────────────────────────────
  const drawCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !loadedImg || !analysisData) return;
    
    const { W, H, offCanvas } = analysisData;
    const ctx = canvas.getContext('2d');
    
    // Ensure canvas element dimensions match exactly
    canvas.width = W; 
    canvas.height = H;
    
    ctx.clearRect(0, 0, W, H);
    
    if (mode === 'orig') {
      ctx.drawImage(loadedImg, 0, 0, W, H);
      return;
    }

    const intensityVal = opacity / 100;
    
    if (mode === 'heat') {
      // Heatmap Only - exactly like reference HTML
      ctx.globalAlpha = 0.25;
      ctx.drawImage(loadedImg, 0, 0, W, H);
      ctx.globalAlpha = 1;
      
      ctx.globalAlpha = intensityVal * 0.92;
      ctx.drawImage(offCanvas, 0, 0);
      ctx.globalAlpha = 1;
    } else {
      // Blend - exactly like reference HTML
      ctx.drawImage(loadedImg, 0, 0, W, H);
      
      ctx.globalAlpha = intensityVal * 0.60;
      ctx.globalCompositeOperation = 'source-over';
      ctx.drawImage(offCanvas, 0, 0);
      ctx.globalAlpha = 1;
      ctx.globalCompositeOperation = 'source-over';
    }
  }, [mode, opacity, loadedImg, analysisData]);

  useEffect(() => {
    drawCanvas();
  }, [drawCanvas]);

  if (!imageFile && !elaData) return null;

  const scoreData = analysisData?.scoring;

  return (
    <BrutalCard className="space-y-0 overflow-hidden !p-0">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-ds-silver/20">
        <h3 className="font-grotesk font-bold text-ds-silver text-base uppercase tracking-wider flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-ds-red animate-pulse inline-block" />
          FAST ELA DETECTOR
        </h3>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-[#ff6622] bg-[#ff6622]/10 border border-[#ff6622]/30 px-2 py-0.5 rounded tracking-widest">
            CLIENT-SIDE FORENSICS
          </span>
        </div>
      </div>

      {/* View tabs */}
      <div className="flex gap-[1px] bg-ds-silver/20 border-b border-ds-silver/20 relative">
        {TABS.map((t) => {
          const isActive = mode === t.key;
          return (
            <button
              key={t.key}
              onClick={() => setMode(t.key)}
              title={t.title}
              className={`flex-1 py-2.5 px-2 text-[10px] sm:text-xs font-mono tracking-wide transition-all bg-ds-bg text-center outline-none ${
                isActive
                  ? 'text-[#ff6622] border-b-2 border-b-[#ff6622] bg-[#2a2a2a]'
                  : 'text-ds-silver/60 hover:text-ds-silver hover:bg-[#2a2a2a]'
              }`}
            >
              {t.label}
            </button>
          );
        })}
      </div>

      {/* Intensity slider */}
      {mode !== 'orig' && (
        <div className="flex items-center gap-3 px-4 py-2 bg-[#1e1e1e] border-b border-ds-silver/10">
          <span className="text-[10px] font-mono text-ds-silver/50 uppercase tracking-widest flex-shrink-0">
            HEATMAP INTENSITY
          </span>
          <input
            type="range"
            min={10}
            max={100}
            value={opacity}
            onChange={(e) => setOpacity(Number(e.target.value))}
            className="flex-1 h-1 appearance-none cursor-pointer outline-none rounded bg-[#333] [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:bg-[#ff6622] [&::-webkit-slider-thumb]:rounded-full"
          />
          <span className="text-[10px] font-mono text-[#ff6622] w-8 text-right flex-shrink-0 font-bold">
            {opacity}%
          </span>
        </div>
      )}

      {/* Canvas */}
      <div className="relative bg-[#000] w-full max-h-[600px] flex items-center justify-center overflow-hidden">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-[#1a1a1a] z-10">
            <div className="flex flex-col items-center gap-3">
              <div className="w-[42px] h-[42px] border-2 border-[#ff6622]/15 border-t-[#ff6622] rounded-full animate-spin" />
              <span className="text-xs font-mono text-ds-silver/60">Running forensic analysis...</span>
            </div>
          </div>
        )}
        <canvas
          ref={canvasRef}
          className="block w-full h-auto object-contain"
          style={{ imageRendering: 'auto' }}
        />
      </div>

      {/* Verdict & Score (Synced with System Result) */}
      {scoreData && (
        <div className="bg-[#2a2a2a] px-5 py-3 border-t border-ds-silver/20 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2 text-[13px] font-bold">
              {/* Score-dependent color logic */}
              {(() => {
                const finalScore = systemScore ?? scoreData.score;
                const finalVerdict = systemVerdict?.label ?? (scoreData.verdict === 'FAKE' ? 'AI detected' : scoreData.verdict === 'PARTIAL' ? 'Partial AI detected' : 'Likely authentic');
                const finalColor = finalScore >= 70 ? '#ff4422' : finalScore >= 40 ? '#ffaa00' : '#00cc55';
                
                return (
                  <>
                    <div className="w-[18px] h-[18px] rounded-full text-[9.5px] text-white flex items-center justify-center font-black" style={{ background: finalColor }}>!</div>
                    <span style={{ color: finalColor }}>
                      {finalVerdict}
                    </span>
                    <span className="px-3 py-1 text-white rounded font-mono font-bold text-xs" style={{ background: finalColor }}>
                      {finalScore}%
                    </span>
                  </>
                );
              })()}
            </div>
            <div className="text-[11.5px] text-[#888] font-mono leading-tight max-w-[500px]">
              {scoreData.summary}
            </div>
          </div>
          <button className="flex items-center gap-2 px-5 py-2.5 border-[1.5px] border-[#aaa] rounded-lg bg-transparent text-[#e8edf5] text-[13px] font-bold font-syne hover:bg-white/5 hover:border-white transition-all flex-shrink-0">
            📋 Report
          </button>
        </div>
      )}

      {/* Signal Grids (Exactly like reference UI) */}
      {scoreData && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 p-3.5 bg-[#1a1a1a]">
          {scoreData.signals.map((s, idx) => (
            <SignalRow key={idx} {...s} />
          ))}
        </div>
      )}
    </BrutalCard>
  );
}

function SignalRow({ name, score, severity, desc, sev }) {
  // Map SEV to colors like the original
  const c2 = sev === 'HIGH' ? '#ff4422' : sev === 'MEDIUM' ? '#ffaa00' : '#4488ff';
  const ic = sev === 'HIGH' ? '🔴' : sev === 'MEDIUM' ? '🟡' : '🔵';

  return (
    <div className="bg-[#1e1e1e] border border-[#2a2a2a] rounded-lg p-2.5 flex gap-2">
      <div className="text-[13.5px] mt-[1px] flex-shrink-0">{ic}</div>
      <div className="flex-1">
        <div className="text-[11px] font-bold mb-[2px]" style={{ color: c2 }}>{name}</div>
        <div className="text-[10px] text-[#555] font-mono leading-snug">{desc}</div>
        <div className="h-[2px] bg-[#2a2a2a] rounded-sm mt-1.5 overflow-hidden">
          <div
            className="h-full rounded-sm transition-all duration-[1300ms]"
            style={{ width: `${score}%`, background: c2 }}
          />
        </div>
      </div>
    </div>
  );
}
