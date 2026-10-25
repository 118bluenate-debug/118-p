"""
118 팔배개 - 테스트 및 CI/CD용 Mock STT 엔진
GPU나 가중치 다운로드 없이 단위/통합 테스트를 즉시 수행할 수 있는 어댑터
"""

import time
import random
from typing import Dict, Any, List
import numpy as np

from stt_engine.base import STTEngineBase, STTResult
from stt_engine.terminology import SecurityTerminologyProcessor
from stt_engine.pii_masker import PIIMasker


class MockSTTEngine(STTEngineBase):
    """118 상담 도메인 모의 STT 엔진"""

    SAMPLE_DIALOGS: List[str] = [
        "모바일 청첩장 문자 링크를 눌렀는데 악성 apk가 설치된 것 같아요.",
        "서울중앙지검 검사라고 하면서 010-1234-5678 번호로 전화가 와서 대포통장 사건에 연루되었다고 합니다.",
        "팀뷰어로 원격제어를 요청해서 인증번호를 알려줬는데 계좌에서 돈이 빠져나갔습니다.",
        "제 주민번호 900101-1234567가 도용되어 알뜰폰이 개통되었다는 문자를 받았습니다.",
        "스미싱 문자인 것 같은데 한국인터넷진흥원 보호나라에서 확인 가능한가요?",
        "카드사에서 1234-5678-9876-5432 카드로 결제되었다고 문자가 왔는데 제가 결제한 적이 없습니다.",
        "사이버경찰청 182나 금융감독원 1332로 신고하는 방법을 안내해 주실 수 있나요?"
    ]

    def __init__(self, model_size: str = "mock", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = model_size
        self.device = "mock"
        self._counter = 0

    def load_model(self, model_size: str = "mock", device: str = "cpu", compute_type: str = "int8"):
        pass

    def transcribe_audio(
        self,
        audio_float32: np.ndarray,
        sample_rate: int = 16000,
        is_final: bool = True,
        speaker: str = "민원인"
    ) -> STTResult:
        text = self.SAMPLE_DIALOGS[self._counter % len(self.SAMPLE_DIALOGS)]
        self._counter += 1

        duration = len(audio_float32) / float(sample_rate) if len(audio_float32) > 0 else 2.5
        corrected = SecurityTerminologyProcessor.correct_text(text)
        masked = PIIMasker.mask_text(corrected)

        return STTResult(
            text=masked,
            raw_text=text,
            is_final=is_final,
            start_time=0.0,
            end_time=round(duration, 2),
            confidence=0.96,
            speaker=speaker,
            language="ko"
        )

    def get_engine_info(self) -> Dict[str, Any]:
        return {
            "engine": "mock-whisper",
            "model_size": "mock",
            "device": "cpu",
            "is_ready": True
        }
