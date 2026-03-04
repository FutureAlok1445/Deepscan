import React from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts';
import BrutalCard from '../ui/BrutalCard';
import { HeartPulse } from 'lucide-react';

export default function HeartbeatChart({ heartbeatData }) {
  if (!heartbeatData) {
    return (
      <BrutalCard className="text-center py-8">
        <p className="text-ds-silver/50 font-mono text-sm">No heartbeat data available</p>
      </BrutalCard>
    );
  }

  // Normalize: accept `data`, `signal`, or top-level array
  const rawData = heartbeatData.data || heartbeatData.signal || [];
  // Ensure each point has { time, value }
  const data = rawData.map((p, i) => ({
    time: p.time ?? p.t ?? i,
    value: p.value ?? p.amplitude ?? p.v ?? 0,
  }));

  if (!data.length) {
    return (
      <BrutalCard className="text-center py-8">
        <p className="text-ds-silver/50 font-mono text-sm">No heartbeat data available</p>
      </BrutalCard>
    );
  }

  const bpm = heartbeatData.bpm ?? heartbeatData.heart_rate ?? 0;
  const isNatural = heartbeatData.is_natural ?? !heartbeatData.is_deepfake ?? true;
  const anomalies = heartbeatData.anomalies || [];

  return (
    <BrutalCard className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-grotesk font-bold text-ds-silver text-lg uppercase tracking-wider flex items-center gap-2">
          <HeartPulse className="w-5 h-5 text-ds-red" />
          rPPG Heartbeat
        </h3>
        <div className="flex items-center gap-3">
          {bpm && (
            <span className="text-sm font-mono text-ds-red font-bold">
              {bpm} BPM
            </span>
          )}
          <span
            className={`text-xs font-mono px-2 py-1 border ${
              isNatural
                ? 'text-ds-green border-ds-green bg-ds-green/10'
                : 'text-ds-red border-ds-red bg-ds-red/10'
            }`}
          >
            {isNatural ? 'NATURAL' : 'ANOMALOUS'}
          </span>
        </div>
      </div>

      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#222" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 10, fill: '#666', fontFamily: 'Space Mono' }}
              stroke="#333"
            />
            <YAxis
              tick={{ fontSize: 10, fill: '#666', fontFamily: 'Space Mono' }}
              stroke="#333"
            />
            <Tooltip
              contentStyle={{
                background: '#111116',
                border: '2px solid #e0e0e0',
                fontFamily: 'Space Mono',
                fontSize: 12,
              }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#ff3c00"
              strokeWidth={2}
              dot={false}
              animationDuration={1500}
            />
            {anomalies.map((a, i) => (
              <ReferenceLine
                key={i}
                x={a.time}
                stroke="#ffd700"
                strokeDasharray="4 4"
                label={{ value: '!', fill: '#ffd700', fontSize: 10 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </BrutalCard>
  );
}
