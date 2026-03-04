import React from 'react';

export default function PaperTear({ flip = false, className = '' }) {
  return (
    <div
      className={`w-full overflow-hidden leading-[0] ${flip ? 'rotate-180' : ''} ${className}`}
      aria-hidden="true"
    >
      <svg
        viewBox="0 0 1440 60"
        preserveAspectRatio="none"
        className="w-full h-8 md:h-12"
      >
        <path
          d="M0,0 L40,20 L80,5 L120,25 L160,8 L200,22 L240,3 L280,28 L320,10 L360,20 L400,2 L440,30 L480,8 L520,25 L560,5 L600,22 L640,12 L680,28 L720,4 L760,20 L800,10 L840,26 L880,6 L920,24 L960,8 L1000,22 L1040,4 L1080,28 L1120,10 L1160,20 L1200,2 L1240,25 L1280,8 L1320,22 L1360,5 L1400,18 L1440,0 L1440,60 L0,60 Z"
          fill="#0a0a0f"
        />
      </svg>
    </div>
  );
}
