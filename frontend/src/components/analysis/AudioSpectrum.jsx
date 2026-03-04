import React from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import BrutalCard from '../ui/BrutalCard';
import { Mic } from 'lucide-react';

export default function AudioSpectrum({ audioData }) {
  if (!audioData || !audioData.spectrum?.length) {
    return (
      <BrutalCard className="text-center py-8">
        <p className="text-ds-silver/50 font-mono text-sm">No audio spectrum data available</p>
      </BrutalCard>
    );
  }

  const { spectrum, clone_probability, splicing_detected } = audioData;
  // Backend sends anomalies as strings, mock sends as objects
  const rawAnomalies = audioData.anomalies || [];
  const anomalies = rawAnomalies.map(a => typeof a === 'string' ? { label: a } : a);

  return (
    <BrutalCard className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h3 className="font-grotesk font-bold text-ds-silver text-lg uppercase tracking-wider flex items-center gap-2">
          <Mic className="w-5 h-5 text-ds-cyan" />
          Audio Analysis
        </h3>
        <div className="flex items-center gap-2">
          {clone_probability != null && (
            <span className={`text-xs font-mono px-2 py-1 border ${
              clone_probability > 60 ? 'text-ds-red border-ds-red bg-ds-red/10' : 'text-ds-green border-ds-green bg-ds-green/10'
            }`}>
              Clone: {clone_probability}%
            </span>
          )}
          {splicing_detected != null && (
            <span className={`text-xs font-mono px-2 py-1 border ${
              splicing_detected ? 'text-ds-red border-ds-red bg-ds-red/10' : 'text-ds-green border-ds-green bg-ds-green/10'
            }`}>
              {splicing_detected ? 'SPLICE DETECTED' : 'NO SPLICE'}
            </span>
          )}
        </div>
      </div>

      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={spectrum} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
            <defs>
              <linearGradient id="specGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#00f5ff" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#00f5ff" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#222" />
            <XAxis
              dataKey="freq"
              tick={{ fontSize: 10, fill: '#666', fontFamily: 'Space Mono' }}
              stroke="#333"
              label={{ value: 'Hz', position: 'insideBottomRight', fill: '#666', fontSize: 10 }}
            />
            <YAxis
              tick={{ fontSize: 10, fill: '#666', fontFamily: 'Space Mono' }}
              stroke="#333"
              label={{ value: 'dB', position: 'insideTopLeft', fill: '#666', fontSize: 10 }}
            />
            <Tooltip
              contentStyle={{
                background: '#111116',
                border: '2px solid #e0e0e0',
                fontFamily: 'Space Mono',
                fontSize: 12,
              }}
            />
            <Area
              type="monotone"
              dataKey="amplitude"
              stroke="#00f5ff"
              strokeWidth={2}
              fill="url(#specGrad)"
              animationDuration={1500}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {anomalies.length > 0 && (
        <div className="space-y-1">
          <p className="text-xs font-mono text-ds-yellow uppercase tracking-wider">
            Anomalies Detected
          </p>
          <div className="flex flex-wrap gap-2">
            {anomalies.map((a, i) => (
              <span
                key={i}
                className="text-xs font-mono px-2 py-1 bg-ds-yellow/10 text-ds-yellow border border-ds-yellow/30"
              >
                {a.label || (a.freq_start ? `${a.freq_start}-${a.freq_end}Hz` : String(a))}
              </span>
            ))}
          </div>
        </div>
      )}
    </BrutalCard>
  );
}
