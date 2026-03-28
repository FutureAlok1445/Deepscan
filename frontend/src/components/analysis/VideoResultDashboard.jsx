import React, { useState, useMemo } from 'react';
import {
    Shield, ShieldAlert, ShieldCheck, ShieldOff,
    Eye, Heart, Mic, Brain, Cpu, Activity,
    AlertTriangle, CheckCircle2, Info,
    FileSearch, Clock, Target, Zap, Scan, Fingerprint,
    BarChart2, BookOpen, Link2, Film, ChevronDown, ChevronUp,
    Layers, FileVideo, List
} from 'lucide-react';


// ─── Verdict config ───────────────────────────────────────────────────────────
const VERDICT = {
    AUTHENTIC:       { label: 'AUTHENTIC',       color: '#22c55e', bg: 'rgba(34,197,94,0.08)',   border: 'rgba(34,197,94,0.25)',   text: 'text-green-400',  ring: '#22c55e', icon: ShieldCheck, desc: 'No significant signs of AI manipulation detected.' },
    PARTIALLY_AI:    { label: 'UNCERTAIN',        color: '#eab308', bg: 'rgba(234,179,8,0.08)',   border: 'rgba(234,179,8,0.25)',   text: 'text-yellow-400', ring: '#eab308', icon: Shield,      desc: 'Mixed signals — some AI elements detected. Proceed with caution.' },
    LIKELY_FAKE:     { label: 'LIKELY FAKE',      color: '#f97316', bg: 'rgba(249,115,22,0.08)',  border: 'rgba(249,115,22,0.25)',  text: 'text-orange-400', ring: '#f97316', icon: ShieldAlert, desc: 'Strong indicators of AI-generated or manipulated content.' },
    DEFINITELY_FAKE: { label: 'CONFIRMED FAKE',   color: '#ef4444', bg: 'rgba(239,68,68,0.08)',   border: 'rgba(239,68,68,0.25)',   text: 'text-red-400',    ring: '#ef4444', icon: ShieldOff,   desc: 'Multiple forensic engines confirm synthetic/deepfake media.' },
};
function getVerdict(score) {
    if (score <= 34) return VERDICT.AUTHENTIC;
    if (score <= 65) return VERDICT.PARTIALLY_AI;
    if (score <= 82) return VERDICT.LIKELY_FAKE;
    return VERDICT.DEFINITELY_FAKE;
}

// ─── Engine metadata ──────────────────────────────────────────────────────────
const ENGINE_INFO = {
    'Spatio-Temporal-Analysis':   { name: 'Face Authenticity',     icon: Scan,        desc: 'ViT neural network scans facial textures for AI generation signatures.' },
    'Latent-Trajectory-Curvature':{ name: 'Motion Physics',         icon: Activity,    desc: 'Verifies that motion follows natural physics rather than synthetic generation.' },
    'Eye-Blink-EAR':              { name: 'Blink Pattern',          icon: Eye,         desc: 'Real humans blink irregularly. AI faces often have abnormal blink rates.' },
    'Face-Mesh-Tracking':         { name: 'Face Geometry',          icon: Fingerprint, desc: 'Tracks 468 facial landmarks to detect unnatural jitter or warping.' },
    'Eye-Reflection-Geometry':    { name: 'Light Reflection',       icon: Zap,         desc: 'Checks if corneal reflections are physically consistent with the scene.' },
    'Lip-Sync-Correlation':       { name: 'Lip-Sync Accuracy',      icon: Mic,         desc: 'Compares mouth movements against the audio track frame-by-frame.' },
    'rPPG-Biological-Pulse':      { name: 'Biological Heartbeat',   icon: Heart,       desc: 'Detects subtle skin colour changes from blood flow — impossible to fake.' },
    'Audio-Spoof-Detection':      { name: 'Voice Clone Check',      icon: Mic,         desc: 'Analyses vocal harmonics to detect AI-synthesized or cloned speech.' },
    'Semantic-Fact-Check':        { name: 'Context Verification',   icon: Link2,       desc: 'Cross-references claims in the video against fact-check databases.' },
};

// ─── Helpers ──────────────────────────────────────────────────────────────────
function scoreColor(s) {
    if (s >= 70) return { text: 'text-red-400',    bar: '#ef4444', label: 'High Risk',  bg: 'bg-red-500/10' };
    if (s >= 40) return { text: 'text-yellow-400', bar: '#eab308', label: 'Moderate',   bg: 'bg-yellow-500/10' };
    return              { text: 'text-green-400',  bar: '#22c55e', label: 'Low Risk',   bg: 'bg-green-500/10' };
}

function ScoreBar({ score, color }) {
    return (
        <div className="h-1.5 bg-white/5 rounded-full overflow-hidden mt-2">
            <div className="h-full rounded-full transition-all duration-700"
                style={{ width: `${Math.min(score, 100)}%`, backgroundColor: color }} />
        </div>
    );
}

