import React, { useState } from 'react';
import {
    Shield, ShieldAlert, ShieldCheck, ShieldOff,
    Eye, Heart, Mic, Brain, Cpu, Activity,
    ChevronRight, AlertTriangle, CheckCircle2, Info,
    FileSearch, Clock, Target, Zap, Scan, Fingerprint,
    TrendingUp, BarChart2, BookOpen, Link2
} from 'lucide-react';

// ─── Verdict Configuration ───────────────────────────────────────────────────
const VERDICT = {
    AUTHENTIC:      { label: 'AUTHENTIC',      color: '#39ff14', bg: 'bg-green-500/10',   border: 'border-green-500/20',   text: 'text-green-400',   icon: ShieldCheck,  desc: 'No significant signs of AI manipulation detected.' },
    UNCERTAIN:      { label: 'UNCERTAIN',      color: '#ffd700', bg: 'bg-yellow-500/10',  border: 'border-yellow-500/20',  text: 'text-yellow-400',  icon: Shield,       desc: 'Mixed signals — proceed with caution.' },
    LIKELY_FAKE:    { label: 'LIKELY FAKE',    color: '#ff8c00', bg: 'bg-orange-500/10',  border: 'border-orange-500/20',  text: 'text-orange-400',  icon: ShieldAlert,  desc: 'Strong indicators of AI-generated or manipulated content.' },
    DEFINITELY_FAKE:{ label: 'DEFINITELY FAKE',color: '#ff3c00', bg: 'bg-red-500/10',     border: 'border-red-500/20',     text: 'text-red-400',     icon: ShieldOff,    desc: 'Multiple forensic engines confirm synthetic/deepfake media.' },
};
function getVerdict(score) {
    if (score < 30) return VERDICT.AUTHENTIC;
    if (score < 60) return VERDICT.UNCERTAIN;
    if (score < 85) return VERDICT.LIKELY_FAKE;
    return VERDICT.DEFINITELY_FAKE;
}

// ─── Human-readable engine metadata ─────────────────────────────────────────
const ENGINE_INFO = {
    'Spatio-Temporal-Analysis':  { name: 'Face Authenticity',    icon: Scan,        desc: 'Deep neural network scans facial textures for AI generation signatures.' },
    'Latent-Trajectory-Curvature':{ name: 'Physics Check',       icon: Activity,    desc: 'Checks if motion between frames follows natural physics or is synthetically generated.' },
    'Eye-Blink-EAR':             { name: 'Eye Blink Pattern',    icon: Eye,         desc: 'Real humans blink irregularly. AI-generated faces often have abnormal blink rates.' },
    'Face-Mesh-Tracking':        { name: 'Face Geometry',        icon: Fingerprint, desc: 'Tracks 468 facial landmarks to detect unnatural jitter or warping.' },
    'Eye-Reflection-Geometry':   { name: 'Light Reflection',     icon: Zap,         desc: 'Checks if light reflections in the eyes are physically consistent.' },
    'Lip-Sync-Correlation':      { name: 'Lip-Sync Accuracy',    icon: Mic,         desc: 'Compares mouth movements frame-by-frame against the audio track.' },
    'rPPG-Biological-Pulse':     { name: 'Biological Heartbeat', icon: Heart,       desc: 'Detects subtle skin color changes caused by blood flow — impossible to fake.' },
    'Audio-Spoof-Detection':     { name: 'Voice Clone Check',    icon: Mic,         desc: 'Analyzes vocal harmonics to detect AI-synthesized or cloned speech.' },
    'Semantic-Fact-Check':       { name: 'Context Verification', icon: Link2,       desc: 'Cross-references claims in the video against public fact-check databases.' },
};

// ─── Score color helpers ─────────────────────────────────────────────────────
function scoreColor(s) {
    if (s >= 70) return { text: 'text-red-400',    bar: '#ff3c00', label: 'High Risk' };
    if (s >= 40) return { text: 'text-yellow-400', bar: '#ffd700', label: 'Moderate' };
    return              { text: 'text-green-400',  bar: '#39ff14', label: 'Low Risk' };
}

