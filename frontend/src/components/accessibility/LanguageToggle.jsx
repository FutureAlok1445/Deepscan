import React, { useState, useRef, useEffect } from 'react';
import { Globe } from 'lucide-react';
import { LANGUAGES } from '../../utils/constants';

export default function LanguageToggle({ currentLang = 'en', onChangeLang }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const current = LANGUAGES.find((l) => l.code === currentLang) || LANGUAGES[0];

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono text-ds-silver/70 border-2 border-ds-silver/30 hover:border-ds-silver transition-colors"
        aria-label="Change language"
      >
        <Globe className="w-3.5 h-3.5" />
        {current.label}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-1 bg-ds-card border-3 border-ds-silver brutal-shadow z-50 min-w-[140px]">
          {LANGUAGES.map((lang) => (
            <button
              key={lang.code}
              onClick={() => {
                onChangeLang?.(lang.code);
                setOpen(false);
              }}
              className={`w-full text-left px-3 py-2 text-sm font-mono transition-colors hover:bg-ds-silver/10 ${
                lang.code === currentLang ? 'text-ds-red bg-ds-red/5' : 'text-ds-silver/70'
              }`}
            >
              {lang.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
