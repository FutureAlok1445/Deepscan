import React from 'react';
import { ShieldAlert, Info, Microscope, Target, Flag, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function SemanticIntelligence({ data }) {
    if (!data) return null;

    const {
        description = '',
        subjects = '',
        claims = [],
        manipulation_indicators = [],
        narrative_intent = '',
        risk_level = 'UNKNOWN',
        risk_justification = ''
    } = data;

    const getRiskColor = (level) => {
        switch (level?.toUpperCase()) {
            case 'LOW': return 'text-green-500 bg-green-500/10 border-green-500/20';
            case 'MEDIUM': return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20';
            case 'HIGH': return 'text-orange-500 bg-orange-500/10 border-orange-500/20';
            case 'CRITICAL': return 'text-red-500 bg-red-500/10 border-red-500/20';
            default: return 'text-ds-silver/40 bg-ds-silver/5 border-ds-silver/10';
        }
    };

    const getPlausibilityColor = (p) => {
        switch (p?.toUpperCase()) {
            case 'PLAUSIBLE': return 'text-green-400';
            case 'QUESTIONABLE': return 'text-yellow-400';
            case 'SUSPICIOUS': return 'text-orange-400';
            case 'IMPLAUSIBLE': return 'text-red-400';
            default: return 'text-ds-silver/40';
        }
    };

    return (
        <div className="w-full bg-[#0a0a0a] border border-ds-silver/10 rounded-lg shadow-xl overflow-hidden font-mono mt-6">
            {/* Header */}
            <div className="px-6 py-4 bg-white/[0.02] border-b border-ds-silver/10 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <ShieldAlert className="w-5 h-5 text-ds-cyan" />
                    <div>
                        <h3 className="font-grotesk font-bold text-ds-silver text-sm uppercase tracking-widest">
                            OSINT & Media Intelligence
                        </h3>
                        <p className="text-[10px] text-ds-silver/40 tracking-wider">Deep Semantic Fact-Checking Engine</p>
                    </div>
                </div>
                <div className={`px-3 py-1 rounded border text-[10px] font-bold tracking-tighter uppercase ${getRiskColor(risk_level)}`}>
                    RISK: {risk_level}
                </div>
            </div>

            <div className="p-6 space-y-6">
                {/* Top Grid: Description & Intent */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                        <label className="text-[10px] uppercase font-bold text-ds-silver/30 tracking-widest flex items-center gap-2">
                            <Info className="w-3 h-3" /> Scene Description
                        </label>
                        <p className="text-ds-silver/80 text-sm leading-relaxed">{description}</p>
                    </div>
                    <div className="space-y-2">
                        <label className="text-[10px] uppercase font-bold text-ds-silver/30 tracking-widest flex items-center gap-2">
                            <Target className="w-3 h-3" /> Narrative Intent
                        </label>
                        <p className="text-ds-silver/80 text-sm leading-relaxed">{narrative_intent}</p>
                    </div>
                </div>

                {/* Subjects */}
                <div className="space-y-2 pt-4 border-t border-ds-silver/5">
                    <label className="text-[10px] uppercase font-bold text-ds-silver/30 tracking-widest flex items-center gap-2">
                        <Microscope className="w-3 h-3" /> Identified Subjects
                    </label>
                    <p className="text-ds-silver/80 text-sm">{subjects}</p>
                </div>

                {/* Factual Claims */}
                {claims.length > 0 && (
                    <div className="space-y-3 pt-4 border-t border-ds-silver/5">
                        <label className="text-[10px] uppercase font-bold text-ds-silver/30 tracking-widest flex items-center gap-2">
                            <Flag className="w-3 h-3" /> Extracted Factual Claims
                        </label>
                        <div className="grid grid-cols-1 gap-2">
                            {claims.map((claim, i) => (
                                <div key={i} className="flex items-start gap-3 p-3 bg-white/[0.01] border border-ds-silver/5 rounded-md group hover:bg-white/[0.03] transition-colors">
                                    <div className={`mt-1 h-3 w-1 rounded-full ${getPlausibilityColor(claim.plausibility).replace('text', 'bg').replace('/40', '/20')}`} title={claim.plausibility} />
                                    <div className="flex-1">
                                        <div className="flex items-center justify-between mb-1">
                                            <span className="text-[9px] font-bold text-ds-cyan/70 uppercase tracking-tighter bg-ds-cyan/5 px-1.5 rounded">{claim.category}</span>
                                            <span className={`text-[9px] font-bold uppercase tracking-tighter ${getPlausibilityColor(claim.plausibility)}`}>{claim.plausibility}</span>
                                        </div>
                                        <p className="text-ds-silver/90 text-[13px] leading-tight group-hover:text-ds-silver transition-colors">"{claim.text}"</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Manipulation Indicators */}
                {manipulation_indicators.length > 0 && (
                    <div className="space-y-3 pt-4 border-t border-ds-silver/5">
                        <label className="text-[10px] uppercase font-bold text-ds-silver/30 tracking-widest flex items-center gap-2">
                            <AlertCircle className="w-3 h-3" /> Forensic Anomalies
                        </label>
                        <ul className="space-y-2">
                            {manipulation_indicators.map((indicator, i) => (
                                <li key={i} className="flex items-center gap-2 text-xs text-ds-silver/70">
                                    <div className="w-1.5 h-1.5 rounded-full bg-ds-cyan/30" />
                                    {indicator}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                {/* Risk Justification */}
                {risk_justification && (
                    <div className="mt-6 p-4 bg-ds-bg border-l-2 border-ds-cyan/30 rounded-r-lg">
                        <div className="flex items-center gap-2 mb-2">
                            <CheckCircle2 className={`w-4 h-4 ${getRiskColor(risk_level).split(' ')[0]}`} />
                            <span className="text-xs font-bold text-ds-silver/50 tracking-widest uppercase">Intelligence Verdict</span>
                        </div>
                        <p className="text-ds-silver/80 text-sm italic italic">
                            {risk_justification}
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}
