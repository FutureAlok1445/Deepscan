import React from 'react';
import { FileSearch, Clock, ChevronRight } from 'lucide-react';

export default function VideoDescription({ videoDescription }) {
    if (!videoDescription) return null;

    const { description, setting, people, activity, moments = [], context } = videoDescription;
    const hasSections = setting || people || activity || context;

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
                            Semantic Scene Analysis
                        </h3>
                        <p className="text-[10px] text-ds-silver/40">Visual Context Engine / Llama-3.3-70b</p>
                    </div>
                </div>
                <div className="hidden sm:flex items-center gap-2 px-3 py-1 bg-ds-cyan/10 border border-ds-cyan/20 rounded-full">
                    <span className="w-1.5 h-1.5 rounded-full bg-ds-cyan animate-pulse" />
                    <span className="text-[10px] text-ds-cyan uppercase tracking-wider font-bold">Processed</span>
                </div>
            </div>

            {/* Body */}
            <div className="p-6">
                {hasSections ? (
                    <div className="space-y-0 text-sm">
                        <DataRow label="Setting" value={setting} delay="0" />
                        <DataRow label="Subjects" value={people} delay="100" />
                        <DataRow label="Activity" value={activity} delay="200" />
                        <DataRow label="Narrative" value={context} delay="300" />

                        {/* Moments Timeline */}
                        {moments.length > 0 && (
                            <div className="flex flex-col sm:flex-row py-4 border-b border-ds-silver/5 animate-fade-in" style={{ animationDelay: '400ms', animationFillMode: 'both' }}>
                                <div className="sm:w-1/4 pb-2 sm:pb-0 sm:pr-4 flex items-start gap-2 text-ds-silver/50 font-bold uppercase tracking-wider text-xs pt-1">
                                    <Clock className="w-3.5 h-3.5" />
                                    <span>Timeline</span>
                                </div>
                                <div className="sm:w-3/4 space-y-3 relative before:absolute before:inset-0 before:ml-[9px] before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-ds-silver/10 before:to-transparent">
                                    {moments.filter(m => m.trim().length > 4).map((moment, i) => (
                                        <div key={i} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                                            <div className="flex items-center justify-center w-5 h-5 rounded-full border border-ds-cyan bg-ds-bg text-ds-cyan text-[10px] font-bold z-10 shrink-0">
                                                {i + 1}
                                            </div>
                                            <div className="w-[calc(100%-2.5rem)] md:w-[calc(50%-2.5rem)] p-3 rounded bg-white/[0.02] border border-ds-silver/5 text-ds-silver/80 text-xs shadow">
                                                {moment.trim()}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                ) : (
                    /* Fallback plain text layout */
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

function DataRow({ label, value, delay }) {
    if (!value) return null;
    return (
        <div
            className="flex flex-col sm:flex-row py-4 border-b border-ds-silver/5 last:border-0 hover:bg-white/[0.02] transition-colors duration-300 animate-fade-in"
            style={{ animationDelay: `${delay}ms`, animationFillMode: 'both' }}
        >
            <div className="sm:w-1/4 pb-1 sm:pb-0 sm:pr-4 flex items-center text-ds-silver/50 font-bold uppercase tracking-wider text-xs">
                {label}
            </div>
            <div className="sm:w-3/4 text-ds-silver/90 leading-relaxed text-sm">
                {value}
            </div>
        </div>
    );
}
