import React, { useState } from 'react';
import {
    Shield, ShieldAlert, ShieldCheck, ShieldOff,
    Eye, Cpu, CheckCircle2,
    FileSearch, Zap, Scan, Fingerprint, Activity,
    TrendingUp, BarChart2, BookOpen, Link2, Aperture, Ghost, Radar
} from 'lucide-react';
import ArbitrationSystem from './ArbitrationSystem';

// ─── Human-readable engine metadata ─────────────────────────────────────────
const ENGINE_INFO = {
    'metadata_cvs':          { name: 'EXIF & Metadata',          icon: BookOpen,    desc: 'Deep inspection of EXIF tags for software manipulation signatures.' },
    'visual_forensics_mas':  { name: 'Visual CNN Forensics',     icon: Scan,        desc: 'Detects spatial manipulation patterns using Vision Transformers.' },
    'face_geometry_pps':     { name: 'Facial Geometry',          icon: Fingerprint, desc: 'Analyzes facial symmetry and biological blending boundaries.' },
    'frequency':             { name: 'Frequency Domain (FFT)',   icon: Activity,    desc: 'Analyzes spatial frequency spectra for unnatural GAN-generated periodic noise.' },
    'semantic_context_irs':  { name: 'Contextual Plausibility',  icon: Link2,       desc: 'Evaluates scene physics and object lighting consistency.' },
    'diffusion_fingerprint': { name: 'Diffusion Noise Pattern',  icon: Ghost,       desc: 'Scans for subtle pixel-level noise artifacts unique to Midjourney/DALL-E.' },
};

function scoreColor(s) {
    if (s >= 70) return { text: 'text-red-400',    bar: '#ff3c00', label: 'High Risk' };
    if (s >= 40) return { text: 'text-yellow-400', bar: '#ffd700', label: 'Moderate' };
    return              { text: 'text-green-400',  bar: '#39ff14', label: 'Low Risk' };
}

function ScoreBar({ score, color }) {
    return (
        <div className="h-1.5 bg-white/5 rounded-full overflow-hidden mt-2">
            <div className="h-full rounded-full transition-all duration-700" style={{ width: `${Math.min(score, 100)}%`, backgroundColor: color }} />
        </div>
    );
}

