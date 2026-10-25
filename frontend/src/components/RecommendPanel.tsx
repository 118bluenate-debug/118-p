import React, { useState } from 'react';
import { Lightbulb, Copy, Check, ShieldAlert, Building2, HelpCircle } from 'lucide-react';
import { RealtimeAnalysis } from '../types';

interface RecommendPanelProps {
  analysis: RealtimeAnalysis;
}

export const RecommendPanel: React.FC<RecommendPanelProps> = ({ analysis }) => {
  const [copied, setCopied] = useState<boolean>(false);

  const handleCopyScript = () => {
    if (!analysis.recommended_response_script) return;
    navigator.clipboard.writeText(analysis.recommended_response_script);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      
      {/* 패널 타이틀 */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Lightbulb size={18} color="var(--status-yellow)" />
          <h2 style={{ fontSize: '1rem', fontWeight: 700 }}>C. 추천 응대 및 표준 스크립트</h2>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          <Building2 size={13} />
          <span>{analysis.responsible_agency || 'KISA 118 상담센터'}</span>
        </div>
      </div>

      {/* 추천 응대 스크립트 박스 */}
      <div style={{
        padding: '14px 16px',
        borderRadius: '12px',
        background: 'linear-gradient(135deg, rgba(2, 132, 199, 0.12) 0%, rgba(59, 130, 246, 0.12) 100%)',
        border: '1px solid rgba(0, 229, 255, 0.3)',
        position: 'relative'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-cyan)', textTransform: 'uppercase' }}>
            KISA 118 표준 권고 멘트
          </span>
          <button
            onClick={handleCopyScript}
            className="btn-secondary"
            style={{ padding: '4px 10px', fontSize: '0.72rem' }}
            title="상담사 클립보드로 복사"
          >
            {copied ? <Check size={12} color="var(--status-green)" /> : <Copy size={12} />}
            <span>{copied ? '복사됨!' : '문구 복사'}</span>
          </button>
        </div>

        <p style={{
          fontSize: '0.92rem',
          color: '#FFFFFF',
          lineHeight: 1.6,
          fontWeight: 500,
          whiteSpace: 'pre-line'
        }}>
          {analysis.recommended_response_script ||
            '민원인의 초기 피해 정황을 청취한 후 적합한 표준 응대 멘트가 이곳에 추천됩니다.'}
        </p>
      </div>

      {/* 추가 확인 필요 질문 리스트 */}
      {analysis.recommended_questions && analysis.recommended_questions.length > 0 && (
        <div style={{
          padding: '12px 14px',
          borderRadius: '10px',
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid var(--border-subtle)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px' }}>
            <HelpCircle size={14} color="var(--accent-blue)" />
            <span>상담사 추가 확인 권장 질문</span>
          </div>
          <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {analysis.recommended_questions.map((q, idx) => (
              <li
                key={idx}
                style={{
                  fontSize: '0.85rem',
                  color: 'var(--text-main)',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '8px',
                  padding: '4px 0'
                }}
              >
                <span style={{ color: 'var(--accent-cyan)', fontWeight: 700 }}>Q{idx + 1}.</span>
                <span>{q}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 긴급 주의사항 및 조치 가이드 */}
      {analysis.caution_notes && analysis.caution_notes.length > 0 && (
        <div style={{
          padding: '12px 14px',
          borderRadius: '10px',
          background: 'rgba(244, 63, 94, 0.06)',
          border: '1px solid rgba(244, 63, 94, 0.25)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', fontWeight: 700, color: '#FDA4AF', marginBottom: '8px' }}>
            <ShieldAlert size={14} />
            <span>민원인 긴급 행동 수칙 (주의사항)</span>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
            {analysis.caution_notes.map((note, idx) => (
              <span
                key={idx}
                style={{
                  fontSize: '0.78rem',
                  padding: '4px 10px',
                  borderRadius: '6px',
                  background: 'rgba(244, 63, 94, 0.15)',
                  border: '1px solid rgba(244, 63, 94, 0.3)',
                  color: '#FFE4E6',
                  fontWeight: 500
                }}
              >
                ⚠ {note}
              </span>
            ))}
          </div>
        </div>
      )}

    </div>
  );
};