// Circular score ring (SVG)
function ScoreRing({ score, verdict, size = 140 }) {
    const V = verdict;
    const r = 52;
    const circ = 2 * Math.PI * r;
    const dash = circ * (1 - Math.min(score, 100) / 100);
    return (
        <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
            <svg width={size} height={size} viewBox="0 0 120 120">
                <circle cx="60" cy="60" r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
                <circle cx="60" cy="60" r={r} fill="none"
                    stroke={V.ring} strokeWidth="8"
                    strokeDasharray={circ} strokeDashoffset={dash}
                    strokeLinecap="round"
                    transform="rotate(-90 60 60)"
                    style={{ transition: 'stroke-dashoffset 1s ease' }}
                />
            </svg>
            <div className="absolute flex flex-col items-center">
                <span className={`text-3xl font-black ${V.text}`}>{Math.round(score)}</span>
                <span className="text-white/30 text-[10px] font-mono">/ 100</span>
            </div>
        </div>
    );
}

// ─── Score calculation (Qwen-dominant) ───────────────────────────────────────
/**
 * Weighted composite score:
 *   45% — Qwen VL verdict (keyword → numeric mapping)
 *   45% — average per-frame AI score from the 60-frame analysis
 *   10% — pipeline sub-scores average (mas+pps+irs+aas+cvs)
 */
function computeDisplayScore(result) {
    const ltca         = result.ltca_data || {};
    const vd           = ltca.video_description;
    const frameData    = ltca.frame_analyses || [];
    const subScores    = result.sub_scores || {};
    const rawAacs      = result.aacs_score ?? result.score ?? 50;

    // Qwen verdict → numeric
    let qwenScore = null;
    if (vd?.verdict) {
        const map = { DEFINITE_AI: 92, LIKELY_AI: 72, SUSPICIOUS: 52, CLEAN: 12, UNKNOWN: null };
        qwenScore = map[vd.verdict] ?? null;
    }

    // Frame average
    let frameAvg = null;
    if (frameData.length > 0) {
        frameAvg = frameData.reduce((a, f) => a + (f.score ?? 0), 0) / frameData.length;
    }

    // Sub-score average (pipeline)
    const subVals = Object.values(subScores).filter(v => typeof v === 'number');
    const subAvg  = subVals.length ? subVals.reduce((a, b) => a + b, 0) / subVals.length : rawAacs;

    // Blend
    if (qwenScore !== null && frameAvg !== null) {
        return Math.round(qwenScore * 0.45 + frameAvg * 0.45 + subAvg * 0.10);
    }
    if (qwenScore !== null) {
        return Math.round(qwenScore * 0.80 + subAvg * 0.20);
    }
    if (frameAvg !== null) {
        return Math.round(frameAvg * 0.80 + subAvg * 0.20);
    }
    return Math.round(rawAacs);
}

