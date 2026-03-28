import React from 'react';
import { Globe, ShieldCheck, Image as ImageIcon, Zap } from 'lucide-react';
import BrutalCard from '../ui/BrutalCard';

export default function ContextVerification({ data }) {
  const isLoaded = data && data.success;
  const hasImages = isLoaded && data.matching_images && data.matching_images.length > 0;
  const isSimulated = data?.is_simulated;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <div className={`w-1 h-5 ${isLoaded ? 'bg-ds-cyan' : 'bg-ds-silver/30'}`} />
        <h3 className="font-grotesk font-bold text-ds-silver text-sm uppercase tracking-wider">
          Layer 11: Live Context Verification
        </h3>
        <span className={`text-[9px] font-mono px-2 py-0.5 rounded border ${
          isLoaded
            ? 'text-ds-cyan bg-ds-cyan/10 border-ds-cyan/30'
            : 'text-ds-red animate-pulse bg-ds-red/10 border-ds-red/20'
        }`}>
          {isLoaded ? (isSimulated ? 'DEMO_DATA' : 'LIVE_API') : 'SYNCING'}
        </span>
        {isLoaded && (
          <span className="text-[9px] font-mono text-ds-silver/30">
            Google Vision / Reverse Image Search
          </span>
        )}
      </div>

      <BrutalCard className={`bg-ds-bg/40 border-ds-cyan/20 !p-4 ${!isLoaded ? 'opacity-40' : ''}`}>
        {!isLoaded ? (
          <div className="py-6 text-center space-y-2">
            <Globe className="w-8 h-8 text-ds-silver/20 mx-auto animate-pulse" />
            <p className="text-xs font-mono text-ds-silver/40">
              Real-time data synchronization pending…
            </p>
          </div>
        ) : (
          <div className="space-y-5">
            {/* Entities Row */}
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-ds-cyan" />
                <span className="font-mono text-[10px] text-ds-cyan uppercase font-bold tracking-wider">
                  Identified Visual Entities
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {data.entities && data.entities.length > 0 ? (
                  data.entities.map((entity, i) => (
                    <span
                      key={i}
                      className="px-2 py-1 bg-ds-cyan/10 border border-ds-cyan/30 text-ds-cyan text-[10px] font-mono rounded"
                    >
                      {entity}
                    </span>
                  ))
                ) : (
                  <span className="text-xs font-mono text-ds-silver/40 italic">No entities extracted</span>
                )}
              </div>
            </div>

            {/* Matching Images Grid */}
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <ImageIcon className="w-4 h-4 text-ds-silver/60" />
                <span className="font-mono text-[10px] text-ds-silver/60 uppercase font-bold tracking-wider">
                  Matching Images Found on Web
                </span>
              </div>
              {hasImages ? (
                <div className="grid grid-cols-3 gap-2">
                  {data.matching_images.map((imgUrl, i) => (
                    <div
                      key={i}
                      className="relative group aspect-square bg-ds-bg border border-ds-silver/10 overflow-hidden rounded"
                    >
                      <img
                        src={imgUrl}
                        alt={`Match ${i + 1}`}
                        className="w-full h-full object-contain p-1 transition-transform duration-200 group-hover:scale-105"
                        onError={(e) => { e.target.style.display = 'none'; e.target.parentNode.classList.add('hidden'); }}
                      />
                      <div className="absolute inset-0 bg-ds-cyan/0 group-hover:bg-ds-cyan/5 transition-colors pointer-events-none" />
                      <div className="absolute bottom-0 left-0 right-0 bg-black/60 text-[8px] font-mono text-ds-silver/60 px-1 py-0.5 opacity-0 group-hover:opacity-100 transition-opacity truncate">
                        Match #{i + 1}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex items-center gap-3 p-3 bg-ds-silver/5 border border-ds-silver/10 rounded">
                  <Zap className="w-4 h-4 text-yellow-500 shrink-0" />
                  <p className="text-[10px] font-mono text-ds-silver/50">
                    No public image matches indexed. Image may be original or private.
                  </p>
                </div>
              )}
            </div>

            <div className="pt-2 border-t border-ds-silver/10">
              <p className="text-[9px] font-mono text-ds-silver/25 leading-relaxed">
                SYSTEM: Real-time reverse image index scan via Google Vision/Lens API. 
                Matching images found on authentic domains indicate non-manipulated origin.
              </p>
            </div>
          </div>
        )}
      </BrutalCard>
    </div>
  );
}
