import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, Edit2, Check, User, Headphones, Shuffle, Radio } from 'lucide-react';
import { TranscriptItem } from '../types';

interface ScriptPanelProps {
  transcripts: TranscriptItem[];
  interimText: string;
  onEditTranscript: (itemId: string, newText: string, newSpeaker: string) => void;
}

export const ScriptPanel: React.FC<ScriptPanelProps> = ({
  transcripts,
  interimText,
  onEditTranscript
}) => {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState<string>('');
  const [editSpeaker, setEditSpeaker] = useState<'상담사' | '민원인' | '혼합/식별중'>('민원인');

  const scrollRef = useRef<HTMLDivElement>(null);

  // 새 발화 추가 시 자동 스크롤
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [transcripts, interimText]);

  const handleStartEdit = (item: TranscriptItem) => {
    setEditingId(item.id);
    setEditText(item.text);
    setEditSpeaker(item.speaker);
  };

  const handleSaveEdit = (itemId: string) => {
    onEditTranscript(itemId, editText, editSpeaker);
    setEditingId(null);
  };

  const toggleSpeaker = (current: '상담사' | '민원인' | '혼합/식별중'): '상담사' | '민원인' | '혼합/식별중' => {
    if (current === '민원인') return '상담사';
    if (current === '상담사') return '혼합/식별중';
    return '민원인';
  };

  return (
    <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: '580px' }}>
      
      {/* 패널 헤더 */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <MessageSquare size={18} color="var(--accent-cyan)" />
          <h2 style={{ fontSize: '1rem', fontWeight: 700 }}>A. 실시간 통화 스크립트</h2>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          <span>화자 배지 클릭 시 변경</span>
          <span style={{ padding: '2px 8px', borderRadius: '4px', background: 'rgba(255, 255, 255, 0.05)', fontFamily: 'var(--font-mono)' }}>
            총 {transcripts.length}건
          </span>
        </div>
      </div>

      {/* 발화 목록 영역 */}
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          padding: '20px',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '14px'
        }}
      >
        {transcripts.length === 0 && !interimText && (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            color: 'var(--text-dim)',
            gap: '10px'
          }}>
            <Radio size={36} strokeWidth={1.5} />
            <p style={{ fontSize: '0.9rem' }}>Line-in 오디오 입력을 대기하고 있습니다.</p>
            <p style={{ fontSize: '0.78rem' }}>통화가 시작되면 실시간으로 한글 전사가 표출됩니다.</p>
          </div>
        )}

        {transcripts.map((item) => {
          const isEditing = editingId === item.id;
          const isCaller = item.speaker === '민원인';
          const isCounselor = item.speaker === '상담사';

          return (
            <div
              key={item.id}
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '6px',
                padding: '12px 16px',
                borderRadius: '12px',
                background: isCaller
                  ? 'rgba(244, 63, 94, 0.06)'
                  : isCounselor
                  ? 'rgba(59, 130, 246, 0.06)'
                  : 'rgba(255, 255, 255, 0.03)',
                border: `1px solid ${
                  isCaller
                    ? 'rgba(244, 63, 94, 0.2)'
                    : isCounselor
                    ? 'rgba(59, 130, 246, 0.2)'
                    : 'var(--border-subtle)'
                }`,
                transition: 'background 0.2s ease'
              }}
            >
              {/* 메타정보: 화자, 타임스탬프, 수정 버튼 */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <button
                    onClick={() => {
                      const next = toggleSpeaker(item.speaker);
                      onEditTranscript(item.id, item.text, next);
                    }}
                    title="클릭하여 화자 변경"
                    className={
                      isCaller
                        ? 'badge-caller'
                        : isCounselor
                        ? 'badge-counselor'
                        : 'badge-mixed'
                    }
                    style={{
                      padding: '3px 10px',
                      borderRadius: '6px',
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    {isCaller && <User size={12} />}
                    {isCounselor && <Headphones size={12} />}
                    {!isCaller && !isCounselor && <Shuffle size={12} />}
                    {item.speaker}
                  </button>

                  <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
                    {item.timestamp_str}
                  </span>

                  {item.edited_by_counselor && (
                    <span style={{ fontSize: '0.68rem', color: 'var(--accent-cyan)' }}>
                      [상담사 교정됨]
                    </span>
                  )}
                </div>

                {/* 신뢰도 및 편집 버튼 */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>
                    신뢰도 {Math.round(item.confidence * 100)}%
                  </span>
                  <button
                    onClick={() => handleStartEdit(item)}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: 'var(--text-muted)',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center'
                    }}
                    title="STT 텍스트 직접 교정"
                  >
                    <Edit2 size={13} />
                  </button>
                </div>
              </div>

              {/* 발화 본문 또는 편집 인풋 */}
              {isEditing ? (
                <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                  <input
                    type="text"
                    value={editText}
                    onChange={(e) => setEditText(e.target.value)}
                    style={{
                      flex: 1,
                      padding: '8px 12px',
                      borderRadius: '6px',
                      background: 'rgba(0, 0, 0, 0.4)',
                      border: '1px solid var(--accent-cyan)',
                      color: '#FFFFFF',
                      fontSize: '0.9rem',
                      outline: 'none'
                    }}
                    onKeyDown={(e) => e.key === 'Enter' && handleSaveEdit(item.id)}
                    autoFocus
                  />
                  <button
                    className="btn-primary"
                    style={{ padding: '6px 12px', fontSize: '0.8rem' }}
                    onClick={() => handleSaveEdit(item.id)}
                  >
                    <Check size={14} /> 저장
                  </button>
                </div>
              ) : (
                <p style={{
                  fontSize: '0.95rem',
                  lineHeight: 1.6,
                  color: '#FFFFFF',
                  fontWeight: 450,
                  wordBreak: 'break-word'
                }}>
                  {item.text}
                </p>
              )}
            </div>
          );
        })}

        {/* 실시간 중간 전사 (Interim) 배너 */}
        {interimText && (
          <div style={{
            padding: '12px 16px',
            borderRadius: '12px',
            background: 'rgba(0, 229, 255, 0.08)',
            border: '1px dashed rgba(0, 229, 255, 0.4)',
            display: 'flex',
            alignItems: 'center',
            gap: '10px'
          }}>
            <div style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: 'var(--accent-cyan)'
            }} className="animate-pulse-recording" />
            <p style={{
              fontSize: '0.92rem',
              color: 'var(--accent-cyan)',
              fontStyle: 'italic',
              flex: 1
            }}>
              {interimText}
            </p>
            <span style={{ fontSize: '0.7rem', color: 'rgba(0, 229, 255, 0.7)' }}>
              실시간 인식중...
            </span>
          </div>
        )}
      </div>

    </div>
  );
};
