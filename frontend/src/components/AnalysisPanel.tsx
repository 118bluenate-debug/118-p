import React from 'react';
import { Sparkles, CheckCircle, AlertTriangle, HelpCircle, ArrowUpRight, RefreshCw } from 'lucide-react';
import { RealtimeAnalysis } from '../types';

interface AnalysisPanelProps {
  analysis: RealtimeAnalysis;
  isAnalyzing: boolean;
  onRefreshAnalysis: () => void;
}

export const AnalysisPanel: React.FC<AnalysisPanelProps> = ({
  analysis,
  isAnalyzing,
  onRefreshAnalysis
}) => {
  const isEscalationNeeded = analysis.escalation_needed === '즉시 이관 권고';
  const isCheckNeeded = analysis.escalation_needed === '확인 필요';

  return (
    <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      
      {/* 헤더: 섹션 제목 및 카테고리 태그 */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sparkles size={18} color="var(--accent-cyan)" />
          <h2 style={{ fontSize: '1rem', fontWeight: 700 }}>B. AI 실시간 분석</h2>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={onRefreshAnalysis}
            disabled={isAnalyzing}
            className="btn-secondary"
            style={{ padding: '4px 10px', fontSize: '0.75rem' }}
            title="Ollama 모델로 즉시 재분석"
          >
            <RefreshCw size={12} className={isAnalyzing ? 'animate-spin' : ''} />
            {isAnalyzing ? '분석중...' : 'AI 재분석'}
          </button>
          <div className="category-pill">
            {analysis.counseling_category || '유형 분석 대기'}
          </div>
        </div>
      </div>

      {/* 이관 필요성 알림 배너 */}
      {(isEscalationNeeded || isCheckNeeded) && (
        <div style={{
          padding: '10px 14px',
          borderRadius: '8px',
          background: isEscalationNeeded ? 'rgba(244, 63, 94, 0.15)' : 'rgba(245, 158, 11, 0.15)',
          border: `1px solid ${isEscalationNeeded ? 'rgba(244, 63, 94, 0.4)' : 'rgba(245, 158, 11, 0.4)'}`,
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <AlertTriangle size={18} color={isEscalationNeeded ? 'var(--status-rose)' : 'var(--status-yellow)'} />
          <div style={{ fontSize: '0.85rem' }}>
            <span style={{ fontWeight: 700, color: isEscalationNeeded ? '#FDA4AF' : '#FDE68A' }}>
              [{analysis.escalation_needed}]
            </span>{' '}
            <span style={{ color: 'var(--text-main)' }}>
              {analysis.escalation_reason || '피해 규모 확인 및 전문 수사/보안 부서 이관 검토 필요'}
            </span>
          </div>
        </div>
      )}

      {/* 민원인 핵심 요구사항 */}
      <div style={{
        padding: '12px 14px',
        borderRadius: '10px',
        background: 'rgba(255, 255, 255, 0.03)',
        border: '1px solid var(--border-subtle)'
      }}>
        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--accent-cyan)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
          민원인 핵심 요구사항
        </div>
        <p style={{ fontSize: '0.9rem', color: '#FFFFFF', fontWeight: 500, lineHeight: 1.5 }}>
          {analysis.core_intent || '민원인의 발화 내용이 수집되면 핵심 의도를 도출합니다.'}
        </p>
      </div>

      {/* 현재까지 상담 요약 */}
      <div style={{
        padding: '12px 14px',
        borderRadius: '10px',
        background: 'rgba(255, 255, 255, 0.03)',
        border: '1px solid var(--border-subtle)'
      }}>
        <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '4px' }}>
          상담 진행 요약
        </div>
        <p style={{ fontSize: '0.88rem', color: 'var(--text-main)', lineHeight: 1.55 }}>
          {analysis.current_summary || '대화가 진행됨에 따라 실시간 요약이 갱신됩니다.'}
        </p>
      </div>

      {/* 객관적 사실 vs 민원인 주장 2열 그리드 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        
        {/* 객관적 확인 사실 */}
        <div style={{
          padding: '12px',
          borderRadius: '10px',
          background: 'rgba(16, 185, 129, 0.05)',
          border: '1px solid rgba(16, 185, 129, 0.2)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', fontWeight: 700, color: '#6EE7B7', marginBottom: '8px' }}>
            <CheckCircle size={14} /> 확인된 사실
          </div>
          {analysis.objective_facts && analysis.objective_facts.length > 0 ? (
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {analysis.objective_facts.map((fact, idx) => (
                <li key={idx} style={{ fontSize: '0.8rem', color: '#D1FAE5', lineHeight: 1.4, display: 'flex', gap: '6px' }}>
                  <span>•</span> <span>{fact}</span>
                </li>
              ))}
            </ul>
          ) : (
            <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>확인된 사실 없음</span>
          )}
        </div>

        {/* 민원인 주장 및 미확인 사항 */}
        <div style={{
          padding: '12px',
          borderRadius: '10px',
          background: 'rgba(245, 158, 11, 0.05)',
          border: '1px solid rgba(245, 158, 11, 0.2)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', fontWeight: 700, color: '#FCD34D', marginBottom: '8px' }}>
            <HelpCircle size={14} /> 민원인 주장 / 확인필요
          </div>
          {analysis.caller_claims && analysis.caller_claims.length > 0 ? (
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {analysis.caller_claims.map((claim, idx) => (
                <li key={idx} style={{ fontSize: '0.8rem', color: '#FEF3C7', lineHeight: 1.4, display: 'flex', gap: '6px' }}>
                  <span>•</span> <span>{claim}</span>
                </li>
              ))}
            </ul>
          ) : (
            <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>특이 주장 없음</span>
          )}
        </div>

      </div>

    </div>
  );
};
