import React, { useEffect, useRef } from 'react';
import { getScoreHex } from '../../utils/formatters';

export default function TrustScoreGauge({ score = 0, size = 200, label = 'Fake Probability' }) {
  const canvasRef = useRef(null);
  const animRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    ctx.scale(dpr, dpr);

    const cx = size / 2;
    const cy = size / 2;
    const radius = size / 2 - 16;
    const lineWidth = 12;
    const startAngle = 0.75 * Math.PI;
    const endAngle = 2.25 * Math.PI;
    const totalArc = endAngle - startAngle;

    let current = 0;
    const target = Math.min(100, Math.max(0, score));
    const color = getScoreHex(score);

    function draw() {
      ctx.clearRect(0, 0, size, size);

      // Track
      ctx.beginPath();
      ctx.arc(cx, cy, radius, startAngle, endAngle);
      ctx.strokeStyle = '#222';
      ctx.lineWidth = lineWidth;
      ctx.lineCap = 'round';
      ctx.stroke();

      // Value arc
      const valueAngle = startAngle + (current / 100) * totalArc;
      ctx.beginPath();
      ctx.arc(cx, cy, radius, startAngle, valueAngle);
      ctx.strokeStyle = color;
      ctx.lineWidth = lineWidth;
      ctx.lineCap = 'round';
      ctx.stroke();

      // Score text
      ctx.fillStyle = color;
      ctx.font = `bold ${size * 0.22}px "Space Grotesk", sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(`${Math.round(current)}%`, cx, cy - 4);

      // Label
      ctx.fillStyle = '#888';
      ctx.font = `${size * 0.07}px "Space Mono", monospace`;
      ctx.fillText(label.toUpperCase(), cx, cy + size * 0.16);
    }

    function animate() {
      if (current < target) {
        current += Math.max(0.5, (target - current) * 0.08);
        if (current > target) current = target;
        draw();
        animRef.current = requestAnimationFrame(animate);
      } else {
        current = target;
        draw();
      }
    }

    animate();
    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };
  }, [score, size, label]);

  return (
    <div className="flex flex-col items-center">
      <canvas
        ref={canvasRef}
        style={{ width: size, height: size }}
        className="drop-shadow-[0_0_20px_rgba(255,60,0,0.3)]"
      />
    </div>
  );
}
