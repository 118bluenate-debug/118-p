"""
118 팔배개 - STT 엔진 기본 인터페이스 (추상 어댑터)
Faster-Whisper, Whisper-Flash 등 다양한 엔진으로 교체 가능한 구조 정의
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import numpy as np
from pydantic import BaseModel, Field


class STTResult(BaseModel):
    """STT 전사 결과 모델"""
    text: str = Field(description="전사된 텍스트 (보정 및 마스킹 적용)")
    raw_text: str = Field(default="", description="원문 텍스트 (보정 전)")
    is_final: bool = Field(default=False, description="확정 전사 여부 (True: 확정, False: 중간)")
    start_time: float = Field(default=0.0, description="발화 시작 시간 (초)")
    end_time: float = Field(default=0.0, description="발화 종료 시간 (초)")
    confidence: float = Field(default=0.0, description="신뢰도 점수 (0.0 ~ 1.0)")
    speaker: str = Field(default="혼합/식별중", description="화자 (상담사 | 민원인 | 혼합/식별중)")
    language: str = Field(default="ko", description="인식 언어")


class STTEngineBase(ABC):
    """STT 엔진 추상 베이스 클래스"""

    @abstractmethod
    def load_model(self, model_size: str = "base", device: str = "auto", compute_type: str = "default"):
        """STT 모델 로드 및 초기화"""
        pass

    @abstractmethod
    def transcribe_audio(
        self,
        audio_float32: np.ndarray,
        sample_rate: int = 16000,
        is_final: bool = True,
        speaker: str = "혼합/식별중"
    ) -> STTResult:
        """
        오디오 샘플(16kHz Mono float32)을 텍스트로 변환
        
        Args:
            audio_float32: -1.0 ~ 1.0 범위의 float32 numpy 1차원 배열
            sample_rate: 오디오 샘플레이트 (기본 16000)
            is_final: 확정 전사 여부
            speaker: 화자 정보
        
        Returns:
            STTResult 객체
        """
        pass

    @abstractmethod
    def get_engine_info(self) -> Dict[str, Any]:
        """엔진 명칭, 사용 장치(GPU/CPU), 모델 크기 등 메타데이터 반환"""
        pass
