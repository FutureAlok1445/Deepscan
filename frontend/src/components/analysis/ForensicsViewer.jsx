import React, { useState } from 'react';
import BrutalCard from '../ui/BrutalCard';
import BrutalBadge from '../ui/BrutalBadge';

const TABS = ['ELA', 'FFT', 'Noise', 'Metadata'];

export default function ForensicsViewer({ forensics }) {
  const [activeTab, setActiveTab] = useState(0);

  if (!forensics) {
    return (
      <BrutalCard className="text-center py-8">
        <p className="text-ds-silver/50 font-mono text-sm">No forensics data available</p>
      </BrutalCard>
    );
  }

  const tabData = [
    forensics.ela,
    forensics.fft,
    forensics.noise,
    forensics.metadata,
  ];

  const current = tabData[activeTab];

  return (
    <BrutalCard className="space-y-4">
      <h3 className="font-grotesk font-bold text-ds-silver text-lg uppercase tracking-wider flex items-center gap-2">
        <span className="w-3 h-3 bg-ds-yellow inline-block" />
        Forensic Analysis
      </h3>

      {/* Tab bar */}
      <div className="flex border-b-3 border-ds-silver/20">
        {TABS.map((tab, i) => (
          <button
            key={tab}
            onClick={() => setActiveTab(i)}
            className={`px-4 py-2 text-xs font-mono uppercase tracking-wider transition-colors ${
              activeTab === i
                ? 'text-ds-yellow border-b-2 border-ds-yellow bg-ds-yellow/5'
                : 'text-ds-silver/50 hover:text-ds-silver'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="min-h-[200px]">
        {current ? (
          <div className="space-y-3">
            {current.image_url && (
              <div className="border-3 border-ds-silver/30 overflow-hidden">
                <img
                  src={current.image_url}
                  alt={`${TABS[activeTab]} analysis`}
                  className="w-full h-48 object-cover"
                />
              </div>
            )}

            {current.score != null && (
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono text-ds-silver/50 uppercase">Score:</span>
                <BrutalBadge variant={current.score > 70 ? 'red' : current.score > 40 ? 'yellow' : 'green'}>
                  {current.score}%
                </BrutalBadge>
              </div>
            )}

            {current.description && (
              <p className="text-ds-silver/70 text-sm font-mono leading-relaxed">
                {current.description}
              </p>
            )}

            {current.details && typeof current.details === 'object' && (
              <div className="bg-ds-bg border border-ds-silver/20 p-3 space-y-1">
                {Object.entries(current.details).map(([key, val]) => (
                  <div key={key} className="flex justify-between text-xs font-mono">
                    <span className="text-ds-silver/50">{key}:</span>
                    <span className="text-ds-silver">{String(val)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center justify-center h-48">
            <p className="text-ds-silver/30 font-mono text-sm">
              {TABS[activeTab]} data not available
            </p>
          </div>
        )}
      </div>
    </BrutalCard>
  );
}
