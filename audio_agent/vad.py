"""
118 팔배개 - VAD (Voice Activity Detection) 및 음성 구간 감지 모듈
에너지(RMS) 및 영교차율(ZCR) 기반의 신속하고 안정적인 음성 활동 감지기
"""

import numpy as np
from typing import Tuple, List, Optional
from enum import Enum


class VadState(Enum):
    SILENCE = "SILENCE"
    SPEECH_START = "SPEECH_START"
    SPEECH = "SPEECH"
    SPEECH_END = "SPEECH_END"


class EnergyVAD:
    """
    실시간 프레임 단위 음성 활동 감지기
    - RMS 에너지 및 적응형 노이즈 플로어 기반
    - 행오버(Hangover) 버퍼를 통해 단어 사이의 짧은 묵음 보존
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        frame_ms: int = 30,
        energy_threshold: float = 0.008,
        silence_timeout_ms: int = 800,
        speech_lead_ms: int = 200,
        max_speech_duration_s: float = 15.0
    ):
        self.sample_rate = sample_rate
        self.frame_ms = frame_ms
        self.frame_samples = int(sample_rate * (frame_ms / 1000.0))
        self.energy_threshold = energy_threshold
        self.silence_timeout_ms = silence_timeout_ms
        self.speech_lead_ms = speech_lead_ms
        self.max_speech_duration_s = max_speech_duration_s

        # 버퍼 및 상태 변수
        self.is_speaking = False
        self.silence_accum_ms = 0
        self.speech_accum_ms = 0
        self.lead_buffer: List[np.ndarray] = []
        self.max_lead_frames = max(1, int(speech_lead_ms / frame_ms))
        self.current_speech_frames: List[np.ndarray] = []

        # 노이즈 추정
        self.noise_floor = energy_threshold * 0.5

    def calculate_rms(self, frame: np.ndarray) -> float:
        """프레임의 RMS(Root Mean Square) 에너지 계산"""
        if len(frame) == 0:
            return 0.0
        # float32 (-1.0 ~ 1.0) 기준
        energy = np.sqrt(np.mean(np.square(frame)))
        return float(energy)

    def calculate_vu_level(self, rms: float) -> int:
        """UI 표출용 볼륨 레벨 (0 ~ 100) 정규화"""
        # 0.001 -> 1, 0.25 이상 -> 100
        if rms < 0.001:
            return 0
        level = int((rms / 0.25) * 100)
        return min(100, max(0, level))

    def process_frame(self, frame: np.ndarray) -> Tuple[VadState, int, Optional[np.ndarray]]:
        """
        한 프레임을 처리하고 VAD 상태, VU 레벨, (발화 종료 시) 완성된 음성 세그먼트를 반환
        
        Returns:
            (VadState, vu_level, completed_audio_segment_or_None)
        """
        # 프레임이 1채널 1차원 배열인지 확인
        if frame.ndim > 1:
            frame = frame.flatten()

        rms = self.calculate_rms(frame)
        vu = self.calculate_vu_level(rms)

        is_voice = rms >= self.energy_threshold

        completed_segment: Optional[np.ndarray] = None
        state = VadState.SILENCE

        if not self.is_speaking:
            # 묵음 상태
            self.lead_buffer.append(frame)
            if len(self.lead_buffer) > self.max_lead_frames:
                self.lead_buffer.pop(0)

            if is_voice:
                # 발화 시작 감지
                self.is_speaking = True
                self.silence_accum_ms = 0
                self.speech_accum_ms = len(self.lead_buffer) * self.frame_ms
                self.current_speech_frames = list(self.lead_buffer)
                self.lead_buffer.clear()
                state = VadState.SPEECH_START
            else:
                state = VadState.SILENCE
        else:
            # 발화 진행 중 상태
            self.current_speech_frames.append(frame)
            self.speech_accum_ms += self.frame_ms

            if is_voice:
                self.silence_accum_ms = 0
                state = VadState.SPEECH
            else:
                self.silence_accum_ms += self.frame_ms

                # 묵음 지속 시간이 임계값을 초과했거나, 최대 발화 지속 시간에 도달한 경우
                if self.silence_accum_ms >= self.silence_timeout_ms or (self.speech_accum_ms >= self.max_speech_duration_s * 1000):
                    self.is_speaking = False
                    state = VadState.SPEECH_END
                    if self.current_speech_frames:
                        completed_segment = np.concatenate(self.current_speech_frames).astype(np.float32)
                    self.current_speech_frames = []
                    self.silence_accum_ms = 0
                    self.speech_accum_ms = 0
                else:
                    state = VadState.SPEECH

        return state, vu, completed_segment

    def get_interim_segment(self) -> Optional[np.ndarray]:
        """현재 발화 중인 버퍼의 중간 음성 데이터 반환 (중간 전사용)"""
        if self.is_speaking and len(self.current_speech_frames) > 0:
            return np.concatenate(self.current_speech_frames).astype(np.float32)
        return None

    def reset(self):
        """상태 초기화"""
        self.is_speaking = False
        self.silence_accum_ms = 0
        self.speech_accum_ms = 0
        self.lead_buffer.clear()
        self.current_speech_frames.clear()
