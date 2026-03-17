import React from 'react';
import { FileSearch, Clock, ChevronRight, AlertTriangle, ShieldCheck, Fingerprint, Eye } from 'lucide-react';

export default function VideoDescription({ videoDescription }) {
    if (!videoDescription) return null;

    const {
        description = '',
        setting = '',
        people = '',
        activity = '',
        moments = [],
        context = '',
        artifacts = [],
        verdict = 'UNKNOWN',
        verdict_detail = ''
    } = videoDescription;

    const hasSections = setting || people || activity || context || artifacts.length > 0;

    const getVerdictColor = (v) => {
        switch (v?.toUpperCase()) {
            case 'CLEAN': return 'text-green-500 border-green-500/30 bg-green-500/10';
            case 'SUSPICIOUS': return 'text-yellow-500 border-yellow-500/30 bg-yellow-500/10';
            case 'LIKELY_AI': return 'text-orange-500 border-orange-500/30 bg-orange-500/10';
            case 'DEFINITE_AI': return 'text-red-500 border-red-500/30 bg-red-500/10';
            default: return 'text-ds-silver/40 border-ds-silver/20 bg-ds-silver/5';
        }
    };

    return (
        <div className="w-full bg-[#0a0a0a] border-t-2 border-ds-cyan border-x border-b border-ds-silver/10 shadow-2xl relative overflow-hidden font-mono">
            {/* Ambient Background Glow */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-ds-cyan/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/3 pointer-events-none" />

            {/* Header */}
            <div className="px-6 py-4 flex items-center justify-between border-b border-ds-silver/10 bg-white/[0.02]">
                <div className="flex items-center gap-3">
                    <div className="p-1.5 bg-ds-cyan/10 rounded-sm">
                        <FileSearch className="w-4 h-4 text-ds-cyan" />
                    </div>
                    <div>
                        <h3 className="font-grotesk font-bold text-ds-silver text-sm uppercase tracking-[0.2em]">
                            Forensic Multi-Pass Analysis
                        </h3>
                        <p className="text-[10px] text-ds-silver/40">VLM Intelligence · Qwen3.5-9B VL</p>
                    </div>
                </div>
                
                {verdict && (
                    <div className={`flex items-center gap-2 px-3 py-1 border rounded-full ${getVerdictColor(verdict)}`}>
                        <ShieldCheck className="w-3 h-3" />
                        <span className="text-[10px] uppercase tracking-widest font-bold">{verdict}</span>
                    </div>
                )}
            </div>

            {/* Body */}
            <div className="p-6">
                {hasSections ? (
                    <div className="space-y-0 text-sm">
                        <DataRow label="Scene Setting" value={setting} delay="0" icon={<Eye className="w-3.5 h-3.5" />} />
                        <DataRow label="Target Subjects" value={people} delay="100" icon={<Fingerprint className="w-3.5 h-3.5" />} />
                        <DataRow label="Detected Activity" value={activity} delay="200" icon={<Clock className="w-3.5 h-3.5" />} />
                        
                        {/* Visual Artifacts Section */}
                        {artifacts.length > 0 && (
                            <div className="flex flex-col sm:flex-row py-4 border-b border-ds-silver/5 animate-fade-in" style={{ animationDelay: '300ms', animationFillMode: 'both' }}>
                                <div className="sm:w-1/4 pb-2 sm:pb-0 sm:pr-4 flex items-start gap-2 text-ds-silver/50 font-bold uppercase tracking-wider text-xs pt-1">
                                    <AlertTriangle className="w-3.5 h-3.5 text-yellow-500/70" />
                                    <span>Visual Artifacts</span>
                                </div>
                                <div className="sm:w-3/4 flex flex-wrap gap-2">
                                    {artifacts.map((art, i) => (
                                        <div key={i} className="px-2 py-1 bg-white/[0.03] border border-ds-silver/10 rounded text-[11px] text-ds-silver/80">
                                            {art}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        <DataRow label="Forensic Context" value={context} delay="400" icon={<FileSearch className="w-3.5 h-3.5" />} />

                        {/* Verdict Detail */}
                        {verdict_detail && (
                            <div className="mt-4 p-4 bg-ds-cyan/5 border border-ds-cyan/20 rounded-lg animate-fade-in" style={{ animationDelay: '500ms', animationFillMode: 'both' }}>
                                <p className="text-[10px] uppercase text-ds-cyan font-bold mb-1 tracking-widest">Final Visual Verdict</p>
                                <p className="text-ds-silver/90 text-sm italic">"{verdict_detail}"</p>
                            </div>
                        )}

                        {/* Moments Timeline */}
                        {moments.length > 0 && (
                            <div className="flex flex-col sm:flex-row py-4 border-b border-ds-silver/5 animate-fade-in" style={{ animationDelay: '600ms', animationFillMode: 'both' }}>
                                <div className="sm:w-1/4 pb-2 sm:pb-0 sm:pr-4 flex items-start gap-2 text-ds-silver/50 font-bold uppercase tracking-wider text-xs pt-1">
                                    <Clock className="w-3.5 h-3.5" />
                                    <span>Timeline Log</span>
                                </div>
                                <div className="sm:w-3/4 space-y-3 relative before:absolute before:inset-0 before:ml-[9px] before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-ds-silver/10 before:to-transparent">
                                    {moments.filter(m => m.trim().length > 4).map((moment, i) => (
                                        <div key={i} className="relative flex items-center gap-4">
                                            <div className="flex items-center justify-center w-5 h-5 rounded-full border border-ds-cyan bg-ds-bg text-ds-cyan text-[10px] font-bold z-10 shrink-0">
                                                {i + 1}
                                            </div>
                                            <div className="flex-1 p-3 rounded bg-white/[0.02] border border-ds-silver/5 text-ds-silver/80 text-xs shadow-sm">
                                                {moment.trim()}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="bg-black/40 border border-ds-silver/10 p-4 rounded text-ds-silver/70 text-sm leading-relaxed">
                        {description.split('\n').filter(l => l.trim()).map((line, i) => (
                            <div key={i} className="flex gap-3 mb-2 last:mb-0">
                                <ChevronRight className="w-4 h-4 text-ds-cyan shrink-0 mt-0.5" />
                                <p>{line.trim()}</p>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

function DataRow({ label, value, delay, icon }) {
    if (!value) return null;
    return (
        <div
            className="flex flex-col sm:flex-row py-4 border-b border-ds-silver/5 last:border-0 hover:bg-white/[0.02] transition-colors duration-300 animate-fade-in"
            style={{ animationDelay: `${delay}ms`, animationFillMode: 'both' }}
        >
            <div className="sm:w-1/4 pb-1 sm:pb-0 sm:pr-4 flex items-center gap-2 text-ds-silver/50 font-bold uppercase tracking-wider text-xs">
                {icon}
                <span>{label}</span>
            </div>
            <div className="sm:w-3/4 text-ds-silver/90 leading-relaxed text-sm">
                {value}
            </div>
        </div>
    );
}
