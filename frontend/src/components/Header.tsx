import React from 'react';
import { Shield, Mic, RefreshCw, CheckCircle2, Sliders, Activity } from 'lucide-react';
import { SessionSnapshot } from '../types';

interface HeaderProps {
  session: SessionSnapshot | null;
  vuLevel: number;
  isConnected: boolean;
  onOpenDeviceModal: () => void;
  onOpenSummaryModal: () => void;
  onResetSession: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  session,
  vuLevel,
  isConnected,
  onOpenDeviceModal,
  onOpenSummaryModal,
  onResetSession
}) => {
  const isRecording = session?.recording_state === 'RECORDING';
  const isCompleted = session?.recording_state === 'COMPLETED';

  return (
    <header className="glass-panel" style={{ padding: '14px 24px', marginBottom: '16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        
        {/* 로고 및 시스템 타이틀 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            width: '44px',
            height: '44px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #0284C7 0%, #3B82F6 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 16px rgba(2, 132, 199, 0.4)'
          }}>
            <Shield size={26} color="#FFFFFF" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h1 style={{ fontSize: '1.25rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#FFFFFF' }}>
                118 팔배개 <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-cyan)' }}>PAL-BEGAE</span>
              </h1>
              <span style={{
                fontSize: '0.7rem',
                padding: '2px 8px',
                borderRadius: '6px',
                background: 'rgba(2, 132, 199, 0.2)',
                border: '1px solid rgba(0, 229, 255, 0.3)',
                color: '#E0F2FE'
              }}>
                내부망 전용 로컬 AI
              </span>
            </div>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              한국인터넷진흥원(KISA) 118 상담센터 실시간 AI 상담지원 시스템
            </p>
          </div>
        </div>

        {/* 중앙: Line-in VU 미터 및 녹음 상태 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          {/* 상태 배지 */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 14px',
            borderRadius: '9999px',
            background: isRecording ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255, 255, 255, 0.05)',
            border: `1px solid ${isRecording ? 'rgba(16, 185, 129, 0.4)' : 'var(--border-subtle)'}`
          }}>
            <div style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              background: isRecording ? '#10B981' : (isCompleted ? '#00E5FF' : '#6B7280'),
            }} className={isRecording ? 'animate-pulse-recording' : ''} />
            <span style={{
              fontSize: '0.8rem',
              fontWeight: 700,
              color: isRecording ? '#A7F3D0' : (isCompleted ? '#BAE6FD' : '#9CA3AF')
            }}>
              {isRecording ? 'LINE-IN 수집중' : (isCompleted ? '상담 완료' : '수집 대기')}
            </span>
          </div>

          {/* 실시간 볼륨 레벨 (VU) */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', width: '130px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Activity size={12} /> Line-in VU
              </span>
              <span style={{ fontFamily: 'var(--font-mono)' }}>{vuLevel}%</span>
            </div>
            <div className="vu-meter-bar">
              <div className="vu-meter-fill" style={{ width: `${vuLevel}%` }} />
            </div>
          </div>
        </div>

        {/* 우측: 장치 설정, 세션 ID 및 상담 종료 버튼 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            className="btn-secondary"
            onClick={onOpenDeviceModal}
            title="Windows Line-in 오디오 장치 선택"
          >
            <Sliders size={16} />
            <span>장치 설정</span>
          </button>

          <button
            className="btn-secondary"
            onClick={onResetSession}
            title="새 상담 세션으로 초기화"
          >
            <RefreshCw size={15} />
            <span>세션 리셋</span>
          </button>

          <button
            className="btn-primary"
            onClick={onOpenSummaryModal}
            style={{ padding: '8px 18px' }}
          >
            <CheckCircle2 size={16} />
            <span>상담 종료 및 CRM 저장</span>
          </button>
        </div>

      </div>
    </header>
  );
};
