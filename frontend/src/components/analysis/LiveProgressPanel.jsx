import React from 'react';
import BrutalCard from '../ui/BrutalCard';
import { Loader } from 'lucide-react';
import { ANALYSIS_STEPS } from '../../utils/constants';

export default function LiveProgressPanel({ progress = 0, currentStep = 0, messages = [] }) {
  // currentStep can be a string (step name) or number (index)
  const stepIndex = typeof currentStep === 'number'
    ? currentStep
    : ANALYSIS_STEPS.findIndex(s => s.toLowerCase().includes(String(currentStep).toLowerCase()));
  const resolvedStep = stepIndex >= 0 ? stepIndex : Math.floor((progress / 100) * ANALYSIS_STEPS.length);

  return (
    <BrutalCard className="space-y-6">
      <div className="flex items-center gap-3">
        <Loader className="w-6 h-6 text-ds-red animate-spin" />
        <h3 className="font-grotesk font-bold text-ds-silver text-lg uppercase tracking-wider">
          Analysis in Progress
        </h3>
      </div>

      {/* Progress bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-xs font-mono text-ds-silver/80 font-bold">
          <span>Progress</span>
          <span>{Math.round(progress)}%</span>
        </div>
        <div className="h-4 border-3 border-ds-silver overflow-hidden">
          <div
            className="h-full bg-ds-red transition-all duration-500 animate-progress-grow"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-2">
        {ANALYSIS_STEPS.map((step, i) => {
          const isDone = i < resolvedStep;
          const isCurrent = i === resolvedStep;
          return (
            <div
              key={i}
              className={`flex items-center gap-3 px-3 py-2 transition-all duration-300 ${isCurrent ? 'bg-ds-red/10 border-l-4 border-ds-red' : ''
                }`}
            >
              <span className="w-6 h-6 flex items-center justify-center text-xs font-mono shrink-0">
                {isDone ? (
                  <span className="text-ds-green">&#10003;</span>
                ) : isCurrent ? (
                  <span className="w-3 h-3 bg-ds-red rounded-full animate-pulse" />
                ) : (
                  <span className="text-ds-silver/50 font-bold">{i + 1}</span>
                )}
              </span>
              <span
                className={`text-sm font-mono ${isDone
                    ? 'text-ds-green/90 line-through'
                    : isCurrent
                      ? 'text-ds-red font-bold'
                      : 'text-ds-silver/50 font-bold'
                  }`}
              >
                {step}
              </span>
            </div>
          );
        })}
      </div>

      {/* Live log */}
      {messages.length > 0 && (
        <div className="bg-ds-bg/80 border border-ds-silver/20 p-3 max-h-32 overflow-y-auto">
          <p className="text-xs font-mono text-ds-silver/70 uppercase tracking-wider mb-2 font-bold">
            Live Log
          </p>
          {messages.slice(-8).map((msg, i) => (
            <p key={i} className="text-xs font-mono text-ds-silver/80 leading-relaxed">
              <span className="text-ds-cyan font-bold">$</span> {msg.message || JSON.stringify(msg)}
            </p>
          ))}
        </div>
      )}
    </BrutalCard>
  );
}