function Tab({ label, active, onClick, icon: Icon, badge }) {
    return (
        <button
            onClick={onClick}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold uppercase tracking-widest border-b-2 transition-all whitespace-nowrap ${
                active
                    ? 'border-[#00f5ff] text-[#00f5ff]'
                    : 'border-transparent text-white/30 hover:text-white/60 hover:border-white/20'
            }`}
        >
            {Icon && <Icon className="w-3.5 h-3.5" />}
            {label}
            {badge != null && (
                <span className={`px-1.5 py-0.5 rounded text-[9px] font-black ${active ? 'bg-[#00f5ff]/20 text-[#00f5ff]' : 'bg-white/10 text-white/40'}`}>
                    {badge}
                </span>
            )}
        </button>
    );
}

// ─── OVERVIEW TAB ─────────────────────────────────────────────────────────────
function OverviewTab({ result }) {
    const data = result.image_data || {};
    const explain = data.explainability || {};
    const signals = data.signals || {};
    const narrative = result.narrative || {};
    
    // Attempt fallback to standard Result fields for non-10-layer legacy backend outputs
    const summary = explain.text || narrative.summary || narrative.detailed || "No detailed AI summary provided.";

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
                {[
                    { key: 'metadata_cvs',          label: 'Metadata',  icon: BookOpen },
                    { key: 'visual_forensics_mas',  label: 'CNN Vis',   icon: Scan },
                    { key: 'face_geometry_pps',     label: 'Face X-Ray',icon: Fingerprint },
                    { key: 'frequency',             label: 'FFT Spectra',icon: Activity },
                    { key: 'semantic_context_irs',  label: 'Semantics', icon: Link2 },
                    { key: 'diffusion_fingerprint', label: 'Diffusion', icon: Ghost },
                ].map(({ key, label, icon: Icon }) => {
                    const s = signals[key] ?? 0;
                    const c = scoreColor(s);
                    return (
                        <div key={key} className="bg-white/[0.02] border border-white/5 rounded-lg p-3 flex flex-col gap-2">
                            <div className="flex items-center justify-between">
                                <Icon className={`w-4 h-4 ${c.text}`} />
                                <span className={`font-black text-xs ${c.text}`}>{Math.round(s)}%</span>
                            </div>
                            <div>
                                <div className="text-white/80 text-xs font-bold whitespace-nowrap overflow-hidden text-ellipsis">{label}</div>
                            </div>
                            <ScoreBar score={s} color={c.bar} />
                        </div>
                    );
                })}
            </div>

            {/* Plain English Summary */}
            <div className="bg-white/[0.02] border border-white/5 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-3">
                    <CheckCircle2 className="w-4 h-4 text-[#00f5ff]" />
                    <span className="text-[10px] font-bold uppercase tracking-widest text-white/40">Diagnostic Conclusion</span>
                </div>
                {summary.split('\n\n').map((para, i) => (
                    <p key={i} className={`text-sm leading-relaxed mb-3 last:mb-0 ${i === 0 ? 'text-white/90 font-semibold' : 'text-white/70'}`}>
                        {para.trim()}
                    </p>
                ))}
            </div>
            
            {/* If Legacy Findings Exist */}
            {result.findings && result.findings.length > 0 && !data.signals && (
                <div className="bg-white/[0.02] border border-white/5 rounded-xl p-5">
                    <h4 className="text-[10px] font-bold uppercase tracking-widest text-white/40 mb-3">Legacy Scan Details</h4>
                    <div className="space-y-3">
                        {result.findings.map((f, i) => {
                            const c = scoreColor(f.score ?? 0);
                            return (
                                <div key={i} className="flex items-center justify-between bg-white/[0.01] p-3 rounded">
                                    <div>
                                        <div className="text-white/90 font-bold text-sm">{f.engine}</div>
                                        <div className="text-white/50 text-xs">{f.detail}</div>
                                    </div>
                                    <div className={`font-black ${c.text}`}>{f.score ?? 0}%</div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
}

// ─── HEATMAPS & REGIONS TAB ───────────────────────────────────────────────────
function HeatmapsTab({ explain, originalImage }) {
    // If no data, show placeholder
    if (!explain?.ela_base64_heatmap_prefix && (!explain?.regions || explain.regions.length === 0)) {
        return (
            <div className="text-center py-16 text-white/30">
                <Radar className="w-10 h-10 mx-auto mb-3 opacity-20" />
                <p className="text-sm">No spatial heatmaps available for this image.</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* 1. Error Level Analysis Heatmap */}
                {explain.ela_base64_heatmap_prefix && (
                    <div className="bg-white/[0.02] border border-white/5 rounded-xl overflow-hidden p-4">
                        <div className="flex items-center gap-2 mb-4">
                            <Aperture className="w-4 h-4 text-[#00f5ff]" />
                            <span className="text-sm font-bold text-white">ELA Error Intensity Heatmap</span>
                            <span className="ml-auto text-[9px] font-mono text-[#00f5ff]/50 bg-[#00f5ff]/5 px-2 py-0.5 rounded">Pixel Layer</span>
                        </div>
                        <div className="relative aspect-video bg-black rounded-lg overflow-hidden border border-white/10 flex items-center justify-center">
                            <img 
                                src={explain.ela_base64_heatmap_prefix} 
                                alt="ELA Heatmap" 
                                className="max-w-full max-h-full object-contain mix-blend-screen"
                                onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display='block'; }}
                            />
                            <div className="hidden text-white/30 text-xs text-center px-4">Image data corrupt or unavailable</div>
                        </div>
                        <p className="text-xs text-white/40 mt-3 italic">
                            Error Level Analysis (ELA) highlights areas of an image that are saved at different compression levels. High contrast regions (bright spots) strongly indicate splicing or deepfake manipulation.
                        </p>
                    </div>
                )}
                
                {/* 2. Original Image / Bounding Boxes (Claude Vision Regions) */}
                <div className="bg-white/[0.02] border border-white/5 rounded-xl p-4 flex flex-col">
                    <div className="flex items-center gap-2 mb-4">
                        <Eye className="w-4 h-4 text-orange-400" />
                        <span className="text-sm font-bold text-white">Suspect Regions Identified</span>
                        <span className="ml-auto text-[9px] font-mono text-orange-400/50 bg-orange-400/5 px-2 py-0.5 rounded">Claude Vision</span>
                    </div>
                    {explain.regions && explain.regions.length > 0 ? (
                        <div className="space-y-3 flex-1">
                            {explain.regions.map((reg, i) => (
                                <div key={i} className="bg-orange-500/10 border border-orange-500/20 rounded p-3 text-sm">
                                    <div className="flex justify-between items-start mb-1">
                                        <div className="font-bold text-orange-400">{reg.label}</div>
                                        <div className="text-xs font-mono bg-orange-500/20 text-orange-300 px-1.5 py-0.5 rounded">Confidence: {(reg.intensity * 100).toFixed(0)}%</div>
                                    </div>
                                    <div className="text-xs text-orange-200/60 font-mono break-words">
                                        Coordinates: {JSON.stringify(reg.polygon || [])}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="flex-1 flex flex-col items-center justify-center text-white/30 py-8 border border-dashed border-white/10 rounded-lg">
                            <CheckCircle2 className="w-8 h-8 mb-2 opacity-50 text-green-500" />
                            <p className="text-sm">No suspicious visual anomalies isolated.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

// ─── RAW TELEMETRY TAB ────────────────────────────────────────────────────────
function TelemetryTab({ result }) {
    const data = result.image_data || {};
    const signals = data.signals || {};

    return (
        <div className="space-y-6">
            <div className="bg-white/[0.02] border border-white/5 rounded-xl p-5">
                <div className="flex items-center gap-2 mb-4">
                    <BarChart2 className="w-4 h-4 text-[#00f5ff]" />
                    <span className="text-sm font-bold text-white">Full Domain Layer Analysis</span>
                </div>
                <div className="space-y-4">
                    {Object.entries(ENGINE_INFO).map(([key, meta]) => {
                        const score = signals[key];
                        if (score === undefined) return null;
                        const c = scoreColor(score);
                        const Icon = meta.icon;

                        return (
                            <div key={key} className="bg-white/[0.01] border border-white/5 rounded-lg p-4 hover:bg-white/[0.03] transition-colors">
                                <div className="flex items-center gap-3">
                                    <div className={`p-2 rounded-lg bg-white/5`}>
                                        <Icon className={`w-4 h-4 ${c.text}`} />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center justify-between mb-0.5">
                                            <span className="font-bold text-white text-sm">{meta.name}</span>
                                            <span className={`font-black text-sm ${c.text}`}>{Math.round(score)}%</span>
                                        </div>
                                        <p className="text-white/40 text-[11px]">{meta.desc}</p>
                                    </div>
                                </div>
                                <ScoreBar score={score} color={c.bar} />
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Fusion Details */}
            {result.cdcf && (
                <div className="bg-white/[0.02] border border-white/5 rounded-xl p-5">
                    <div className="flex items-center gap-2 mb-4">
                        <Cpu className="w-4 h-4 text-[#b966ff]" />
                        <span className="text-sm font-bold text-white">Fusion Engine (CDCF)</span>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-center">
                        {[
                            { l: 'Method', v: result.cdcf.fusion_method || 'AI Fusion' },
                            { l: 'Confidence', v: `${result.cdcf.confidence ?? '--'}%` },
                            { l: 'Multiplier Applied', v: `${(result.cdcf.multiplier || 1).toFixed(2)}x` },
                            { l: 'Contradictions Blocked', v: result.cdcf.contradictions?.length ?? 0 },
                        ].map(({ l, v }) => (
                            <div key={l} className="p-3 bg-white/[0.02] border border-white/5 rounded-lg">
                                <div className="text-sm md:text-lg font-black text-[#b966ff]">{v}</div>
                                <div className="text-[10px] text-white/30 uppercase mt-1">{l}</div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

// ─── MAIN COMPONENT ───────────────────────────────────────────────────────────
export default function ImageResultDashboard({ result, originalFile }) {
    const [tab, setTab] = useState('overview');
    if (!result) return null;

    const explain = result.image_data?.explainability || {};
    const hasHeatmap = !!explain.ela_base64_heatmap_prefix || (explain.regions && explain.regions.length > 0);
    const score = result.score ?? result.aacs_score ?? 0;

    // Use the base64 URL from result if originalFile (File object) is missing (extension flow)
    const displayImage = originalFile || result.original_image_url;

    const tabs = [
        { id: 'overview',   label: 'Overview',         icon: TrendingUp },
        { id: 'heatmaps',   label: 'Forensic Radar',   icon: Aperture, badge: hasHeatmap ? '✓' : undefined },
        { id: 'expert',     label: 'Engine Telemetry', icon: Cpu },
        { id: 'debate',     label: 'Live AI Debate',   icon: Zap,      badge: 'BETA' },
    ];

    return (
        <div className="w-full bg-[#0a0a0a] border border-white/5 rounded-2xl overflow-hidden shadow-2xl">
            {/* Tab Bar */}
            <div className="flex overflow-x-auto border-b border-white/5 bg-white/[0.01] scrollbar-none">
                {tabs.map(t => (
                    <Tab key={t.id} label={t.label} active={tab === t.id} onClick={() => setTab(t.id)} icon={t.icon} badge={t.badge} />
                ))}
            </div>

            {/* Tab Content */}
            <div className="p-4 sm:p-6">
                {tab === 'overview'   && <OverviewTab   result={result} />}
                {tab === 'heatmaps'   && <HeatmapsTab   explain={explain} originalImage={displayImage} />}
                {tab === 'expert'     && <TelemetryTab  result={result} />}
                
                {/* The Arbitration System runs as its own self-contained widget here */}
                <div style={{ display: tab === 'debate' ? 'block' : 'none' }}>
                    <div className="mb-4">
                        <h3 className="text-white font-bold text-lg flex items-center gap-2">
                            <Zap className="w-5 h-5 text-yellow-400" /> Multi-AI Forensic Debate
                        </h3>
                        <p className="text-white/50 text-xs mt-1">
                            An experimental system where Claude 3.5 Sonnet (Authenticator) and GPT-4o (Detector) argue the authenticity of this image, and Llama 3 70B acts as the final judge. Runs entirely in your browser.
                        </p>
                    </div>
                    <ArbitrationSystem imageFile={displayImage} backendScore={score} />
                </div>
            </div>
        </div>
    );
}
