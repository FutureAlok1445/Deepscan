import React from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, CartesianGrid } from 'recharts';
import BrutalCard from '../ui/BrutalCard';
import { Activity } from 'lucide-react';

export default function TrajectoryPlot({ trajectoryData = [] }) {
    if (!trajectoryData || trajectoryData.length === 0) {
        return null;
    }

    // Format data for Recharts
    const chartData = trajectoryData.map((val, index) => ({
        frame: index + 1,
        smoothness: val,
    }));

    // Determine if it's generally failing
    const avgSmoothness = trajectoryData.reduce((a, b) => a + b, 0) / trajectoryData.length;
    const isJittery = avgSmoothness < 0.65;

    const CustomTooltip = ({ active, payload }) => {
        if (active && payload && payload.length) {
            const val = payload[0].value;
            const isDip = val < 0.5;
            return (
                <div className="bg-ds-bg border-2 border-ds-silver p-3 shadow-[4px_4px_0_theme(colors.ds-red)]">
                    <p className="font-mono text-sm text-ds-silver">Window: {payload[0].payload.frame}</p>
                    <p className={`font-grotesk font-bold ${isDip ? 'text-ds-red' : 'text-ds-green'}`}>
                        Smoothness: {val.toFixed(2)}
                    </p>
                    {isDip && (
                        <p className="text-xs font-mono text-ds-red mt-1">
                            ⚠️ Physics Violation: Vector Collapse
                        </p>
                    )}
                </div>
            );
        }
        return null;
    };

    return (
        <div className="space-y-3">
            <div className="flex items-center justify-between">
                <h3 className="flex items-center gap-2 font-grotesk font-bold text-ds-silver text-lg uppercase tracking-wider">
                    <Activity className="w-5 h-5 text-ds-cyan" />
                    Latent Motion Stability (Physics Check)
                </h3>
                {isJittery && (
                    <span className="text-xs font-mono bg-ds-red text-white px-2 py-1 uppercase tracking-widest font-bold">
                        Unnatural Physics Detected
                    </span>
                )}
            </div>

            <BrutalCard className="p-4 bg-ds-bg/50">
                <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#888" opacity={0.2} vertical={false} />

                            <XAxis
                                dataKey="frame"
                                stroke="#666"
                                tick={{ fill: '#666', fontSize: 12, fontFamily: 'monospace' }}
                                tickLine={false}
                                axisLine={false}
                            />

                            <YAxis
                                domain={[0, 1]}
                                stroke="#666"
                                tick={{ fill: '#666', fontSize: 12, fontFamily: 'monospace' }}
                                tickLine={false}
                                axisLine={false}
                                tickFormatter={(val) => val.toFixed(1)}
                            />

                            <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#666', strokeWidth: 1, strokeDasharray: '5 5' }} />

                            {/* Threshold Line */}
                            <ReferenceLine y={0.65} stroke="#ff3c00" strokeDasharray="3 3" opacity={0.5} label={{ position: 'top', value: 'Instability Threshold', fill: '#ff3c00', fontSize: 10, fontFamily: 'monospace' }} />

                            <Line
                                type="monotone"
                                dataKey="smoothness"
                                stroke={isJittery ? "#ff3c00" : "#39ff14"}
                                strokeWidth={3}
                                dot={false}
                                activeDot={{ r: 6, fill: '#fff', stroke: '#000', strokeWidth: 2 }}
                                animationDuration={1500}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
                <p className="text-xs font-mono text-ds-silver/50 mt-4 text-center">
                    Analyzes the <span className="text-ds-cyan">Latent Trajectory</span> through an R(2+1)D neural network.<br />
                    Real video maintains smooth momentum (+0.8). AI generates erratic, zigzagging vectors.
                </p>
            </BrutalCard>
        </div>
    );
}
