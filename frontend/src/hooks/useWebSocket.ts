import { useState, useEffect, useRef, useCallback } from 'react';
import { SessionSnapshot, TranscriptItem, RealtimeAnalysis, FinalSummary } from '../types';

export function useWebSocket() {
  const [session, setSession] = useState<SessionSnapshot | null>(null);
  const [vuLevel, setVuLevel] = useState<number>(0);
  const [interimText, setInterimText] = useState<string>('');
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [isConnected, setIsConnected] = useState<boolean>(false);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  const connect = useCallback(() => {
    // Vite dev 환경 proxy or 직접 접속
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.port === '5173' ? '127.0.0.1:8000' : window.location.host;
    const wsUrl = `${protocol}//${host}/ws/counselor`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
      };

      ws.onclose = () => {
        setIsConnected(false);
        // 2.5초 후 자동 재접속
        reconnectTimeoutRef.current = window.setTimeout(connect, 2500);
      };

      ws.onerror = () => {
        ws.close();
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          switch (data.type) {
            case 'session_init':
              setSession(data.snapshot);
              setInterimText(data.snapshot.interim_text || '');
              break;

            case 'vu_meter':
              setVuLevel(data.level || 0);
              break;

            case 'interim_stt':
              setInterimText(data.text || '');
              break;

            case 'final_stt':
              setInterimText('');
              setSession((prev) => {
                if (!prev) return prev;
                // 중복 방지
                const exists = prev.transcripts.some((t) => t.id === data.item.id);
                if (exists) return prev;
                return {
                  ...prev,
                  transcripts: [...prev.transcripts, data.item],
                  transcript_count: prev.transcripts.length + 1
                };
              });
              break;

            case 'transcript_edited':
              setSession((prev) => {
                if (!prev) return prev;
                return {
                  ...prev,
                  transcripts: prev.transcripts.map((t) =>
                    t.id === data.item_id
                      ? { ...t, text: data.text, speaker: data.speaker || t.speaker, edited_by_counselor: true }
                      : t
                  )
                };
              });
              break;

            case 'ai_analyzing':
              setIsAnalyzing(data.status);
              break;

            case 'ai_analysis':
              setIsAnalyzing(false);
              setSession((prev) => (prev ? { ...prev, latest_analysis: data.analysis } : prev));
              break;

            case 'recording_status':
              setSession((prev) =>
                prev ? { ...prev, recording_state: data.recording_state } : prev
              );
              break;

            case 'consultation_completed':
              setSession((prev) =>
                prev
                  ? {
                      ...prev,
                      recording_state: 'COMPLETED',
                      final_summary: data.final_summary
                    }
                  : prev
              );
              break;

            default:
              break;
          }
        } catch (e) {
          console.error('WS 메시지 파싱 오류:', e);
        }
      };
    } catch (e) {
      console.error('WS 연결 시도 실패:', e);
      reconnectTimeoutRef.current = window.setTimeout(connect, 3000);
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return {
    session,
    setSession,
    vuLevel,
    interimText,
    isAnalyzing,
    isConnected
  };
}
