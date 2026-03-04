import React from 'react';
import { AlertTriangle, CheckCircle, Info } from 'lucide-react';
import BrutalCard from '../ui/BrutalCard';

const SEVERITY_CONFIG = {
  critical: { icon: AlertTriangle, color: 'text-ds-red', border: 'border-l-ds-red', bg: 'bg-ds-red/5' },
  high: { icon: AlertTriangle, color: 'text-ds-red', border: 'border-l-ds-red', bg: 'bg-ds-red/5' },
  warning: { icon: AlertTriangle, color: 'text-ds-yellow', border: 'border-l-ds-yellow', bg: 'bg-ds-yellow/5' },
  medium: { icon: AlertTriangle, color: 'text-ds-yellow', border: 'border-l-ds-yellow', bg: 'bg-ds-yellow/5' },
  info: { icon: Info, color: 'text-ds-cyan', border: 'border-l-ds-cyan', bg: 'bg-ds-cyan/5' },
  low: { icon: Info, color: 'text-ds-cyan', border: 'border-l-ds-cyan', bg: 'bg-ds-cyan/5' },
  ok: { icon: CheckCircle, color: 'text-ds-green', border: 'border-l-ds-green', bg: 'bg-ds-green/5' },
  normal: { icon: CheckCircle, color: 'text-ds-green', border: 'border-l-ds-green', bg: 'bg-ds-green/5' },
};

/** Map a numeric score to a severity level for backend findings that only have score */
function inferSeverity(finding) {
  if (finding.severity) return finding.severity;
  const score = finding.score ?? 50;
  if (score >= 70) return 'high';
  if (score >= 40) return 'medium';
  if (score >= 20) return 'low';
  return 'normal';
}

export default function KeyFindings({ findings = [] }) {
  if (!findings.length) {
    return (
      <BrutalCard className="text-center py-8">
        <p className="text-ds-silver/50 font-mono text-sm">No findings available</p>
      </BrutalCard>
    );
  }

  return (
    <div className="space-y-3">
      <h3 className="font-grotesk font-bold text-ds-silver text-lg uppercase tracking-wider">
        Key Findings
      </h3>
      {findings.map((finding, i) => {
        const sev = SEVERITY_CONFIG[inferSeverity(finding)] || SEVERITY_CONFIG.info;
        const Icon = sev.icon;
        return (
          <div
            key={i}
            className={`flex items-start gap-3 p-4 border-3 border-ds-silver border-l-[6px] ${sev.border} ${sev.bg}`}
          >
            <Icon className={`w-5 h-5 mt-0.5 flex-shrink-0 ${sev.color}`} />
            <div className="flex-1 min-w-0">
              <p className={`font-grotesk font-bold text-sm ${sev.color}`}>
                {finding.title || finding.module}
              </p>
              <p className="text-ds-silver/70 text-sm font-mono mt-1 leading-relaxed">
                {finding.detail || finding.description}
              </p>
              {finding.confidence != null && (
                <div className="mt-2 flex items-center gap-2">
                  <div className="flex-1 h-1.5 bg-ds-silver/10 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${finding.confidence}%`,
                        backgroundColor: sev.color === 'text-ds-red' ? '#ff3c00' : sev.color === 'text-ds-yellow' ? '#ffd700' : '#39ff14',
                      }}
                    />
                  </div>
                  <span className="text-xs font-mono text-ds-silver/50">
                    {finding.confidence}%
                  </span>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
