import React from 'react';

export default function ScanLine({ className = '' }) {
  return (
    <div
      className={`pointer-events-none fixed inset-0 z-50 scanlines opacity-[0.03] ${className}`}
      aria-hidden="true"
    />
  );
}
