import React from 'react';

const VARIANTS = {
  red: 'bg-ds-red/30 text-ds-red border-ds-red',
  green: 'bg-ds-green/30 text-ds-green border-ds-green',
  yellow: 'bg-ds-yellow/30 text-ds-yellow border-ds-yellow',
  cyan: 'bg-ds-cyan/30 text-ds-cyan border-ds-cyan',
  silver: 'bg-ds-silver/30 text-ds-silver border-ds-silver',
};

export default function BrutalBadge({
  children,
  variant = 'silver',
  className = '',
  pulse = false,
  ...props
}) {
  return (
    <span
      className={`
        inline-flex items-center gap-1.5
        px-2.5 py-1 text-xs font-mono font-bold uppercase tracking-widest
        border-2
        ${VARIANTS[variant] || VARIANTS.silver}
        ${className}
      `}
      {...props}
    >
      {pulse && (
        <span className="relative flex h-2 w-2">
          <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${variant === 'red' ? 'bg-ds-red' : variant === 'green' ? 'bg-ds-green' : 'bg-ds-yellow'}`} />
          <span className={`relative inline-flex rounded-full h-2 w-2 ${variant === 'red' ? 'bg-ds-red' : variant === 'green' ? 'bg-ds-green' : 'bg-ds-yellow'}`} />
        </span>
      )}
      {children}
    </span>
  );
}
