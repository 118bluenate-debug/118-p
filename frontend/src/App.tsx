import React, { useState } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { Header } from './components/Header';
import { ScriptPanel } from './components/ScriptPanel';
import { AnalysisPanel } from './components/AnalysisPanel';
import { RecommendPanel } from './components/RecommendPanel';
import { AudioDeviceModal } from './components/AudioDeviceModal';
import { SummaryModal } from './components/SummaryModal';
import { ShieldCheck, Lock } from 'lucide-react';

export function App() {
  const { session, setSession, vuLevel, interimText, isAnalyzing, isConnected } = useWebSocket();

  const [isDeviceModalOpen, setIsDeviceModalOpen] = useState(false);
  const [isSummaryModalOpen, setIsSummaryModalOpen] = useState(false);

  // 전사 텍스트 및 화자 편집
  const handleEditTranscript = async (itemId: string, newText: string, newSpeaker: string) => {
    try {
      await fetch(`/api/session/transcript/${itemId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: newText, speaker: newSpeaker })
      });
    } catch (e) {
      console.error('발화 편집 저장 실패:', e);
    }
  };

  // 수동 AI 재분석
  const handleRefreshAnalysis = async () => {
    try {
      const res = await fetch('/api/session/analyze', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setSession((prev) => (prev ? { ...prev, latest_analysis: data } : prev));
      }
    } catch (e) {
      console.error('AI 재분석 실패:', e);
    }
  };

  // 세션 리셋
  const handleResetSession = async () => {
    if (!window.confirm('현재 상담 세션을 초기화하고 새 통화 상담을 시작하시겠습니까?')) {
      return;
    }
    try {
      const res = await fetch('/api/session/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ counselor_id: '상담사-01' })
      });
      if (res.ok) {
        const snap = await res.json();
        setSession(snap);
      }
    } catch (e) {
      console.error('세션 리셋 실패:', e);
    }
  };

  return (
    <div style={{ padding: '18px 24px', maxWidth: '1600px', margin: '0 auto' }}>
      
      {/* 최상단 헤더 */}
      <Header
        session={session}
        vuLevel={vuLevel}
        isConnected={isConnected}
        onOpenDeviceModal={() => setIsDeviceModalOpen(true)}
        onOpenSummaryModal={() => setIsSummaryModalOpen(true)}
        onResetSession={handleResetSession}
      />

      {/* 메인 2열 그리드 대시보드 */}
      <main style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '18px', minHeight: 'calc(100vh - 160px)' }}>
        
        {/* 좌측 (Section A): 실시간 통화 스크립트 */}
        <section style={{ height: '100%' }}>
          <ScriptPanel
            transcripts={session?.transcripts || []}
            interimText={interimText}
            onEditTranscript={handleEditTranscript}
          />
        </section>

        {/* 우측: Section B (AI 실시간 분석) + Section C (추천 응대 및 스크립트) */}
        <section style={{ display: 'flex', flexDirection: 'column', gap: '18px', height: '100%' }}>
          {session?.latest_analysis && (
            <>
              <AnalysisPanel
                analysis={session.latest_analysis}
                isAnalyzing={isAnalyzing}
                onRefreshAnalysis={handleRefreshAnalysis}
              />
              <RecommendPanel analysis={session.latest_analysis} />
            </>
          )}
        </section>

      </main>

      {/* 보안 정책 푸터 */}
      <footer style={{
        marginTop: '18px',
        padding: '12px 20px',
        borderRadius: '10px',
        background: 'rgba(0, 0, 0, 0.4)',
        border: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        fontSize: '0.75rem',
        color: 'var(--text-dim)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Lock size={13} color="var(--status-green)" />
          <span>외부 AI API 전송 금지 | 내부망 로컬 Faster-Whisper & Ollama 전용 | 개인정보 자동 마스킹 적용</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShieldCheck size={13} color="var(--accent-cyan)" />
          <span>KISA 한국인터넷진흥원 118 사이버상담센터 보안 규정 준수</span>
        </div>
      </footer>

      {/* 모달 레이어 */}
      <AudioDeviceModal
        isOpen={isDeviceModalOpen}
        onClose={() => setIsDeviceModalOpen(false)}
      />

      <SummaryModal
        isOpen={isSummaryModalOpen}
        onClose={() => setIsSummaryModalOpen(false)}
        session={session}
        onSaved={() => {}}
      />

    </div>
  );
}

export default App;
