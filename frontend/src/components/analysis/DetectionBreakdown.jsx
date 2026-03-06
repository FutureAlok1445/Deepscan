import React from 'react';
import { Eye, Activity, Waves, Brain, Scan, Zap, Radio, Shield } from 'lucide-react';
import BrutalCard from '../ui/BrutalCard';

const ENGINE_META = {
    // Classic engines — mapped by engine name from backend findings
    'Spatio-Temporal-Analysis': { label: 'Spatio-Temporal', icon: Scan, desc: 'ViT + Optical Flow' },
    'Latent-Trajectory-Curvature': { label: 'Physics (LTCA)', icon: Activity, desc: 'Latent space physics' },
    'rPPG-Heartbeat': { label: 'Heartbeat (rPPG)', icon: Radio, desc: 'Facial blood-flow pulse' },
    'Audio-Spoof-Detection': { label: 'Audio Clone', icon: Waves, desc: '9-signature voice analysis' },
    // Audio deep signatures
    'F0-Stability-Analysis': { label: 'F0 Vocal Stability', icon: Waves, desc: 'Fundamental frequency jitter' },
    'Vocal-Tract-Consistency': { label: 'Vocal Tract Length', icon: Activity, desc: 'LPC-based VTL physics' },
    'Spectral-Mirroring-Check': { label: 'Spectral Mirroring', icon: Radio, desc: 'Upsampling aliasing peaks' },
    'MFCC-Articulatory-Dynamics': { label: 'Articulatory Flow', icon: Waves, desc: 'MFCC delta-delta variance' },
    'Breathing-Silence-Pattern': { label: 'Biological Pauses', icon: Activity, desc: 'Micro-silence & breath energy' },
    'Phase-Discontinuity-Detector': { label: 'STFT Phase Flux', icon: Waves, desc: 'Phase jump artifacts' },
    // Advanced video engines
    'Eye-Blink-EAR': { label: 'Eye Blink Analysis', icon: Eye, desc: 'EAR blink pattern & rate' },
    'Face-Mesh-Tracking': { label: 'Face Mesh Tracking', icon: Brain, desc: 'Landmark jitter & chunk warping' },
    'Eye-Reflection-Geometry': { label: 'Eye Reflection', icon: Zap, desc: 'Specular highlight symmetry' },
    'Lip-Sync-Correlation': { label: 'Lip-Sync AV Sync', icon: Waves, desc: 'Audio–visual cross-correlation' },
    'Semantic-Fact-Check': { label: 'Semantic Fact-Check', icon: Shield, desc: 'Vision AI + Google Fact Check' },
};

function ScoreBar({ score, color }) {
    return (
        <div className="flex items-center gap-3 mt-2">
            <div className="flex-1 h-1.5 bg-ds-silver/10 rounded-full overflow-hidden">
                <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{ width: `${Math.min(score, 100)}%`, backgroundColor: color }}
                />
            </div>
            <span className="text-xs font-mono text-ds-silver/60 w-8 text-right">{Math.round(score)}%</span>
        </div>
    );
}

function scoreColor(s) {
    if (s >= 70) return '#ff3c00'; // Red
    if (s >= 40) return '#ffaa00'; // Orange
    return '#00ffaa'; // Cyan-ish Green
}

