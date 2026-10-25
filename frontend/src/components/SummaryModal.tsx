import React, { useState, useEffect } from 'react';
import { X, CheckCircle, Download, Database, ShieldCheck, AlertCircle } from 'lucide-react';
import { SessionSnapshot, FinalSummary } from '../types';

interface SummaryModalProps {
  isOpen: boolean;
  onClose: () => void;
  session: SessionSnapshot | null;
  onSaved: () => void;
}

export const SummaryModal: React.FC<SummaryModalProps> = ({
  isOpen,
  onClose,
  session,
  onSaved
}) => {
  const [category, setCategory] = useState<string>('스미싱/악성앱');
  const [callerIntent, setCallerIntent] = useState<string>('');
  const [summaryText, setSummaryText] = useState<string>('');
  const [actionTaken, setActionTaken] = useState<string>('');
  const [relatedAgency, setRelatedAgency] = useState<string>('KISA 118, 엠세이퍼, 통신사');
  const [escalationStatus, setEscalationStatus] = useState<string>('종결');

  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [saveResult, setSaveResult] = useState<{ status: string; crm_record_id?: string; message: string } | null>(null);

  useEffect(() => {
    if (session && isOpen) {
      const a = session.latest_analysis;
      setCategory(a.counseling_category || '사이버피해 상담');
      setCallerIntent(a.core_intent || '민원 피해 사실 접수 및 대응 안내');
      setSummaryText(a.current_summary || '118 상담 접수 및 피해 예방 안내 완료.');
      setActionTaken(a.recommended_response_script ? `표준 안내 멘트 제공 및 주의사항 전달` : '기본 상담 완료');
      setRelatedAgency(a.responsible_agency || 'KISA 118');
      setEscalationStatus(a.escalation_needed === '즉시 이관 권고' ? '상급자 이관' : '종결');
      setSaveResult(null);
    }
  }, [session, isOpen]);

  if (!isOpen || !session) return null;

  const handleSaveToCRM = async () => {
    setIsSaving(true);
    setSaveResult(null);
    try {
      const res = await fetch('/api/crm/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          category,
          caller_intent: callerIntent,
          consultation_summary: summaryText,
          action_taken: actionTaken,
          related_agency: relatedAgency,
          escalation_status: escalationStatus
        })
      });

      const data = await res.json();
      setSaveResult(data);
      if (data.status === 'SUCCESS' || data.status === 'DUPLICATE') {
        onSaved();
      }
    } catch (e: any) {
      setSaveResult({ status: 'FAILED', message: `저장 실패: ${e.message}` });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDownloadJSON = () => {
    window.open(`/api/crm/export/${session.session_id}`, '_blank');
  };

  return (
    <div className="modal-backdrop">
      <div className="glass-panel" style={{ width: '92%', maxWidth: '720px', padding: '26px', maxHeight: '90vh', overflowY: 'auto' }}>
        
        {/* 모달 헤더 */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Database size={22} color="var(--accent-cyan)" />
            <div>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 800 }}>D. 상담 종료 및 CRM 저장</h2>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                세션 ID: <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>{session.session_id}</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* 안내문 */}
        <div style={{
          padding: '10px 14px',
          borderRadius: '8px',
          background: 'rgba(2, 132, 199, 0.1)',
          border: '1px solid rgba(0, 229, 255, 0.3)',
          color: '#E0F2FE',
          fontSize: '0.82rem',
          marginBottom: '18px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <ShieldCheck size={18} />
          <span>
            상담사가 AI 생성 요약을 최종 검토·수정한 후 Mock CRM에 안전하게 등록합니다. (개인정보는 마스킹 처리됨)
          </span>
        </div>

        {/* 폼 입력 영역 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '20px' }}>
          
          {/* 분류 및 처리결과 */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                최종 상담 유형
              </label>
              <input
                type="text"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  background: 'rgba(0, 0, 0, 0.3)',
                  border: '1px solid var(--border-subtle)',
                  color: '#FFFFFF',
                  fontSize: '0.88rem'
                }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                처리 상태
              </label>
              <select
                value={escalationStatus}
                onChange={(e) => setEscalationStatus(e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  background: '#111827',
                  border: '1px solid var(--border-subtle)',
                  color: '#FFFFFF',
                  fontSize: '0.88rem'
                }}
              >
                <option value="종결">종결 (상담 완료)</option>
                <option value="상급자 이관">상급자 이관</option>
                <option value="유관기관 이첩">유관기관 이첩 (경찰/금감원)</option>
              </select>
            </div>
          </div>

          {/* 민원인 요구사항 */}
          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              민원인 핵심 요구사항
            </label>
            <input
              type="text"
              value={callerIntent}
              onChange={(e) => setCallerIntent(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                background: 'rgba(0, 0, 0, 0.3)',
                border: '1px solid var(--border-subtle)',
                color: '#FFFFFF',
                fontSize: '0.88rem'
              }}
            />
          </div>

          {/* 상담 종합 요약 */}
          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              상담 종합 요약
            </label>
            <textarea
              rows={3}
              value={summaryText}
              onChange={(e) => setSummaryText(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                background: 'rgba(0, 0, 0, 0.3)',
                border: '1px solid var(--border-subtle)',
                color: '#FFFFFF',
                fontSize: '0.88rem',
                lineHeight: 1.5,
                resize: 'vertical'
              }}
            />
          </div>

          {/* 상담 조치 내역 */}
          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              상담사 조치 및 안내 사항
            </label>
            <textarea
              rows={2}
              value={actionTaken}
              onChange={(e) => setActionTaken(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                background: 'rgba(0, 0, 0, 0.3)',
                border: '1px solid var(--border-subtle)',
                color: '#FFFFFF',
                fontSize: '0.88rem',
                lineHeight: 1.5,
                resize: 'vertical'
              }}
            />
          </div>

          {/* 유관기관 */}
          <div>
            <label style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              안내 및 연계 유관기관
            </label>
            <input
              type="text"
              value={relatedAgency}
              onChange={(e) => setRelatedAgency(e.target.value)}
              style={{
                width: '100%',
                padding: '8px 12px',
                borderRadius: '6px',
                background: 'rgba(0, 0, 0, 0.3)',
                border: '1px solid var(--border-subtle)',
                color: '#FFFFFF',
                fontSize: '0.88rem'
              }}
            />
          </div>

        </div>

        {/* 결과 피드백 */}
        {saveResult && (
          <div style={{
            padding: '12px 16px',
            borderRadius: '8px',
            marginBottom: '16px',
            background: saveResult.status === 'SUCCESS' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(245, 158, 11, 0.15)',
            border: `1px solid ${saveResult.status === 'SUCCESS' ? 'var(--status-green)' : 'var(--status-yellow)'}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem' }}>
              <CheckCircle size={16} color={saveResult.status === 'SUCCESS' ? 'var(--status-green)' : 'var(--status-yellow)'} />
              <span>{saveResult.message}</span>
              {saveResult.crm_record_id && (
                <strong style={{ color: 'var(--accent-cyan)' }}>[{saveResult.crm_record_id}]</strong>
              )}
            </div>

            <button
              onClick={handleDownloadJSON}
              className="btn-secondary"
              style={{ padding: '4px 10px', fontSize: '0.75rem' }}
            >
              <Download size={13} /> JSON 다운로드
            </button>
          </div>
        )}

        {/* 하단 버튼 */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
          <button className="btn-secondary" onClick={onClose}>
            닫기
          </button>
          <button
            className="btn-primary"
            onClick={handleSaveToCRM}
            disabled={isSaving}
          >
            <CheckCircle size={16} />
            {isSaving ? '저장 처리중...' : '확인 및 CRM 등록'}
          </button>
        </div>

      </div>
    </div>
  );
};
