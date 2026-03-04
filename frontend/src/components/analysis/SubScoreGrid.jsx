import React from 'react';
import BrutalCard from '../ui/BrutalCard';
import { SUB_SCORES } from '../../utils/constants';
import { getScoreHex } from '../../utils/formatters';
import {
  ScanFace, AudioLines, Film, Mic, Fingerprint, HeartPulse, FileCode, Globe,
} from 'lucide-react';

const ICON_MAP = {
  ScanFace, AudioLines, Film, Mic, Fingerprint, HeartPulse, FileCode, Globe,
};

export default function SubScoreGrid({ subScores = {} }) {
  return (
    <div className="space-y-3">
      <h3 className="font-grotesk font-bold text-ds-silver text-lg uppercase tracking-wider">
        Sub-Scores
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {SUB_SCORES.map(({ key, label, icon }) => {
          const value = subScores[key];
          const Icon = ICON_MAP[icon] || Globe;
          const hex = getScoreHex(value);

          return (
            <BrutalCard key={key} hover={false} className="!p-4 text-center space-y-2">
              <Icon className="w-6 h-6 mx-auto" style={{ color: hex }} />
              <p className="text-xs font-mono text-ds-silver/80 uppercase tracking-wider font-bold">
                {label}
              </p>
              <p className="text-2xl font-grotesk font-black drop-shadow-md" style={{ color: hex }}>
                {value != null ? `${value}%` : '—'}
              </p>
              {/* Mini bar */}
              <div className="h-1.5 bg-ds-silver/20 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{ width: `${value ?? 0}%`, backgroundColor: hex }}
                />
              </div>
            </BrutalCard>
          );
        })}
      </div>
    </div>
  );
}
