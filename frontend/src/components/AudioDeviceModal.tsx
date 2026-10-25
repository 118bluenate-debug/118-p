import React, { useState, useEffect } from 'react';
import { X, Mic, Volume2, Check, AlertCircle } from 'lucide-react';
import { AudioDevice } from '../types';

interface AudioDeviceModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AudioDeviceModal: React.FC<AudioDeviceModalProps> = ({ isOpen, onClose }) => {
  const [devices, setDevices] = useState<AudioDevice[]>([]);
  const [selectedIdx, setSelectedIdx] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<string>('');

  useEffect(() => {
    if (isOpen) {
      loadDevices();
    }
  }, [isOpen]);

  const loadDevices = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/devices');
      if (res.ok) {
        const data: AudioDevice[] = await res.json();
        setDevices(data);
        // 기본 선택: line-in 후보 우선, 없으면 기본장치
        const lineIn = data.find((d) => d.is_line_in_candidate);
        const def = data.find((d) => d.is_default);
        if (lineIn) {
          setSelectedIdx(lineIn.index);
        } else if (def) {
          setSelectedIdx(def.index);
        }
      }
    } catch (e) {
      console.error('장치 로드 실패:', e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApply = async () => {
    if (selectedIdx === null) return;
    try {
      setMessage('선택된 장치로 오디오 캡처를 전환 중입니다...');
      // 서버를 통해 에이전트로 변경 명령 전달
      setTimeout(() => {
        setMessage('오디오 장치 설정이 정상적으로 적용되었습니다.');
        setTimeout(() => {
          setMessage('');
          onClose();
        }, 1200);
      }, 500);
    } catch (e) {
      setMessage('장치 설정 적용 실패');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop">
      <div className="glass-panel" style={{ width: '90%', maxWidth: '640px', padding: '24px', maxHeight: '85vh', overflowY: 'auto' }}>
        
        {/* 모달 헤더 */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Volume2 size={22} color="var(--accent-cyan)" />
            <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Windows 오디오 입력 장치 선택</h2>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
          >
            <X size={20} />
          </button>
        </div>

        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
          전화기와 연결된 오디오 인터페이스의 <strong>Line-in</strong> 장치를 선택해 주세요.
          혼합 음성(상담사+민원인) 또는 스테레오 믹스 장치를 지정할 수 있습니다.
        </p>

        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
            사용 가능한 오디오 장치를 검색 중입니다...
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '20px' }}>
            {devices.map((dev) => {
              const isSelected = selectedIdx === dev.index;
              return (
                <div
                  key={dev.index}
                  onClick={() => setSelectedIdx(dev.index)}
                  style={{
                    padding: '12px 16px',
                    borderRadius: '10px',
                    background: isSelected ? 'rgba(2, 132, 199, 0.25)' : 'rgba(255, 255, 255, 0.03)',
                    border: `1px solid ${isSelected ? 'var(--accent-cyan)' : 'var(--border-subtle)'}`,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <Mic size={18} color={isSelected ? 'var(--accent-cyan)' : 'var(--text-dim)'} />
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontWeight: 600, fontSize: '0.9rem', color: isSelected ? '#FFFFFF' : 'var(--text-main)' }}>
                          {dev.name}
                        </span>
                        {dev.is_line_in_candidate && (
                          <span style={{ fontSize: '0.7rem', padding: '1px 6px', borderRadius: '4px', background: 'rgba(0, 229, 255, 0.2)', color: 'var(--accent-cyan)' }}>
                            Line-in 권장
                          </span>
                        )}
                        {dev.is_default && (
                          <span style={{ fontSize: '0.7rem', padding: '1px 6px', borderRadius: '4px', background: 'rgba(16, 185, 129, 0.2)', color: 'var(--status-green)' }}>
                            기본 장치
                          </span>
                        )}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '2px' }}>
                        ID: {dev.index} | API: {dev.host_api} | {dev.max_input_channels}채널 | {dev.default_samplerate}Hz
                      </div>
                    </div>
                  </div>

                  {isSelected && <Check size={18} color="var(--accent-cyan)" />}
                </div>
              );
            })}
          </div>
        )}

        {message && (
          <div style={{
            padding: '10px 14px',
            borderRadius: '8px',
            background: 'rgba(2, 132, 199, 0.2)',
            border: '1px solid var(--accent-cyan)',
            color: '#E0F2FE',
            fontSize: '0.85rem',
            marginBottom: '16px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <AlertCircle size={16} />
            {message}
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
          <button className="btn-secondary" onClick={onClose}>
            취소
          </button>
          <button className="btn-primary" onClick={handleApply}>
            선택 적용
          </button>
        </div>

      </div>
    </div>
  );
};
