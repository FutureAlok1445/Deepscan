import React, { useMemo } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell, ReferenceLine,
} from 'recharts';
import BrutalCard from '../ui/BrutalCard';
import { Mic, Activity, AlertTriangle, Scissors, AudioWaveform } from 'lucide-react';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-ds-dark border-2 border-ds-cyan px-3 py-2 font-mono text-xs shadow-brutal-sm">
      <p className="text-ds-cyan font-bold">{label}</p>
      {payload.map((p, i) => (
        <p key={i} className="text-ds-silver">
          {p.name}: <span className="text-ds-yellow">{p.value?.toFixed(1)} dB</span>
        </p>
      ))}
    </div>
  );
};

export default function AudioSpectrum({ audioData }) {
  if (!audioData || !audioData.spectrum?.length) {
    return (
      <BrutalCard className="text-center py-8">
        <p className="text-ds-silver/50 font-mono text-sm">No audio spectrum data available</p>
      </BrutalCard>
    );
  }

  const { spectrum, clone_probability, splicing_detected } = audioData;
  const rawAnomalies = audioData.anomalies || [];
  const anomalies = rawAnomalies.map(a => typeof a === 'string' ? { label: a } : a);

  // Calculate frequency band energy distribution for the mini bar chart
  const bandEnergy = useMemo(() => {
    if (!spectrum?.length) return [];
    const bands = [
      { name: 'Sub-Bass', range: [0, 60], color: '#9333ea' },
      { name: 'Bass', range: [60, 250], color: '#6366f1' },
      { name: 'Low-Mid', range: [250, 500], color: '#06b6d4' },
      { name: 'Mid', range: [500, 2000], color: '#00f5ff' },
      { name: 'Hi-Mid', range: [2000, 4000], color: '#facc15' },
      { name: 'Presence', range: [4000, 6000], color: '#fb923c' },
      { name: 'Brilliance', range: [6000, 20000], color: '#ef4444' },
    ];
    return bands.map(band => {
      const points = spectrum.filter(s => {
        const hz = s.freq_hz ?? parseFreqLabel(s.freq);
        return hz >= band.range[0] && hz < band.range[1];
      });
      const avg = points.length > 0
        ? points.reduce((sum, p) => sum + (p.amplitude || 0), 0) / points.length
        : 0;
      return { ...band, energy: Math.round(avg) };
    });
  }, [spectrum]);

  // Peak frequency
  const peakPoint = useMemo(() => {
    if (!spectrum?.length) return null;
    return spectrum.reduce((max, s) => (s.amplitude > (max?.amplitude || 0) ? s : max), spectrum[0]);
  }, [spectrum]);

  // Threat level based on clone probability
  const threatLevel = clone_probability > 75 ? 'CRITICAL' : clone_probability > 50 ? 'HIGH' : clone_probability > 25 ? 'MODERATE' : 'LOW';
  const threatColor = clone_probability > 75 ? 'text-ds-red' : clone_probability > 50 ? 'text-ds-yellow' : clone_probability > 25 ? 'text-ds-cyan' : 'text-ds-green';

  return (
    <BrutalCard className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h3 className="font-grotesk font-bold text-ds-silver text-lg uppercase tracking-wider flex items-center gap-2">
          <AudioWaveform className="w-5 h-5 text-ds-cyan" />
          Audio Forensics
        </h3>
        <div className="flex items-center gap-2 flex-wrap">
          {clone_probability != null && (
            <span className={`text-xs font-mono px-2 py-1 border ${
              clone_probability > 60 ? 'text-ds-red border-ds-red bg-ds-red/10' : 'text-ds-green border-ds-green bg-ds-green/10'
            }`}>
              Clone: {clone_probability}%
            </span>
          )}
          {splicing_detected != null && (
            <span className={`text-xs font-mono px-2 py-1 border flex items-center gap-1 ${
              splicing_detected ? 'text-ds-red border-ds-red bg-ds-red/10' : 'text-ds-green border-ds-green bg-ds-green/10'
            }`}>
              <Scissors className="w-3 h-3" />
              {splicing_detected ? 'SPLICE DETECTED' : 'NO SPLICE'}
            </span>
          )}
        </div>
      </div>

      {/* Threat + Peak Stats Row */}
      <div className="grid grid-cols-3 gap-2">
        <div className="bg-ds-dark/50 border border-ds-silver/10 px-3 py-2">
          <p className="text-[10px] font-mono text-ds-silver/50 uppercase">Threat Level</p>
          <p className={`text-sm font-bold font-mono ${threatColor}`}>{threatLevel}</p>
        </div>
        <div className="bg-ds-dark/50 border border-ds-silver/10 px-3 py-2">
          <p className="text-[10px] font-mono text-ds-silver/50 uppercase">Peak Freq</p>
          <p className="text-sm font-bold font-mono text-ds-cyan">{peakPoint?.freq || '—'}</p>
        </div>
        <div className="bg-ds-dark/50 border border-ds-silver/10 px-3 py-2">
          <p className="text-[10px] font-mono text-ds-silver/50 uppercase">Anomalies</p>
          <p className={`text-sm font-bold font-mono ${anomalies.length > 0 ? 'text-ds-yellow' : 'text-ds-green'}`}>
            {anomalies.length} found
          </p>
        </div>
      </div>

      {/* Main Spectrum Chart */}
      <div>
        <p className="text-[10px] font-mono text-ds-silver/40 uppercase mb-1 tracking-widest flex items-center gap-1">
          <Activity className="w-3 h-3" /> Frequency Spectrum (FFT)
        </p>
        <div className="h-52 bg-ds-dark/30 border border-ds-silver/10 p-1">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={spectrum} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
              <defs>
                <linearGradient id="specGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00f5ff" stopOpacity={0.4} />
                  <stop offset="50%" stopColor="#00f5ff" stopOpacity={0.1} />
                  <stop offset="95%" stopColor="#00f5ff" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1a1a2e" />
              <XAxis
                dataKey="freq"
                tick={{ fontSize: 9, fill: '#555', fontFamily: 'Space Mono' }}
                stroke="#222"
                interval={Math.max(0, Math.floor(spectrum.length / 8) - 1)}
              />
              <YAxis
                tick={{ fontSize: 9, fill: '#555', fontFamily: 'Space Mono' }}
                stroke="#222"
                label={{ value: 'dB', position: 'insideTopLeft', fill: '#555', fontSize: 9 }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="amplitude"
                stroke="#00f5ff"
                strokeWidth={1.5}
                fill="url(#specGrad)"
                animationDuration={1200}
                dot={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Frequency Band Energy Distribution */}
      {bandEnergy.length > 0 && (
        <div>
          <p className="text-[10px] font-mono text-ds-silver/40 uppercase mb-1 tracking-widest flex items-center gap-1">
            <Mic className="w-3 h-3" /> Band Energy Distribution
          </p>
          <div className="h-28 bg-ds-dark/30 border border-ds-silver/10 p-1">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={bandEnergy} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1a1a2e" />
                <XAxis dataKey="name" tick={{ fontSize: 8, fill: '#555', fontFamily: 'Space Mono' }} stroke="#222" />
                <YAxis tick={{ fontSize: 8, fill: '#555' }} stroke="#222" />
                <Tooltip
                  contentStyle={{ background: '#111116', border: '2px solid #e0e0e0', fontFamily: 'Space Mono', fontSize: 11 }}
                  formatter={(v) => [`${v} dB`, 'Energy']}
                />
                <Bar dataKey="energy" animationDuration={800} radius={[2, 2, 0, 0]}>
                  {bandEnergy.map((entry, i) => (
                    <Cell key={i} fill={entry.color} fillOpacity={0.85} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Anomalies */}
      {anomalies.length > 0 && (
        <div className="space-y-1">
          <p className="text-xs font-mono text-ds-yellow uppercase tracking-wider flex items-center gap-1">
            <AlertTriangle className="w-3.5 h-3.5" />
            Anomalies Detected ({anomalies.length})
          </p>
          <div className="flex flex-wrap gap-2">
            {anomalies.map((a, i) => (
              <span
                key={i}
                className="text-xs font-mono px-2 py-1 bg-ds-yellow/10 text-ds-yellow border border-ds-yellow/30 flex items-center gap-1"
              >
                <span className="w-1.5 h-1.5 bg-ds-yellow rounded-full animate-pulse" />
                {a.label || (a.freq_start ? `${a.freq_start}-${a.freq_end}Hz` : String(a))}
              </span>
            ))}
          </div>
        </div>
      )}
    </BrutalCard>
  );
}

/** Parse a freq label like "4.2kHz" or "500Hz" into numeric Hz */
function parseFreqLabel(label) {
  if (!label) return 0;
  const s = String(label).toLowerCase();
  if (s.includes('khz')) return parseFloat(s) * 1000;
  return parseFloat(s) || 0;
}
