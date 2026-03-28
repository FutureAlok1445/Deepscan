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
    <div className="space-y-2">
      <div className="flex items-center gap-2 mb-2">
        <div className="w-1 h-4 bg-ds-red" />
        <h3 className="font-grotesk font-bold text-ds-silver text-sm uppercase tracking-wider">
          Forensic Sub-Scores
        </h3>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-4 gap-2">
        {SUB_SCORES.map(({ key, label, icon }) => {
          const value = subScores[key];
          const Icon = ICON_MAP[icon] || Globe;
          const hex = getScoreHex(value);

          return (
            <div key={key} className="bg-ds-bg/50 border border-ds-silver/10 p-2 sm:p-3 flex items-center gap-3">
              <Icon className="w-4 h-4 flex-shrink-0" style={{ color: hex }} />
              <div className="flex-1 min-w-0">
                <p className="text-[9px] font-mono text-ds-silver/40 uppercase truncate">
                  {label}
                </p>
                <p className="text-sm font-grotesk font-black" style={{ color: hex }}>
                  {value != null ? `${value}%` : '—'}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

