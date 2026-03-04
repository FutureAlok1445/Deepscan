import React from 'react';
import BrutalCard from '../ui/BrutalCard';
import { MessageSquare } from 'lucide-react';

export default function NarrativeExplanation({ narrative }) {
  if (!narrative) {
    return (
      <BrutalCard className="text-center py-8">
        <p className="text-ds-silver/50 font-mono text-sm">No explanation available</p>
      </BrutalCard>
    );
  }

  const { summary, detailed, eli5, technical_summary, technical } = typeof narrative === 'string'
    ? { summary: narrative, detailed: null, eli5: null, technical_summary: null, technical: null }
    : narrative;

  const techContent = technical_summary || technical;

  return (
    <BrutalCard className="space-y-4">
      <h3 className="font-grotesk font-bold text-ds-silver text-lg uppercase tracking-wider flex items-center gap-2">
        <MessageSquare className="w-5 h-5 text-ds-cyan" />
        AI Explanation
      </h3>

      {/* Summary */}
      {summary && (
        <div className="p-4 bg-ds-bg border-l-4 border-ds-cyan">
          <p className="text-ds-silver text-sm font-mono leading-relaxed">{summary}</p>
        </div>
      )}

      {/* ELI5 */}
      {eli5 && (
        <div className="space-y-1">
          <p className="text-xs font-mono text-ds-yellow uppercase tracking-wider">
            Simple Explanation
          </p>
          <p className="text-ds-silver/80 text-sm font-mono leading-relaxed">{eli5}</p>
        </div>
      )}

      {/* Detailed */}
      {detailed && (
        <details className="group">
          <summary className="cursor-pointer text-xs font-mono text-ds-cyan uppercase tracking-wider hover:text-ds-cyan/80 transition-colors">
            {'>'} Detailed Analysis
          </summary>
          <div className="mt-2 p-3 bg-ds-bg border border-ds-silver/20">
            <p className="text-ds-silver/70 text-sm font-mono leading-relaxed whitespace-pre-wrap">
              {detailed}
            </p>
          </div>
        </details>
      )}

      {/* Technical */}
      {techContent && (
        <details className="group">
          <summary className="cursor-pointer text-xs font-mono text-ds-yellow uppercase tracking-wider hover:text-ds-yellow/80 transition-colors">
            {'>'} Technical Summary
          </summary>
          <div className="mt-2 p-3 bg-ds-bg border border-ds-silver/20">
            <pre className="text-ds-silver/60 text-xs font-mono leading-relaxed overflow-x-auto">
              {typeof techContent === 'string'
                ? techContent
                : JSON.stringify(techContent, null, 2)}
            </pre>
          </div>
        </details>
      )}
    </BrutalCard>
  );
}
