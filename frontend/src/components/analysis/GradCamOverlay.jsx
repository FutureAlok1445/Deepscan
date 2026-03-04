import React, { useState } from 'react';
import BrutalCard from '../ui/BrutalCard';
import { Eye, Layers } from 'lucide-react';

export default function GradCamOverlay({ gradcam }) {
  const [showOverlay, setShowOverlay] = useState(true);
  const [opacity, setOpacity] = useState(60);

  if (!gradcam) {
    return (
      <BrutalCard className="text-center py-8">
        <p className="text-ds-silver/50 font-mono text-sm">No Grad-CAM data available</p>
      </BrutalCard>
    );
  }

  const { original_url, heatmap_url, regions = [] } = gradcam;

  return (
    <BrutalCard className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-grotesk font-bold text-ds-silver text-lg uppercase tracking-wider flex items-center gap-2">
          <Eye className="w-5 h-5 text-ds-green" />
          Grad-CAM
        </h3>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowOverlay(!showOverlay)}
            className={`flex items-center gap-1 text-xs font-mono px-2 py-1 border transition-colors ${
              showOverlay
                ? 'text-ds-green border-ds-green bg-ds-green/10'
                : 'text-ds-silver/50 border-ds-silver/30'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            Overlay
          </button>
        </div>
      </div>

      {/* Image container */}
      <div className="relative border-3 border-ds-silver/30 overflow-hidden bg-ds-bg">
        {original_url && (
          <img
            src={original_url}
            alt="Original"
            className="w-full h-64 object-cover"
          />
        )}
        {showOverlay && heatmap_url && (
          <img
            src={heatmap_url}
            alt="Grad-CAM heatmap"
            className="absolute inset-0 w-full h-64 object-cover transition-opacity duration-300"
            style={{ opacity: opacity / 100 }}
          />
        )}

        {/* Manipulation regions */}
        {showOverlay && regions.map((region, i) => (
          <div
            key={i}
            className="absolute border-2 border-ds-red/80 bg-ds-red/10"
            style={{
              left: `${region.x}%`,
              top: `${region.y}%`,
              width: `${region.w ?? region.width}%`,
              height: `${region.h ?? region.height}%`,
            }}
          >
            <span className="absolute -top-5 left-0 text-[10px] font-mono bg-ds-red text-white px-1">
              {region.label || `R${i + 1}`}
            </span>
          </div>
        ))}
      </div>

      {/* Opacity slider */}
      {showOverlay && (
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-ds-silver/50">Opacity</span>
          <input
            type="range"
            min={0}
            max={100}
            value={opacity}
            onChange={(e) => setOpacity(Number(e.target.value))}
            className="flex-1 accent-ds-red"
          />
          <span className="text-xs font-mono text-ds-silver/50 w-10 text-right">{opacity}%</span>
        </div>
      )}
    </BrutalCard>
  );
}
