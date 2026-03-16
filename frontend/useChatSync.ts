import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Custom hook to synchronize chat state with the FastAPI backend via WebSockets.
 */
export const useChatSync = (userId: string, serverUrl: string) => {
  const [messages, setMessages] = useState<any[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (socketRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(`${serverUrl}/ws/${userId}`);
    socketRef.current = ws;

    ws.onopen = () => {
      console.log('Connected to ChatSync');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      // Synchronize state with incoming message (including AI response)
      setMessages((prev) => [...prev, {
        role: 'user',
        content: data.user_message,
        timestamp: data.timestamp
      }, {
        role: 'ai',
        content: data.ai_response,
        timestamp: data.timestamp
      }]);
    };

    ws.onclose = () => {
      console.log('Disconnected from ChatSync');
      setIsConnected(false);
      // Simple reconnection logic
      setTimeout(connect, 3000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket Error:', error);
      ws.close();
    };
  }, [userId, serverUrl]);

  useEffect(() => {
    connect();
    return () => {
      socketRef.current?.close();
    };
  }, [connect]);

  const sendMessage = (text: string) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ text }));
    } else {
      console.warn('Cannot send message, socket not connected');
    }
  };

  return { messages, isConnected, sendMessage };
};
