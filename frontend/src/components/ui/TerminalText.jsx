import React, { useState, useEffect } from 'react';

export default function TerminalText({
  text = '',
  speed = 40,
  className = '',
  cursor = true,
  onComplete,
}) {
  const [displayed, setDisplayed] = useState('');
  const [done, setDone] = useState(false);

  useEffect(() => {
    setDisplayed('');
    setDone(false);
    let i = 0;
    const interval = setInterval(() => {
      i++;
      setDisplayed(text.slice(0, i));
      if (i >= text.length) {
        clearInterval(interval);
        setDone(true);
        onComplete?.();
      }
    }, speed);
    return () => clearInterval(interval);
  }, [text, speed]);

  return (
    <span className={`font-mono ${className}`}>
      {displayed}
      {cursor && !done && (
        <span className="inline-block w-2 h-4 bg-ds-green ml-0.5 animate-blink align-middle" />
      )}
    </span>
  );
}
