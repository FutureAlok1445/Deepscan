import React from 'react';
import BrutalCard from '../ui/BrutalCard';

export default function CdcfPanel({ cdcf }) {
  if (!cdcf) {
    return (
      <BrutalCard className="text-center py-8">
        <p className="text-ds-silver/50 font-mono text-sm">No CDCF data available</p>
      </BrutalCard>
    );
  }

  // Normalize: backend returns `fusion` shape, mock returns `cdcf` shape
  const consensus = cdcf.consensus ?? (cdcf.multiplier ? Math.round(cdcf.multiplier * 100) : 0);
  const dissent = cdcf.dissent ?? (cdcf.contradictions?.length ? Math.min(cdcf.contradictions.length * 15, 100) : 0);
  const confidence = cdcf.confidence ?? 0;
  const fusion_method = cdcf.fusion_method || cdcf.method || 'XGBoost';
  const contradictions = cdcf.contradictions || [];

  return (
    <BrutalCard className="space-y-4">
      <h3 className="font-grotesk font-bold text-ds-silver text-lg uppercase tracking-wider flex items-center gap-2">
        <span className="w-3 h-3 bg-ds-cyan inline-block" />
        CDCF Engine
      </h3>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatBox label="Consensus" value={`${consensus ?? 0}%`} color="text-ds-green" />
        <StatBox label="Dissent" value={`${dissent ?? 0}%`} color="text-ds-red" />
        <StatBox label="Confidence" value={`${confidence ?? 0}%`} color="text-ds-cyan" />
        <StatBox label="Method" value={fusion_method || 'XGBoost'} color="text-ds-yellow" small />
      </div>

      {/* Consensus vs Dissent bar */}
      <div className="space-y-1">
        <div className="flex justify-between text-xs font-mono text-ds-silver/60">
          <span>Consensus</span>
          <span>Dissent</span>
        </div>
        <div className="h-4 border-3 border-ds-silver flex overflow-hidden">
          <div
            className="bg-ds-green/80 transition-all duration-700"
            style={{ width: `${consensus ?? 50}%` }}
          />
          <div
            className="bg-ds-red/80 transition-all duration-700"
            style={{ width: `${dissent ?? 50}%` }}
          />
        </div>
      </div>

      {cdcf.module_votes && (
        <div className="space-y-2">
          <p className="text-xs font-mono text-ds-silver/50 uppercase tracking-wider">
            Module Votes
          </p>
          <div className="grid grid-cols-2 gap-2">
            {cdcf.module_votes.map((vote, i) => (
              <div
                key={i}
                className="flex items-center justify-between p-2 bg-ds-bg border border-ds-silver/20"
              >
                <span className="text-xs font-mono text-ds-silver/70 truncate">
                  {vote.module}
                </span>
                <span
                  className={`text-xs font-mono font-bold ${
                    vote.verdict === 'fake' ? 'text-ds-red' : 'text-ds-green'
                  }`}
                >
                  {vote.verdict?.toUpperCase()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {contradictions.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-mono text-ds-yellow/80 uppercase tracking-wider">
            Contradictions
          </p>
          {contradictions.map((c, i) => (
            <p key={i} className="text-xs font-mono text-ds-silver/60 pl-2 border-l-2 border-ds-yellow/40">
              {typeof c === 'string' ? c : JSON.stringify(c)}
            </p>
          ))}
        </div>
      )}
    </BrutalCard>
  );
}

function StatBox({ label, value, color = 'text-ds-silver', small = false }) {
  return (
    <div className="p-3 bg-ds-bg border border-ds-silver/20 text-center">
      <p className="text-xs font-mono text-ds-silver/50 uppercase tracking-wider mb-1">{label}</p>
      <p className={`${small ? 'text-sm' : 'text-xl'} font-grotesk font-bold ${color}`}>{value}</p>
    </div>
  );
}