// ─── Reusable Score Bar ───────────────────────────────────────────────────────
function ScoreBar({ score, color }) {
    return (
        <div className="h-1.5 bg-white/5 rounded-full overflow-hidden mt-2">
            <div className="h-full rounded-full transition-all duration-700" style={{ width: `${Math.min(score, 100)}%`, backgroundColor: color }} />
        </div>
    );
}

// ─── Tab Button ───────────────────────────────────────────────────────────────
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
function OverviewTab({ result, score, verdict }) {
    const V = verdict;
    const VIcon = V.icon;
    const ltca = result.ltca_data || {};
    const vd = ltca.video_description;
    const narrative = result.narrative;

    // Plain-English summary from the narrative
    const summary = typeof narrative === 'string'
        ? narrative
        : (narrative?.summary || narrative?.detailed || '');

    return (
        <div className="space-y-6">
            {/* Verdict hero */}
            <div className={`p-6 rounded-xl border ${V.bg} ${V.border} flex items-center gap-6`}>
                <div className={`p-4 rounded-full ${V.bg} border ${V.border}`}>
                    <VIcon className={`w-10 h-10 ${V.text}`} />
                </div>
                <div className="flex-1">
                    <div className={`text-3xl font-black tracking-widest ${V.text}`}>{V.label}</div>
                    <p className="text-white/60 text-sm mt-1">{V.desc}</p>
                    <div className="flex items-center gap-4 mt-3">
                        <div>
                            <span className={`text-5xl font-black ${V.text}`}>{Math.round(score)}</span>
                            <span className="text-white/30 text-sm font-mono ml-1">/ 100</span>
                        </div>
                        <div className="text-xs text-white/40 font-mono">
                            <div>AACS FAKE PROBABILITY SCORE</div>
                            <div className="mt-1">0–30 = Real · 31–60 = Uncertain · 61+ = Fake</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Sub-scores: human labels */}
            {result.sub_scores && (
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                    {[
                        { key: 'mas', label: 'Face Scan',    icon: Scan,        desc: 'Visual AI detection' },
                        { key: 'pps', label: 'Heartbeat',    icon: Heart,       desc: 'Biological signals' },
                        { key: 'irs', label: 'Context',      icon: BookOpen,    desc: 'Information risk' },
                        { key: 'aas', label: 'Voice',        icon: Mic,         desc: 'Audio analysis' },
                        { key: 'cvs', label: 'Sources',      icon: Link2,       desc: 'Cross-verification' },
                    ].map(({ key, label, icon: Icon, desc }) => {
                        const s = result.sub_scores[key] ?? 0;
                        const c = scoreColor(s);
                        return (
                            <div key={key} className="bg-white/[0.02] border border-white/5 rounded-lg p-3 flex flex-col gap-2">
                                <div className="flex items-center justify-between">
                                    <Icon className={`w-4 h-4 ${c.text}`} />
                                    <span className={`font-black text-sm ${c.text}`}>{Math.round(s)}%</span>
                                </div>
                                <div>
                                    <div className="text-white/80 text-xs font-bold">{label}</div>
                                    <div className="text-white/30 text-[10px]">{desc}</div>
                                </div>
                                <ScoreBar score={s} color={c.bar} />
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Plain English Summary */}
            {summary && (
                <div className="bg-white/[0.02] border border-white/5 rounded-xl p-5">
                    <div className="flex items-center gap-2 mb-3">
                        <Brain className="w-4 h-4 text-[#00f5ff]" />
                        <span className="text-[10px] font-bold uppercase tracking-widest text-white/40">AI Expert Summary</span>
                    </div>
                    <p className="text-white/80 text-sm leading-relaxed">{summary}</p>
                </div>
            )}

            {/* Quick scene info from Qwen */}
            {vd && (vd.setting !== 'N/A' || vd.people !== 'N/A') && (
                <div className="bg-white/[0.02] border border-white/5 rounded-xl p-5">
                    <div className="flex items-center gap-2 mb-4">
                        <FileSearch className="w-4 h-4 text-[#00f5ff]" />
                        <span className="text-[10px] font-bold uppercase tracking-widest text-white/40">Visual Content Summary</span>
                        <span className="ml-auto text-[9px] font-mono text-[#00f5ff]/50 bg-[#00f5ff]/5 px-2 py-0.5 rounded">Qwen3 VL</span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                        {[
                            { l: 'Scene', v: vd.setting },
                            { l: 'Subjects', v: vd.people },
                            { l: 'Activity', v: vd.activity },
                        ].filter(x => x.v && x.v !== 'N/A' && x.v !== 'Unknown').map(({ l, v }) => (
                            <div key={l}>
                                <div className="text-[10px] text-white/30 font-bold uppercase mb-1">{l}</div>
                                <div className="text-white/80">{v}</div>
                            </div>
                        ))}
                    </div>
                    {vd.verdict && vd.verdict !== 'UNKNOWN' && (
                        <div className={`mt-4 flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-bold border ${
                            vd.verdict === 'CLEAN' ? 'text-green-400 bg-green-500/10 border-green-500/20'
                            : vd.verdict === 'SUSPICIOUS' ? 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20'
                            : vd.verdict === 'LIKELY_AI' ? 'text-orange-400 bg-orange-500/10 border-orange-500/20'
                            : 'text-red-400 bg-red-500/10 border-red-500/20'
                        }`}>
                            <Eye className="w-3 h-3" />
                            Visual Verdict: {vd.verdict.replace('_', ' ')}
                            {vd.verdict_detail && <span className="font-normal ml-2 opacity-70">— {vd.verdict_detail.replace(/^(CLEAN|SUSPICIOUS|LIKELY_AI|DEFINITE_AI)\s*—?\s*/i, '')}</span>}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

// ─── DETECTORS TAB ────────────────────────────────────────────────────────────
function DetectorsTab({ result }) {
    const findings = result.findings || [];
    const ltca = result.ltca_data || {};

    // Build human-readable card for each engine
    const engineMap = {};
    findings.forEach(f => {
        if (f.engine && f.score != null) engineMap[f.engine] = f;
    });
    // Also add scores from ltca_data
    [
        { engine: 'Eye-Blink-EAR',          score: ltca.blink_score,   detail: ltca.blink_detail,   reasoning: ltca.blink_reasoning },
        { engine: 'Face-Mesh-Tracking',      score: ltca.mesh_score,    detail: ltca.mesh_detail,    reasoning: ltca.mesh_reasoning },
        { engine: 'Eye-Reflection-Geometry', score: ltca.reflect_score, detail: ltca.reflect_detail, reasoning: ltca.reflect_reasoning },
        { engine: 'Lip-Sync-Correlation',    score: ltca.sync_score,    detail: ltca.sync_detail,    reasoning: ltca.sync_reasoning },
    ].forEach(e => { if (e.score != null && !engineMap[e.engine]) engineMap[e.engine] = e; });

    const entries = Object.entries(engineMap).filter(([, v]) => v.score != null);

    if (!entries.length) return (
        <div className="text-white/30 text-sm text-center py-12">No engine data available.</div>
    );

    return (
        <div className="space-y-3">
            <p className="text-xs text-white/30 font-mono mb-4">
                Each detector below examines a different aspect of the video. <span className="text-green-400">Green = low risk</span>, <span className="text-yellow-400">yellow = moderate</span>, <span className="text-red-400">red = high risk</span>.
            </p>
            {entries.map(([key, finding]) => {
                const meta = ENGINE_INFO[key] || { name: key, icon: Activity, desc: 'Forensic analyzer.' };
                const Icon = meta.icon;
                const s = finding.score ?? 0;
                const c = scoreColor(s);

                return (
                    <div key={key} className="bg-white/[0.02] border border-white/5 rounded-xl p-4 hover:bg-white/[0.04] transition-colors">
                        <div className="flex items-center gap-3">
                            <div className={`p-2 rounded-lg bg-white/5`}>
                                <Icon className={`w-4 h-4 ${c.text}`} />
                            </div>
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center justify-between mb-0.5">
                                    <span className="font-bold text-white text-sm">{meta.name}</span>
                                    <span className={`font-black text-sm ${c.text}`}>{Math.round(s)}% <span className="font-normal text-[10px] opacity-60">{c.label}</span></span>
                                </div>
                                <p className="text-white/40 text-[11px]">{meta.desc}</p>
                            </div>
                        </div>
                        <ScoreBar score={s} color={c.bar} />
                        {(finding.detail || finding.reasoning) && (
                            <div className="mt-3 pl-2 border-l border-white/10">
                                {finding.reasoning && (
                                    <p className="text-white/60 text-[11px] italic">{finding.reasoning}</p>
                                )}
                                {finding.detail && !finding.reasoning && (
                                    <p className="text-white/50 text-[11px]">{finding.detail}</p>
                                )}
                            </div>
                        )}
                    </div>
                );
            })}

            {/* Biometric vitals strip */}
            {(ltca.rppg_bpm || ltca.blinks_detected != null || ltca.sync_correlation != null) && (
                <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-3">
                    {[
                        { l: 'Detected Heart Rate', v: ltca.rppg_bpm ? `${ltca.rppg_bpm} BPM` : null, good: ltca.rppg_bpm > 40 },
                        { l: 'Eye Blinks', v: ltca.blinks_detected != null ? `${ltca.blinks_detected} detected` : null, good: ltca.blinks_detected > 0 },
                        { l: 'AV Correlation', v: ltca.sync_correlation != null ? ltca.sync_correlation.toFixed(3) : null, good: ltca.sync_correlation > 0.3 },
                        { l: 'Temporal Drift', v: ltca.sync_offset != null ? `${ltca.sync_offset} frames` : null, good: Math.abs(ltca.sync_offset || 0) < 5 },
                    ].filter(x => x.v).map(({ l, v, good }) => (
                        <div key={l} className="bg-white/[0.02] border border-white/5 rounded-lg p-3 text-center">
                            <div className={`text-xl font-black ${good ? 'text-green-400' : 'text-red-400'}`}>{v}</div>
                            <div className="text-[10px] text-white/30 mt-1 uppercase">{l}</div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

// ─── FORENSIC AI TAB (Qwen Output) ───────────────────────────────────────────
function ForensicAITab({ ltca }) {
    const vd = ltca?.video_description;
    const sa = ltca?.semantic_analysis;

    if (!vd && !sa) return (
        <div className="text-center py-16 text-white/30">
            <Brain className="w-10 h-10 mx-auto mb-3 opacity-20" />
            <p className="text-sm">No AI forensic analysis data available.</p>
            <p className="text-xs mt-1 opacity-60">Make sure LM Studio is running with a vision model loaded.</p>
        </div>
    );

    return (
        <div className="space-y-6">
            {/* Video Description Panel */}
            {vd && (
                <div className="bg-white/[0.02] border border-white/5 rounded-xl overflow-hidden">
                    <div className="px-5 py-3 bg-[#00f5ff]/5 border-b border-[#00f5ff]/10 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <FileSearch className="w-4 h-4 text-[#00f5ff]" />
                            <span className="text-sm font-bold text-white">Visual Forensic Report</span>
                        </div>
                        <div className="flex items-center gap-2">
                            {vd.verdict && vd.verdict !== 'UNKNOWN' && (
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                                    vd.verdict === 'CLEAN' ? 'text-green-400 border-green-500/30 bg-green-500/10'
                                    : vd.verdict === 'SUSPICIOUS' ? 'text-yellow-400 border-yellow-500/30 bg-yellow-500/10'
                                    : vd.verdict === 'LIKELY_AI' ? 'text-orange-400 border-orange-500/30 bg-orange-500/10'
                                    : 'text-red-400 border-red-500/30 bg-red-500/10'
                                }`}>{vd.verdict.replace('_', ' ')}</span>
                            )}
                            <span className="text-[9px] font-mono text-[#00f5ff]/40 bg-[#00f5ff]/5 px-1.5 py-0.5 rounded">Qwen3 VL</span>
                        </div>
                    </div>
                    <div className="p-5 space-y-4">
                        {/* Fields */}
                        {[
                            { label: 'Scene Setting', value: vd.setting, icon: <Target className="w-3 h-3" /> },
                            { label: 'Identified Subjects', value: vd.people, icon: <Fingerprint className="w-3 h-3" /> },
                            { label: 'Detected Activity', value: vd.activity, icon: <Activity className="w-3 h-3" /> },
                            { label: 'Forensic Context', value: vd.context, icon: <FileSearch className="w-3 h-3" /> },
                        ].filter(x => x.value && x.value !== 'N/A' && x.value !== 'Unknown').map(({ label, value, icon }) => (
                            <div key={label} className="flex gap-4 pb-4 border-b border-white/5 last:border-0 last:pb-0">
                                <div className="w-32 shrink-0 flex items-center gap-1.5 text-white/30 text-[10px] font-bold uppercase tracking-wider pt-0.5">
                                    {icon} {label}
                                </div>
                                <p className="text-white/80 text-sm leading-relaxed">{value}</p>
                            </div>
                        ))}

                        {/* Artifacts */}
                        {vd.artifacts?.length > 0 && (
                            <div className="pt-2">
                                <div className="flex items-center gap-1.5 text-yellow-400/70 text-[10px] font-bold uppercase mb-2">
                                    <AlertTriangle className="w-3 h-3" /> Visual Artifacts Detected
                                </div>
                                <div className="flex flex-wrap gap-2">
                                    {vd.artifacts.map((a, i) => (
                                        <span key={i} className="px-2 py-1 bg-yellow-500/10 border border-yellow-500/20 rounded text-yellow-300/80 text-[11px]">{a}</span>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Moments Timeline */}
                        {vd.moments?.length > 0 && (
                            <div className="pt-2">
                                <div className="flex items-center gap-1.5 text-white/30 text-[10px] font-bold uppercase mb-2">
                                    <Clock className="w-3 h-3" /> Frame-by-Frame Timeline
                                </div>
                                <div className="space-y-2">
                                    {vd.moments.filter(m => m.trim().length > 4).map((m, i) => (
                                        <div key={i} className="flex items-start gap-3">
                                            <div className="w-5 h-5 shrink-0 rounded-full border border-[#00f5ff]/30 bg-[#00f5ff]/5 flex items-center justify-center text-[9px] font-bold text-[#00f5ff]/60">{i + 1}</div>
                                            <p className="text-white/60 text-xs pt-0.5">{m}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Verdict detail */}
                        {vd.verdict_detail && (
                            <div className="mt-2 p-3 bg-[#00f5ff]/5 border border-[#00f5ff]/10 rounded-lg">
                                <span className="text-[9px] font-bold text-[#00f5ff]/50 uppercase">AI Verdict Reasoning</span>
                                <p className="text-white/70 text-sm italic mt-1">"{vd.verdict_detail}"</p>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Semantic Intelligence Panel */}
            {sa && (
                <div className="bg-white/[0.02] border border-white/5 rounded-xl overflow-hidden">
                    <div className="px-5 py-3 bg-purple-500/5 border-b border-purple-500/10 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Brain className="w-4 h-4 text-purple-400" />
                            <span className="text-sm font-bold text-white">OSINT & Disinformation Analysis</span>
                        </div>
                        <div className={`px-2 py-0.5 rounded border text-[10px] font-bold ${
                            sa.risk_level === 'LOW' ? 'text-green-400 border-green-500/30 bg-green-500/10'
                            : sa.risk_level === 'MEDIUM' ? 'text-yellow-400 border-yellow-500/30 bg-yellow-500/10'
                            : sa.risk_level === 'HIGH' ? 'text-orange-400 border-orange-500/30 bg-orange-500/10'
                            : sa.risk_level === 'CRITICAL' ? 'text-red-400 border-red-500/30 bg-red-500/10'
                            : 'text-white/30 border-white/10'
                        }`}>RISK: {sa.risk_level}</div>
                    </div>
                    <div className="p-5 space-y-4">
                        {sa.description && (
                            <div>
                                <div className="text-[10px] text-white/30 font-bold uppercase mb-1">Scene Intelligence</div>
                                <p className="text-white/70 text-sm">{sa.description}</p>
                            </div>
                        )}
                        {sa.subjects && (
                            <div>
                                <div className="text-[10px] text-white/30 font-bold uppercase mb-1">Identified Subjects</div>
                                <p className="text-white/70 text-sm">{sa.subjects}</p>
                            </div>
                        )}
                        {sa.narrative_intent && (
                            <div>
                                <div className="text-[10px] text-white/30 font-bold uppercase mb-1">Narrative Intent</div>
                                <p className="text-white/70 text-sm">{sa.narrative_intent}</p>
                            </div>
                        )}

                        {sa.claims?.length > 0 && (
                            <div>
                                <div className="text-[10px] text-white/30 font-bold uppercase mb-2">Extracted Claims ({sa.claims.length})</div>
                                <div className="space-y-2">
                                    {sa.claims.map((c, i) => (
                                        <div key={i} className="p-3 bg-white/[0.02] border border-white/5 rounded-lg">
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-[#00f5ff]/10 text-[#00f5ff]/70">{c.category}</span>
                                                <span className={`text-[9px] font-bold ${
                                                    c.plausibility === 'PLAUSIBLE' ? 'text-green-400'
                                                    : c.plausibility === 'QUESTIONABLE' ? 'text-yellow-400'
                                                    : c.plausibility === 'SUSPICIOUS' ? 'text-orange-400'
                                                    : 'text-red-400'
                                                }`}>{c.plausibility}</span>
                                            </div>
                                            <p className="text-white/70 text-[12px]">"{c.text}"</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {sa.manipulation_indicators?.length > 0 && (
                            <div>
                                <div className="text-[10px] text-white/30 font-bold uppercase mb-2">Manipulation Patterns</div>
                                <ul className="space-y-1.5">
                                    {sa.manipulation_indicators.map((m, i) => (
                                        <li key={i} className="flex items-start gap-2 text-xs text-white/60">
                                            <AlertTriangle className="w-3 h-3 text-orange-400 shrink-0 mt-0.5" />
                                            {m}
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {sa.risk_justification && (
                            <div className="p-3 bg-white/[0.02] border border-white/5 rounded-lg">
                                <div className="text-[9px] text-white/30 font-bold uppercase mb-1">Intelligence Assessment</div>
                                <p className="text-white/70 text-sm italic">{sa.risk_justification}</p>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

// ─── EXPERT TAB (NLM + Technical data) ────────────────────────────────────────
function ExpertTab({ result }) {
    const ltca = result.ltca_data || {};
    const nlm = ltca.nlm_report || '';
    const fusion = result.cdcf || result.fusion;

    return (
        <div className="space-y-6">
            {nlm && (
                <div className="bg-white/[0.02] border border-white/5 rounded-xl p-5">
                    <div className="flex items-center gap-2 mb-4">
                        <Brain className="w-4 h-4 text-[#00f5ff]" />
                        <span className="text-sm font-bold text-white">Deep Expert Analysis (NLM)</span>
                        <span className="ml-auto text-[9px] font-mono text-white/30 bg-white/5 px-2 py-0.5 rounded">Groq Llama 3.3 70B</span>
                    </div>
                    <div className="space-y-4">
                        {nlm.split('\n\n').filter(p => p.trim()).map((para, i) => (
                            <p key={i} className={`font-mono text-sm leading-relaxed ${
                                i === 0 ? 'text-white/90 font-semibold'
                                : 'text-white/60'
                            }`}>{para.trim()}</p>
                        ))}
                    </div>
                </div>
            )}

            {fusion && (
                <div className="bg-white/[0.02] border border-white/5 rounded-xl p-5">
                    <div className="flex items-center gap-2 mb-4">
                        <Cpu className="w-4 h-4 text-[#00f5ff]" />
                        <span className="text-sm font-bold text-white">CDCF Fusion Engine</span>
                        <span className="ml-auto text-[9px] font-mono text-white/30">{fusion.fusion_method || 'CDCF + XGBoost'}</span>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                        {[
                            { l: 'Multiplier', v: `${(fusion.multiplier || 1).toFixed(2)}x` },
                            { l: 'Consensus', v: `${fusion.consensus ?? '--'}%` },
                            { l: 'Confidence', v: `${fusion.confidence ?? '--'}%` },
                            { l: 'Contradictions', v: fusion.contradictions?.length ?? 0 },
                        ].map(({ l, v }) => (
                            <div key={l} className="text-center p-3 bg-white/[0.02] border border-white/5 rounded-lg">
                                <div className="text-lg font-black text-[#00f5ff]">{v}</div>
                                <div className="text-[10px] text-white/30 uppercase">{l}</div>
                            </div>
                        ))}
                    </div>
                    {fusion.contradictions?.length > 0 && (
                        <div>
                            <div className="text-[10px] text-white/30 uppercase font-bold mb-2">Engine Contradictions</div>
                            <div className="flex flex-wrap gap-2">
                                {fusion.contradictions.map((c, i) => (
                                    <span key={i} className="px-2 py-1 bg-yellow-500/10 border border-yellow-500/20 rounded text-yellow-400 text-[11px] font-mono">{c}</span>
                                ))}
                            </div>
                        </div>
                    )}
                    {fusion.confidence_note && (
                        <p className="mt-3 text-xs text-white/40 italic">{fusion.confidence_note}</p>
                    )}
                </div>
            )}

            {/* Raw ltca data telemetry */}
            {ltca && (
                <div className="bg-white/[0.02] border border-white/5 rounded-xl p-5">
                    <div className="flex items-center gap-2 mb-4">
                        <BarChart2 className="w-4 h-4 text-[#00f5ff]" />
                        <span className="text-sm font-bold text-white">Raw Sensor Telemetry</span>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3 font-mono text-xs">
                        {[
                            { l: 'Spatial Score', v: ltca.spatial_score },
                            { l: 'Temporal Penalty', v: ltca.temporal_penalty },
                            { l: 'Noise Score', v: ltca.noise_score },
                            { l: 'Artifact Penalty', v: ltca.artifact_penalty },
                            { l: 'Curvature Index', v: ltca.curvature_score },
                            { l: 'Velocity Variance', v: ltca.velocity_variance },
                            { l: 'Physics Flagged', v: ltca.is_fake != null ? (ltca.is_fake ? 'YES' : 'NO') : null },
                            { l: 'rPPG BPM', v: ltca.rppg_bpm },
                            { l: 'rPPG SNR', v: ltca.rppg_snr != null ? (ltca.rppg_snr < 0.05 ? 'NOISE' : ltca.rppg_snr.toFixed(3)) : null },
                        ].filter(x => x.v != null).map(({ l, v }) => (
                            <div key={l} className="flex justify-between p-2 bg-white/[0.02] border border-white/5 rounded">
                                <span className="text-white/30">{l}</span>
                                <span className="text-[#00f5ff] font-bold">{typeof v === 'number' ? v.toFixed(2) : v}</span>
                            </div>
                        ))}
                    </div>
                    {ltca.reason && (
                        <div className="mt-3 p-3 bg-white/[0.02] border-l-2 border-[#00f5ff]/30 rounded-r-lg">
                            <span className="text-[10px] text-white/30 uppercase">Physics Engine Diagnosis</span>
                            <p className="text-white/60 text-xs mt-1">{ltca.reason}</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

// ─── MAIN COMPONENT ───────────────────────────────────────────────────────────
export default function VideoResultDashboard({ result }) {
    const [tab, setTab] = useState('overview');
    if (!result) return null;

    const score = result.score ?? result.aacs_score ?? 0;
    const verdict = getVerdict(score);
    const ltca = result.ltca_data || {};
    const hasAI = ltca.video_description || ltca.semantic_analysis;
    const nlmFindings = result.findings || [];

    const tabs = [
        { id: 'overview',   label: 'Overview',         icon: TrendingUp },
        { id: 'detectors',  label: 'Detection Engines', icon: Scan,      badge: nlmFindings.length || undefined },
        { id: 'forensicai', label: 'AI Forensic Report',icon: Brain,     badge: hasAI ? '✓' : undefined },
        { id: 'expert',     label: 'Expert / Raw Data', icon: Cpu },
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
            <div className="p-6">
                {tab === 'overview'   && <OverviewTab   result={result} score={score} verdict={verdict} />}
                {tab === 'detectors'  && <DetectorsTab  result={result} />}
                {tab === 'forensicai' && <ForensicAITab ltca={ltca} />}
                {tab === 'expert'     && <ExpertTab     result={result} />}
            </div>
        </div>
    );
}
