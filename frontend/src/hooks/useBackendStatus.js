import { useState, useEffect, useRef } from 'react';
import { checkHealth } from '../api/deepscan';

/**
 * Polls the backend /health endpoint every `interval` ms.
 * Returns { isOnline, latency, lastChecked }
 */
export default function useBackendStatus(interval = 15000) {
  const [isOnline, setIsOnline] = useState(null); // null = unknown
  const [latency, setLatency] = useState(null);
  const [lastChecked, setLastChecked] = useState(null);
  const timer = useRef(null);

  useEffect(() => {
    let mounted = true;

    async function poll() {
      const start = Date.now();
      const { ok } = await checkHealth();
      if (!mounted) return;
      setIsOnline(ok);
      setLatency(ok ? Date.now() - start : null);
      setLastChecked(new Date());
    }

    poll(); // immediate check
    timer.current = setInterval(poll, interval);

    return () => {
      mounted = false;
      clearInterval(timer.current);
    };
  }, [interval]);

  return { isOnline, latency, lastChecked };
}