// ─────────────────────────────────────────────────────────────────────────────
// SIMPLE VIEW
// ─────────────────────────────────────────────────────────────────────────────
function SimpleView({ result, score, verdict }) {
    const V   = verdict;
    const VIcon = V.icon;
    const ltca = result.ltca_data || {};
    const vd   = ltca.video_description;
    const sa   = ltca.semantic_analysis;

    const qwenText = vd?.description || vd?.context || null;
    const frameData = ltca.frame_analyses || [];
    const frameAvg = frameData.length
        ? Math.round(frameData.reduce((a, f) => a + (f.score ?? 0), 0) / frameData.length)
        : null;

    return (
        <div className="space-y-5">
            {/* ── Hero verdict card ─────────────────────────────────── */}
            <div className="rounded-2xl p-6 flex flex-col sm:flex-row items-center sm:items-start gap-6"
                style={{ background: V.bg, border: `1.5px solid ${V.border}` }}>
                <ScoreRing score={score} verdict={V} size={130} />
                <div className="flex-1">
                    <div className="flex items-center gap-3 mb-1">
                        <VIcon className={`w-6 h-6 ${V.text}`} />
                        <span className={`text-2xl font-black tracking-widest ${V.text}`}>{V.label}</span>
                    </div>
                    <p className="text-white/60 text-sm leading-relaxed mb-4">{V.desc}</p>

                    {/* Score breakdown pills */}
                    <div className="flex flex-wrap gap-2">
                        {vd?.verdict && vd.verdict !== 'UNKNOWN' && (
                            <span className={`px-3 py-1 rounded-full text-xs font-bold border ${
                                vd.verdict === 'CLEAN' ? 'text-green-400 border-green-500/30 bg-green-500/10'
                                : vd.verdict === 'SUSPICIOUS' ? 'text-yellow-400 border-yellow-500/30 bg-yellow-500/10'
                                : 'text-red-400 border-red-500/30 bg-red-500/10'
                            }`}>
                                🔍 Qwen: {vd.verdict.replace('_', ' ')}
                            </span>
                        )}
                        {frameAvg !== null && (
                            <span className={`px-3 py-1 rounded-full text-xs font-bold border ${scoreColor(frameAvg).text} ${scoreColor(frameAvg).bg} border-white/10`}>
                                🎞 Frames avg: {frameAvg}%
                            </span>
                        )}
                        {sa?.risk_level && sa.risk_level !== 'UNKNOWN' && (
                            <span className={`px-3 py-1 rounded-full text-xs font-bold border ${
                                sa.risk_level === 'LOW' ? 'text-green-400 border-green-500/30 bg-green-500/10'
                                : sa.risk_level === 'MEDIUM' ? 'text-yellow-400 border-yellow-500/30 bg-yellow-500/10'
                                : sa.risk_level === 'CRITICAL' ? 'text-red-400 border-red-500/30 bg-red-500/10'
                                : 'text-orange-400 border-orange-500/30 bg-orange-500/10'
                            }`}>
                                ⚠ OSINT Risk: {sa.risk_level}
                            </span>
                        )}
                    </div>
                </div>
            </div>

            {/* ── Qwen AI Analysis card ─────────────────────────────── */}
            {qwenText && (
                <div className="rounded-2xl overflow-hidden"
                    style={{ border: '1px solid rgba(0,245,255,0.12)' }}>
                    <div className="flex items-center gap-2 px-5 py-3"
                        style={{ background: 'rgba(0,245,255,0.05)', borderBottom: '1px solid rgba(0,245,255,0.10)' }}>
                        <Brain className="w-4 h-4 text-[#00f5ff]" />
                        <span className="text-sm font-bold text-white">AI Forensic Analysis</span>
                        <span className="ml-auto text-[9px] font-mono text-[#00f5ff]/50 bg-[#00f5ff]/5 border border-[#00f5ff]/15 px-2 py-0.5 rounded">Qwen3 VL</span>
                    </div>
                    <div className="px-5 py-4 max-h-[420px] overflow-y-auto bg-black/20">
                        {qwenText.split('\n').map((line, i) => {
                            const t = line.trim();
                            if (!t) return <div key={i} className="mb-2" />;
                            const isH = t.startsWith('**') || t.startsWith('#');
                            const isB = t.startsWith('- ') || t.startsWith('* ') || t.startsWith('• ');
                            return (
                                <p key={i} className={
                                    isH ? 'text-[#00f5ff] text-xs font-bold uppercase tracking-wider mt-4 mb-1'
                                    : isB ? 'text-white/75 text-sm pl-3 border-l border-[#00f5ff]/20 mb-1.5'
                                    :       'text-white/82 text-sm leading-relaxed mb-1.5'
                                }>
                                    {line.replace(/\*\*/g, '').replace(/^#{1,3} /, '')}
                                </p>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* ── OSINT claims snippet ──────────────────────────────── */}
            {sa?.claims?.length > 0 && (
                <div className="rounded-xl p-4 space-y-2"
                    style={{ background: 'rgba(168,85,247,0.05)', border: '1px solid rgba(168,85,247,0.15)' }}>
                    <div className="flex items-center gap-2 mb-3">
                        <Target className="w-4 h-4 text-purple-400" />
                        <span className="text-sm font-bold text-white">Factual Claims Detected</span>
                    </div>
                    {sa.claims.slice(0, 3).map((c, i) => (
                        <div key={i} className="flex items-start gap-3 text-sm">
                            <span className={`mt-0.5 shrink-0 text-[10px] font-black px-1.5 py-0.5 rounded border ${
                                c.plausibility === 'SUSPICIOUS' || c.plausibility === 'IMPLAUSIBLE'
                                    ? 'text-red-400 border-red-500/30 bg-red-500/10'
                                    : 'text-green-400 border-green-500/30 bg-green-500/10'
                            }`}>{c.plausibility}</span>
                            <span className="text-white/70">{c.text}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

// ─────────────────────────────────────────────────────────────────────────────
// COMPLEX VIEW (TABBED & EUPHORIA AESTHETIC)
// ─────────────────────────────────────────────────────────────────────────────

// Reusable stat pill
function Stat({ label, value, color = 'text-white' }) {
    return (
        <div className="bg-white/[0.03] border border-white/5 rounded-2xl p-4 text-center hover:bg-white/[0.05] transition-colors">
            <div className={`text-2xl font-black tracking-tight ${color}`}>{value}</div>
            <div className="text-[10px] text-white/40 uppercase tracking-widest mt-1 font-mono">{label}</div>
        </div>
    );
}

function ComplexView({ result, score, verdict }) {
    const V     = verdict;
    const ltca  = result.ltca_data || {};
    const vd    = ltca.video_description || {};
    const sa    = ltca.semantic_analysis || {};
    const frameData = ltca.frame_analyses || [];
    const subScores = result.sub_scores || {};
    const findings  = result.findings || [];
    const audio  = result.audio || {};

    const qwenText = vd.description || vd.context;
    const hasAudio = audio.spectrum?.length > 0 || audio.clone_probability != null;
    const hasOsint = sa.description || sa.claims?.length > 0;
    const hasExpert = result.narrative?.detailed;

    // Build engine map
    const engineMap = {};
    findings.forEach(f => { if (f.engine && f.score != null) engineMap[f.engine] = f; });
    [
        { engine: 'Eye-Blink-EAR', score: ltca.blink_score, detail: ltca.blink_detail },
        { engine: 'Face-Mesh-Tracking', score: ltca.mesh_score, detail: ltca.mesh_detail },
        { engine: 'Eye-Reflection-Geometry', score: ltca.reflect_score, detail: ltca.reflect_detail },
        { engine: 'Lip-Sync-Correlation', score: ltca.sync_score, detail: ltca.sync_detail },
    ].forEach(e => { if (e.score != null && !engineMap[e.engine]) engineMap[e.engine] = e; });

    const frameAvg = frameData.length
        ? Math.round(frameData.reduce((a, f) => a + (f.score ?? 0), 0) / frameData.length)
        : null;

    // Tabs definition
    const tabs = [
        ...(qwenText ? [{ id: 'qwen', label: 'AI Forensics', icon: Brain, color: '#00f5ff' }] : []),
        ...(frameData.length > 0 ? [{ id: 'frames', label: 'Frames', badge: frameData.length, icon: Film, color: '#c084fc' }] : []),
        ...(Object.keys(engineMap).length > 0 ? [{ id: 'engines', label: 'Engines', icon: Cpu, color: '#e2e8f0' }] : []),
        ...(hasAudio ? [{ id: 'audio', label: 'Audio', icon: Mic, color: '#60a5fa' }] : []),
        ...(hasOsint ? [{ id: 'osint', label: 'OSINT', icon: Target, color: '#a855f7' }] : []),
        ...(hasExpert ? [{ id: 'expert', label: 'Summary', icon: BookOpen, color: '#a1a1aa' }] : []),
    ];

    const [activeTab, setActiveTab] = useState(tabs[0]?.id || 'qwen');

    return (
        <div className="space-y-6">

            {/* ── Top Score Banner ─────────────────────────────────── */}
            <div className="flex flex-col md:flex-row gap-4 items-stretch">
                <div className="flex-1 flex items-center justify-between rounded-3xl px-8 py-5 relative overflow-hidden group"
                    style={{ background: V.bg, border: `1.5px solid ${V.border}` }}>
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/[0.03] to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
                    <div className="flex items-center gap-6 relative z-10">
                        <ScoreRing score={score} verdict={V} size={90} />
                        <div>
                            <div className={`text-xl font-black tracking-widest uppercase ${V.text}`}>{V.label}</div>
                            <p className="text-white/60 text-xs mt-1.5 max-w-sm leading-relaxed">{V.desc}</p>
                            
                            <div className="flex items-center gap-2 mt-3 flex-wrap">
                                <span className="text-[9px] text-white/30 font-mono tracking-widest">WEIGHTS:</span>
                                <span className="text-[10px] font-bold text-[#00f5ff]/80 bg-[#00f5ff]/10 border border-[#00f5ff]/20 px-2 py-0.5 rounded-full">45% Qwen</span>
                                <span className="text-[10px] font-bold text-purple-400/80 bg-purple-500/10 border border-purple-500/20 px-2 py-0.5 rounded-full">45% Frames</span>
                                <span className="text-[10px] font-bold text-white/40 bg-white/5 border border-white/10 px-2 py-0.5 rounded-full">10% Pipeline</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Sub-score Mini-grid */}
                <div className="grid grid-cols-3 md:grid-cols-2 lg:grid-cols-3 gap-2 shrink-0 md:w-[320px]">
                    {[
                        { key: 'mas', label: 'Face Scan' },
                        { key: 'pps', label: 'Heartbeat' },
                        { key: 'aas', label: 'Voice' },
                        { key: 'irs', label: 'Context' },
                        { key: 'cvs', label: 'Sources' },
                    ].map(({ key, label }) => {
                        const s = subScores[key] ?? 0;
                        const c = scoreColor(s);
                        return (
                            <div key={key} className="bg-white/[0.02] border border-white/5 rounded-2xl flex flex-col justify-center items-center py-2 hover:bg-white/[0.04] transition-colors">
                                <span className={`text-sm font-black ${c.text}`}>{Math.round(s)}<span className="text-[9px] font-normal opacity-50">%</span></span>
                                <span className="text-[9px] text-white/30 tracking-wider uppercase mt-0.5">{label}</span>
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* ── Aesthetic Tab Bar ────────────────────────────────── */}
            <div className="flex items-center gap-2 overflow-x-auto pb-2 custom-scrollbar">
                {tabs.map(t => {
                    const isActive = activeTab === t.id;
                    const TIcon = t.icon;
                    return (
                        <button
                            key={t.id}
                            onClick={() => setActiveTab(t.id)}
                            className={`flex items-center gap-2 px-5 py-3 rounded-xl text-sm font-bold transition-all relative overflow-hidden group shrink-0 ${
                                isActive ? 'bg-white/10 text-white shadow-lg' : 'bg-transparent text-white/40 hover:text-white/80 hover:bg-white/5'
                            }`}
                            style={{
                                border: isActive ? `1px solid ${t.color}50` : '1px solid transparent',
                                boxShadow: isActive ? `0 4px 20px -5px ${t.color}30` : 'none'
                            }}
                        >
                            {/* Neon glow effect on active tab */}
                            {isActive && (
                                <div className="absolute top-0 left-0 right-0 h-[1.5px]" style={{ background: t.color, boxShadow: `0 0 10px ${t.color}` }} />
                            )}
                            <TIcon className={`w-4 h-4 transition-colors ${isActive ? '' : 'opacity-50'}`} style={{ color: isActive ? t.color : 'inherit' }} />
                            <span>{t.label}</span>
                            {t.badge && (
                                <span className="ml-1.5 text-[10px] bg-black/40 px-2 py-0.5 rounded-full border border-white/10 text-white/70">
                                    {t.badge}
                                </span>
                            )}
                        </button>
                    );
                })}
            </div>

            {/* ── Tab Content Container ─────────────────────────────── */}
            <div className="bg-black/20 border border-white/5 rounded-3xl p-6 md:p-8 min-h-[400px] relative overflow-hidden">
                
                {/* 1. QWEN AI FORENSICS TAB */}
                {activeTab === 'qwen' && qwenText && (
                    <div className="animate-in fade-in slide-in-from-bottom-2 duration-500">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="p-3 rounded-xl bg-[#00f5ff]/10 border border-[#00f5ff]/20">
                                <Brain className="w-5 h-5 text-[#00f5ff]" />
                            </div>
                            <div>
                                <h3 className="text-xl font-black text-white">Qwen3 VL Master Report</h3>
                                <p className="text-[#00f5ff]/70 text-xs mt-0.5 font-mono">Visual-Language AI Agent output</p>
                            </div>
                            {vd?.verdict && vd.verdict !== 'UNKNOWN' && (
                                <div className={`ml-auto px-4 py-1.5 rounded-full text-xs font-black border uppercase tracking-wider ${
                                    vd.verdict === 'CLEAN' ? 'text-green-400 border-green-500/30 bg-green-500/10'
                                    : vd.verdict === 'SUSPICIOUS' ? 'text-yellow-400 border-yellow-500/30 bg-yellow-500/10'
                                    : 'text-red-400 border-red-500/30 bg-red-500/10'
                                }`}>
                                    {vd.verdict.replace('_', ' ')}
                                </div>
                            )}
                        </div>
                        <div className="space-y-4 max-h-[500px] overflow-y-auto pr-4 custom-scrollbar text-white/80 leading-relaxed text-sm md:text-base">
                            {qwenText.split('\n').map((line, i) => {
                                const t = line.trim();
                                if (!t) return null;
                                const isH = t.startsWith('**') || t.startsWith('#');
                                const isB = t.startsWith('- ') || t.startsWith('* ') || t.startsWith('• ');
                                return (
                                    <p key={i} className={`
                                        ${isH ? 'text-[#00f5ff] text-base font-black tracking-normal mt-6 mb-2' 
                                          : isB ? 'pl-4 border-l-2 border-[#00f5ff]/30 mb-2 py-0.5 text-white/70' 
                                          : 'mb-3'}
                                    `}>
                                        {line.replace(/\*\*/g, '').replace(/^#{1,3} /, '')}
                                    </p>
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* 2. FRAME BY FRAME TAB */}
                {activeTab === 'frames' && frameData.length > 0 && (
                    <div className="animate-in fade-in slide-in-from-bottom-2 duration-500">
                        <div className="grid grid-cols-3 gap-4 mb-8">
                            <Stat label="Overall Average" value={`${frameAvg}%`} color={scoreColor(frameAvg).text} />
                            <Stat label="Highly Altered" value={frameData.filter(f => f.score >= 50).length} color="text-orange-400" />
                            <Stat label="Clean Frames" value={frameData.filter(f => f.score < 35).length} color="text-green-400" />
                        </div>
                        
                        <div className="mb-6 bg-white/[0.02] border border-white/5 rounded-xl p-4">
                            <h4 className="text-[10px] text-white/30 uppercase tracking-widest mb-3 font-mono">Frame Progression Map</h4>
                            <div className="flex items-end gap-1 h-12">
                                {frameData.map((f, i) => {
                                    const h = Math.max(10, Math.round(f.score * 0.5));
                                    const isHigh = f.score >= 70;
                                    const c = isHigh ? '#ef4444' : f.score >= 40 ? '#eab308' : '#22c55e';
                                    return (
                                        <div key={i} className="flex-1 rounded-sm relative group cursor-pointer transition-all hover:opacity-100"
                                            style={{ height: `${h}%`, backgroundColor: c, opacity: 0.6 }}
                                        >
                                            <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-black text-white text-[10px] font-bold py-1 px-2 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10 pointer-events-none">
                                                F{i}: {Math.round(f.score)}%
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>

                        <div className="grid grid-cols-4 sm:grid-cols-6 lg:grid-cols-10 gap-2">
                            {frameData.map((f, i) => {
                                const isHigh = f.score >= 70;
                                const isMed = f.score >= 40;
                                const borderColor = isHigh ? 'border-red-500/50' : isMed ? 'border-yellow-500/50' : 'border-green-500/20';
                                const bgColor = isHigh ? 'bg-red-500/10' : isMed ? 'bg-yellow-500/10' : 'bg-green-500/5';
                                return (
                                    <div key={i} className={`relative rounded-lg overflow-hidden border ${borderColor} ${bgColor} transition-transform hover:scale-[1.05] hover:z-10 bg-black`}>
                                        {f.image_b64
                                            ? <img src={f.image_b64} alt={`frame ${i}`} className="w-full aspect-square object-cover" />
                                            : <div className="w-full aspect-square flex items-center justify-center opacity-30"><Film className="w-4 h-4" /></div>
                                        }
                                        <div className="absolute bottom-0 inset-x-0 h-1/2 bg-gradient-to-t from-black/90 to-transparent pointer-events-none" />
                                        <span className={`absolute bottom-1 right-1.5 text-[9px] font-black ${isHigh ? 'text-red-400' : isMed ? 'text-yellow-400' : 'text-green-400'}`}>
                                            {Math.round(f.score)}%
                                        </span>
                                        <span className="absolute top-1 left-1.5 text-[7px] text-white/50 font-mono">#{i}</span>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* 3. ENGINES TAB */}
                {activeTab === 'engines' && Object.keys(engineMap).length > 0 && (
                    <div className="animate-in fade-in slide-in-from-bottom-2 duration-500">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {Object.entries(engineMap).map(([key, finding]) => {
                                const meta = ENGINE_INFO[key] || { name: key, icon: Activity, desc: '' };
                                const Icon = meta.icon;
                                const s = finding.score ?? 0;
                                const c = scoreColor(s);
                                return (
                                    <div key={key} className="bg-white/[0.02] border border-white/5 rounded-2xl p-5 hover:bg-white/[0.04] transition-colors relative overflow-hidden group">
                                        <div className={`absolute top-0 left-0 w-1 h-full opacity-50 group-hover:opacity-100 transition-opacity`} style={{ background: c.bar }} />
                                        <div className="flex items-center justify-between mb-4">
                                            <div className="flex items-center gap-3">
                                                <div className="p-2.5 rounded-xl bg-black/40 border border-white/10">
                                                    <Icon className={`w-4 h-4 ${c.text}`} />
                                                </div>
                                                <div>
                                                    <div className="font-bold text-white text-sm">{meta.name}</div>
                                                    <p className="text-white/40 text-[10px] uppercase font-mono mt-0.5">{meta.desc || 'Forensic Pipeline'}</p>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <div className={`text-xl font-black ${c.text}`}>{Math.round(s)}<span className="text-xs font-normal opacity-50">%</span></div>
                                                <div className={`text-[9px] uppercase font-bold ${c.text} border border-current px-1.5 py-0.5 rounded opacity-80 mt-1 inline-block`}>{c.label}</div>
                                            </div>
                                        </div>
                                        <ScoreBar score={s} color={c.bar} />
                                        {(finding.reasoning || finding.detail) && (
                                            <p className="mt-4 text-white/60 text-xs italic pl-3 border-l-2" style={{ borderColor: c.bar }}>
                                                {finding.reasoning || finding.detail}
                                            </p>
                                        )}
                                    </div>
                                );
                            })}
                        </div>

                        {/* Extra vital metrics from video processing if available */}
                        {(ltca.rppg_bpm || ltca.blinks_detected != null || ltca.sync_correlation != null) && (
                            <div className="mt-8">
                                <h3 className="text-xs font-mono text-white/30 uppercase tracking-widest mb-4">Extracted Biometrics</h3>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    {[
                                        { l: 'Heart Rate Mapping', v: ltca.rppg_bpm ? `${ltca.rppg_bpm} BPM` : null, good: ltca.rppg_bpm > 40 },
                                        { l: 'Involuntary Blinks', v: ltca.blinks_detected != null ? `${ltca.blinks_detected}` : null, good: ltca.blinks_detected > 0 },
                                        { l: 'Audio-Video Sync', v: ltca.sync_correlation?.toFixed(3) ?? null, good: ltca.sync_correlation > 0.3 },
                                        { l: 'Temporal Drift', v: ltca.sync_offset != null ? `${ltca.sync_offset}f` : null, good: Math.abs(ltca.sync_offset || 0) < 5 },
                                    ].filter(x => x.v).map(({ l, v, good }) => (
                                        <div key={l} className="bg-black/30 border border-white/5 rounded-2xl p-4 flex flex-col items-center justify-center text-center">
                                            <span className={`text-xl font-bold ${good ? 'text-green-400' : 'text-orange-400'}`}>{v}</span>
                                            <span className="text-[10px] text-white/40 uppercase mt-1">{l}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* 4. AUDIO TAB */}
                {activeTab === 'audio' && hasAudio && (
                    <div className="animate-in fade-in slide-in-from-bottom-2 duration-500">
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
                            <Stat label="Voice Clone Risk" value={`${Math.round(audio.clone_probability ?? 0)}%`} color={scoreColor(audio.clone_probability ?? 0).text} />
                            <Stat label="Splice Detection" value={audio.splicing_detected ? '⚠ Detected' : '✓ Clean'} color={audio.splicing_detected ? 'text-red-400' : 'text-green-400'} />
                            {Object.entries(audio.signature_scores || {}).slice(0, 2).map(([k, v]) => (
                                <Stat key={k} label={k.replace(/_/g, ' ')} value={`${Math.round(v)}%`} color={scoreColor(v).text} />
                            ))}
                        </div>
                        {audio.anomalies?.length > 0 && (
                            <div className="bg-orange-500/10 border border-orange-500/20 rounded-2xl p-5">
                                <h3 className="text-xs font-bold text-orange-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                                    <AlertTriangle className="w-4 h-4" /> Detected Anomalies
                                </h3>
                                <div className="space-y-2">
                                    {audio.anomalies.map((a, i) => (
                                        <div key={i} className="text-sm text-orange-200/80 bg-black/20 p-2.5 rounded-lg">
                                            {a}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* 5. OSINT TAB */}
                {activeTab === 'osint' && hasOsint && (
                    <div className="animate-in fade-in slide-in-from-bottom-2 duration-500 space-y-6">
                        {sa.risk_level && sa.risk_level !== 'UNKNOWN' && (
                            <div className={`inline-block px-4 py-1.5 rounded-full text-xs font-black border uppercase tracking-wider mb-2 ${
                                sa.risk_level === 'LOW' ? 'text-green-400 border-green-500/30 bg-green-500/10'
                                : sa.risk_level === 'MEDIUM' ? 'text-yellow-400 border-yellow-500/30 bg-yellow-500/10'
                                : sa.risk_level === 'CRITICAL' ? 'text-red-400 border-red-500/30 bg-red-500/10'
                                : 'text-orange-400 border-orange-500/30 bg-orange-500/10'
                            }`}>
                                Overall Threat Level: {sa.risk_level}
                            </div>
                        )}
                        
                        {sa.description && (
                            <p className="text-white/80 text-sm leading-relaxed max-w-3xl">{sa.description}</p>
                        )}

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {sa.claims?.length > 0 && (
                                <div className="bg-white/[0.02] border border-white/5 rounded-2xl p-5">
                                    <h4 className="text-[10px] text-purple-400 font-bold uppercase tracking-widest mb-4 flex items-center gap-2">
                                        <Target className="w-3 h-3" /> Factual Claims Analyzed
                                    </h4>
                                    <div className="space-y-3">
                                        {sa.claims.map((c, i) => (
                                            <div key={i} className="flex items-start gap-3 bg-black/30 p-3 rounded-xl border border-white/5">
                                                <span className={`shrink-0 text-[10px] font-black px-1.5 py-0.5 rounded border ${
                                                    c.plausibility === 'SUSPICIOUS' || c.plausibility === 'IMPLAUSIBLE'
                                                        ? 'text-red-400 border-red-500/30 bg-red-500/10'
                                                        : c.plausibility === 'QUESTIONABLE'
                                                        ? 'text-yellow-400 border-yellow-500/30 bg-yellow-500/10'
                                                        : 'text-green-400 border-green-500/30 bg-green-500/10'
                                                }`}>{c.category}</span>
                                                <div className="flex-1">
                                                    <p className="text-white/80 text-sm mb-1 leading-snug">{c.text}</p>
                                                    <span className={`text-[9px] font-bold uppercase tracking-wide ${
                                                        c.plausibility === 'SUSPICIOUS' || c.plausibility === 'IMPLAUSIBLE'
                                                            ? 'text-red-400' : c.plausibility === 'QUESTIONABLE'
                                                            ? 'text-yellow-400' : 'text-green-400'
                                                    }`}>{c.plausibility}</span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <div className="space-y-6">
                                {sa.manipulation_indicators?.length > 0 && (
                                    <div className="bg-orange-500/5 border border-orange-500/20 rounded-2xl p-5">
                                        <h4 className="text-[10px] text-orange-400 font-bold uppercase tracking-widest mb-3">Red Flags</h4>
                                        <div className="space-y-2">
                                            {sa.manipulation_indicators.map((m, i) => (
                                                <div key={i} className="flex items-start gap-2 text-sm text-orange-200/80 bg-black/20 p-2.5 rounded-lg">
                                                    <AlertTriangle className="w-4 h-4 shrink-0 text-orange-400 mt-0.5" />
                                                    {m}
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                                {sa.narrative_intent && (
                                    <div className="bg-purple-500/10 border border-purple-500/20 rounded-2xl p-5 relative overflow-hidden">
                                        <div className="absolute -right-4 -top-4 opacity-10">
                                            <Brain className="w-24 h-24 text-purple-400" />
                                        </div>
                                        <h4 className="text-[10px] text-purple-300 font-bold uppercase tracking-widest mb-2 relative z-10">Identified Intent</h4>
                                        <p className="text-purple-100/80 text-sm leading-relaxed relative z-10">{sa.narrative_intent}</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}

                {/* 6. EXPERT SUMMARY TAB */}
                {activeTab === 'expert' && hasExpert && (
                    <div className="animate-in fade-in slide-in-from-bottom-2 duration-500 max-w-3xl">
                        <div className="bg-white/[0.02] border border-white/5 rounded-2xl p-6 md:p-8">
                            <h3 className="text-sm font-bold text-white mb-4 flex items-center gap-2">
                                <BookOpen className="w-5 h-5 text-white/50" />
                                Executive Summary
                            </h3>
                            <p className="text-white/80 text-base leading-relaxed tracking-wide mb-6">{result.narrative.detailed}</p>
                            
                            {result.narrative.technical && (
                                <div>
                                    <h4 className="text-[10px] text-white/30 uppercase tracking-widest mb-2 font-mono">Technical Breakdown</h4>
                                    <div className="bg-black/40 border border-white/10 rounded-xl p-4">
                                        <p className="text-white/40 text-xs font-mono leading-relaxed">{result.narrative.technical}</p>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN COMPONENT
// ─────────────────────────────────────────────────────────────────────────────
export default function VideoResultDashboard({ result }) {
    const [complexView, setComplexView] = useState(false);

    const score   = useMemo(() => computeDisplayScore(result), [result]);
    const verdict = useMemo(() => getVerdict(score), [score]);

    return (
        <div className="space-y-5">
            {/* ── Top bar: file info + view toggle ─────────────────── */}
            <div className="flex items-center justify-between flex-wrap gap-3">
                <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-[#00f5ff]/10 border border-[#00f5ff]/20">
                        <FileVideo className="w-5 h-5 text-[#00f5ff]" />
                    </div>
                    <div>
                        <div className="text-sm font-bold text-white truncate max-w-[220px]">
                            {result.original_filename || result.filename || 'Video Analysis'}
                        </div>
                        <div className="text-[10px] text-white/30 font-mono">
                            {result.elapsed_seconds != null ? `Processed in ${result.elapsed_seconds}s` : 'Analysis complete'}
                        </div>
                    </div>
                </div>

                {/* View toggle */}
                <button
                    onClick={() => setComplexView(v => !v)}
                    className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all"
                    style={{
                        background: complexView ? 'rgba(0,245,255,0.10)' : 'rgba(255,255,255,0.04)',
                        border: complexView ? '1px solid rgba(0,245,255,0.25)' : '1px solid rgba(255,255,255,0.08)',
                        color: complexView ? '#00f5ff' : 'rgba(255,255,255,0.5)',
                    }}
                >
                    <Layers className="w-4 h-4" />
                    {complexView ? 'Simple View' : 'Detailed View'}
                </button>
            </div>

            {/* ── View content ──────────────────────────────────────── */}
            {complexView
                ? <ComplexView result={result} score={score} verdict={verdict} />
                : <SimpleView  result={result} score={score} verdict={verdict} />
            }
        </div>
    );
}