export default function DetectionBreakdown({ findings = [], ltcaData = {} }) {
    // Build engine score map from findings
    const engineMap = {};
    findings.forEach(f => {
        if (f.engine && f.score != null) {
            engineMap[f.engine] = f;
        }
    });

    // Also pull scorecard from ltcaData for engines that don't emit findings
    const extraScores = [
        { engine: 'Eye-Blink-EAR', score: ltcaData.blink_score, detail: ltcaData.blink_detail },
        { engine: 'Face-Mesh-Tracking', score: ltcaData.mesh_score, detail: ltcaData.mesh_detail },
        { engine: 'Eye-Reflection-Geometry', score: ltcaData.reflect_score, detail: ltcaData.reflect_detail },
        { engine: 'Lip-Sync-Correlation', score: ltcaData.sync_score, detail: ltcaData.sync_detail },
    ].filter(e => e.score != null && !engineMap[e.engine]);

    extraScores.forEach(e => { engineMap[e.engine] = e; });

    const entries = Object.entries(engineMap).filter(([, v]) => v.score != null);
    if (entries.length === 0) return null;

    return (
        <BrutalCard className="border-t-4 border-t-ds-cyan">
            <h3 className="font-grotesk font-black text-ds-silver text-xl uppercase tracking-widest mb-6 flex items-center gap-2">
                <Scan className="w-5 h-5 text-ds-cyan" />
                Detection Engine Breakdown
                <span className="ml-auto text-[10px] font-mono text-ds-silver/30">QUANTUM FORENSICS ACTIVE</span>
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {entries.map(([engineKey, finding]) => {
                    const meta = ENGINE_META[engineKey] || { label: engineKey, icon: Activity, desc: 'Forensic analyzer' };
                    const Icon = meta.icon;
                    const s = finding.score ?? 0;
                    const color = scoreColor(s);
                    const textColor = s >= 70 ? 'text-ds-red' : s >= 40 ? 'text-ds-yellow' : 'text-ds-green';

                    return (
                        <div
                            key={engineKey}
                            className={`p-4 border-2 border-ds-silver/10 bg-ds-silver/5 rounded-sm hover:border-ds-silver/30 transition-all group`}
                        >
                            <div className="flex items-center gap-2 mb-1">
                                <Icon className={`w-4 h-4 flex-shrink-0 ${textColor} group-hover:scale-110 transition-transform`} />
                                <span className="font-grotesk font-black text-sm text-ds-silver uppercase tracking-tight">{meta.label}</span>
                                <span className={`ml-auto font-mono text-sm font-black ${textColor}`}>{Math.round(s)}%</span>
                            </div>
                            <p className="text-ds-silver/50 text-[10px] uppercase font-mono tracking-tighter">{meta.desc}</p>

                            {finding.reasoning && (
                                <div className="mt-3 p-2 bg-black/40 border-l-2 border-ds-silver/20 text-[11px] font-mono text-ds-silver/60 leading-relaxed italic">
                                    {finding.reasoning}
                                </div>
                            )}

                            <ScoreBar score={s} color={color} />

                            {finding.detail && !finding.reasoning && (
                                <p className="text-ds-silver/40 text-[10px] font-mono mt-2 leading-snug line-clamp-2 italic">
                                    {finding.detail}
                                </p>
                            )}
                        </div>
                    );
                })}
            </div>

            {/* Supplementary Telemetry */}
            {(ltcaData.sync_correlation != null || ltcaData.vtl_mean != null) && (
                <div className="mt-6 p-4 border-2 border-ds-silver/10 bg-black/20 grid grid-cols-2 sm:grid-cols-4 gap-4 text-[10px] font-mono">
                    {ltcaData.sync_correlation != null && (
                        <div className="space-y-1">
                            <p className="text-ds-silver/30 uppercase">AV Correlation</p>
                            <p className="text-ds-cyan font-bold">{ltcaData.sync_correlation?.toFixed(3)}</p>
                        </div>
                    )}
                    {ltcaData.vtl_mean != null && (
                        <div className="space-y-1">
                            <p className="text-ds-silver/30 uppercase">Avg Vocal Tract</p>
                            <p className="text-ds-cyan font-bold">{ltcaData.vtl_mean?.toFixed(1)} cm</p>
                        </div>
                    )}
                    {ltcaData.sync_offset != null && (
                        <div className="space-y-1">
                            <p className="text-ds-silver/30 uppercase">Temporal Drift</p>
                            <p className="text-ds-cyan font-bold">{ltcaData.sync_offset} frames</p>
                        </div>
                    )}
                    {ltcaData.blinks_detected != null && (
                        <div className="space-y-1">
                            <p className="text-ds-silver/30 uppercase">Stochastic Blinks</p>
                            <p className="text-ds-cyan font-bold">{ltcaData.blinks_detected}</p>
                        </div>
                    )}
                </div>
            )}
        </BrutalCard>
    );
}
