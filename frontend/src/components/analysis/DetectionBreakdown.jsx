import React from 'react';
import { Eye, Activity, Waves, Brain, Scan, Zap, Radio, Shield } from 'lucide-react';
import BrutalCard from '../ui/BrutalCard';

const ENGINE_META = {
    // Classic engines — mapped by engine name from backend findings
    'Spatio-Temporal-Analysis': { label: 'Spatio-Temporal', icon: Scan, desc: 'ViT + Optical Flow' },
    'Latent-Trajectory-Curvature': { label: 'Physics (LTCA)', icon: Activity, desc: 'Latent space physics' },
    'rPPG-Heartbeat': { label: 'Heartbeat (rPPG)', icon: Radio, desc: 'Facial blood-flow pulse' },
    'Audio-Spoof-Detection': { label: 'Audio Clone', icon: Waves, desc: 'Voice synthesis detection' },
    // Advanced engines
    'Eye-Blink-EAR': { label: 'Eye Blink Analysis', icon: Eye, desc: 'EAR blink pattern & rate' },
    'Face-Mesh-Tracking': { label: 'Face Mesh Tracking', icon: Brain, desc: 'Landmark jitter & chunk warping' },
    'Eye-Reflection-Geometry': { label: 'Eye Reflection', icon: Zap, desc: 'Specular highlight symmetry' },
    'Lip-Sync-Correlation': { label: 'Lip-Sync AV Sync', icon: Waves, desc: 'Audio–visual cross-correlation' },
    'Semantic-Fact-Check': { label: 'Semantic Fact-Check', icon: Shield, desc: 'Vision AI + Google Fact Check' },
};

function ScoreBar({ score, color }) {
    return (
        <div className="flex items-center gap-3 mt-2">
            <div className="flex-1 h-2 bg-ds-silver/10 rounded-full overflow-hidden">
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
    if (s >= 70) return '#ff3c00';
    if (s >= 40) return '#ffd700';
    return '#39ff14';
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
        <BrutalCard>
            <h3 className="font-grotesk font-bold text-ds-silver text-lg uppercase tracking-wider mb-5 flex items-center gap-2">
                <Scan className="w-5 h-5 text-ds-cyan" />
                Detection Engine Breakdown
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {entries.map(([engineKey, finding]) => {
                    const meta = ENGINE_META[engineKey] || { label: engineKey, icon: Activity, desc: '' };
                    const Icon = meta.icon;
                    const s = finding.score ?? 0;
                    const color = scoreColor(s);
                    const textColor = s >= 70 ? 'text-ds-red' : s >= 40 ? 'text-ds-yellow' : 'text-ds-green';

                    return (
                        <div
                            key={engineKey}
                            className="p-4 border border-ds-silver/15 bg-ds-bg/60 rounded-sm hover:border-ds-silver/30 transition-colors"
                        >
                            <div className="flex items-center gap-2 mb-1">
                                <Icon className={`w-4 h-4 flex-shrink-0 ${textColor}`} />
                                <span className="font-grotesk font-bold text-sm text-ds-silver">{meta.label}</span>
                                <span className={`ml-auto font-mono text-sm font-bold ${textColor}`}>{Math.round(s)}%</span>
                            </div>
                            <p className="text-ds-silver/40 text-xs font-mono">{meta.desc}</p>
                            {finding.detail && (
                                <p className="text-ds-silver/60 text-xs font-mono mt-1 leading-snug line-clamp-2">{finding.detail}</p>
                            )}
                            <ScoreBar score={s} color={color} />
                        </div>
                    );
                })}
            </div>

            {/* Lip-Sync detail stats */}
            {ltcaData.sync_correlation != null && (
                <div className="mt-4 p-3 border border-ds-silver/10 bg-ds-bg/40 flex flex-wrap gap-4 text-xs font-mono">
                    <span className="text-ds-silver/50">AV Correlation: <span className="text-ds-cyan">{ltcaData.sync_correlation?.toFixed(2)}</span></span>
                    {ltcaData.sync_offset != null && (
                        <span className="text-ds-silver/50">Frame Offset: <span className="text-ds-cyan">{ltcaData.sync_offset} frames</span></span>
                    )}
                    {ltcaData.blinks_detected != null && (
                        <span className="text-ds-silver/50">Blinks Detected: <span className="text-ds-cyan">{ltcaData.blinks_detected}</span></span>
                    )}
                </div>
            )}
        </BrutalCard>
    );
}
