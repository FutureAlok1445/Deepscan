import React from 'react';

import BrutalCard from './ui/BrutalCard';
import BrutalButton from './ui/BrutalButton';

function getVerdictConfig(aacs_score) {
  const score = typeof aacs_score === 'number' ? aacs_score : 0;
  if (score < 35) {
    return {
      label: 'REAL',
      color: 'bg-emerald-500 text-black border-black shadow-[6px_6px_0_0_rgba(0,0,0,1)]',
      sentence: 'This picture looks real.',
    };
  }
  if (score <= 60) {
    return {
      label: 'SUSPICIOUS',
      color: 'bg-amber-400 text-black border-black shadow-[6px_6px_0_0_rgba(0,0,0,1)]',
      sentence: 'This picture might be edited or AI-generated.',
    };
  }
  return {
    label: 'FAKE',
    color: 'bg-red-500 text-black border-black shadow-[6px_6px_0_0_rgba(0,0,0,1)]',
    sentence: 'This picture is very likely fake.',
  };
}

export default function SimpleResult({ aacs_score, verdict, plain_reason, action, context }) {
  const cfg = getVerdictConfig(aacs_score);
  const contextCount = context?.match_count ?? 0;

  return (
    <div className="w-full flex items-center justify-center">
      <BrutalCard className="w-full max-w-3xl text-center bg-ds-bg border-2 border-ds-silver shadow-[6px_6px_0_0_rgba(0,0,0,1)] px-6 py-10 sm:px-10 sm:py-12">
        <div className="flex flex-col items-center gap-6">
          {/* Verdict badge */}
          <div
            className={[
              'inline-flex items-center justify-center rounded-sm px-6 py-3 border font-grotesk font-black tracking-widest uppercase',
              'text-[40px] sm:text-[56px] leading-none',
              cfg.color,
            ].join(' ')}
          >
            {cfg.label}
          </div>

          {/* Plain sentence */}
          <p className="max-w-xl font-mono text-[16px] sm:text-[18px] text-ds-silver">
            {typeof plain_reason === 'object' 
              ? (plain_reason?.summary || plain_reason?.text || JSON.stringify(plain_reason)) 
              : (plain_reason || cfg.sentence)}
          </p>

          {/* Context line */}
          <p className="font-mono text-[16px] sm:text-[18px] text-ds-silver/80">
            {contextCount > 0
              ? `Found on ${contextCount} website${contextCount === 1 ? '' : 's'} online`
              : 'Not found online'}
          </p>

          {/* Action button */}
          <div className="mt-4">
            <BrutalButton size="lg" onClick={action?.onClick}>
              {action?.label || 'What should I do next?'}
            </BrutalButton>
          </div>
        </div>
      </BrutalCard>
    </div>
  );
}

