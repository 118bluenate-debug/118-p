"""
118 팔배개 - STT 엔진 팩토리 모듈
설정값(환경변수)에 따라 적절한 STT 엔진 어댑터 인스턴스 생성
"""

import os
from typing import Optional
from stt_engine.base import STTEngineBase
from stt_engine.faster_whisper_engine import FasterWhisperEngine
from stt_engine.mock_engine import MockSTTEngine


class STTEngineFactory:
    """STT 엔진 생성 팩토리"""

    @classmethod
    def create_engine(
        cls,
        engine_type: Optional[str] = None,
        model_size: Optional[str] = None,
        device: Optional[str] = None,
        compute_type: Optional[str] = None,
        mask_pii: bool = True,
        apply_security_dict: bool = True
    ) -> STTEngineBase:
        engine_type = (engine_type or os.getenv("STT_ENGINE", "faster-whisper")).lower()
        model_size = model_size or os.getenv("STT_MODEL_SIZE", "base")
        device = device or os.getenv("STT_DEVICE", "auto")
        compute_type = compute_type or os.getenv("STT_COMPUTE_TYPE", "default")

        if engine_type == "faster-whisper":
            return FasterWhisperEngine(
                model_size=model_size,
                device=device,
                compute_type=compute_type,
                mask_pii=mask_pii,
                apply_security_dict=apply_security_dict
            )
        elif engine_type in ("mock", "test"):
            return MockSTTEngine(model_size=model_size)
        else:
            raise ValueError(f"지원하지 않는 STT 엔진 타입입니다: {engine_type}")
