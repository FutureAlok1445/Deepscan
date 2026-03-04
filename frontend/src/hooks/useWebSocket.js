import { useState, useEffect, useRef, useCallback } from 'react';
import { WS_URL } from '../api/deepscan';

export default function useWebSocket(jobId) {
  const [messages, setMessages] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const wsRef = useRef(null);

  const connect = useCallback(() => {
    if (!jobId) return;
    try {
      const ws = new WebSocket(`${WS_URL}/ws/live?job_id=${jobId}`);
      wsRef.current = ws;

      ws.onopen = () => setIsConnected(true);
      ws.onclose = () => setIsConnected(false);
      ws.onerror = () => setIsConnected(false);

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setMessages((prev) => [...prev, data]);
          setLastMessage(data);
        } catch {
          // ignore non-JSON messages
        }
      };
    } catch {
      setIsConnected(false);
    }
  }, [jobId]);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  return { messages, isConnected, lastMessage };
}
