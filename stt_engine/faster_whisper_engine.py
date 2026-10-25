"""
118 팔배개 - Faster-Whisper 기반 실시간 STT 엔진 구현체
NVIDIA GPU(RTX 5080 등) CUDA 가속 및 CPU 자동 폴백 지원
"""

import logging
import time
from typing import Dict, Any, Optional
import numpy as np

from stt_engine.base import STTEngineBase, STTResult
from stt_engine.terminology import SecurityTerminologyProcessor
from stt_engine.pii_masker import PIIMasker

logger = logging.getLogger("FasterWhisperEngine")


class FasterWhisperEngine(STTEngineBase):
    """Faster-Whisper (CTranslate2) 기반 고성능 STT 엔진"""

    def __init__(
        self,
        model_size: str = "base",
        device: str = "auto",
        compute_type: str = "default",
        language: str = "ko",
        mask_pii: bool = True,
        apply_security_dict: bool = True
    ):
        self.model_size = model_size
        self.requested_device = device
        self.requested_compute_type = compute_type
        self.language = language
        self.mask_pii = mask_pii
        self.apply_security_dict = apply_security_dict

        self.actual_device = "cpu"
        self.actual_compute_type = "int8"
        self.model = None
        self._is_ready = False

        self.load_model(model_size, device, compute_type)

    def load_model(self, model_size: str = "base", device: str = "auto", compute_type: str = "default"):
        """Faster-Whisper 모델 로드 (CUDA 우선 시도 후 CPU 폴백)"""
        from faster_whisper import WhisperModel
        import ctranslate2

        target_device = device
        if target_device == "auto":
            # CUDA 사용 가능 여부 확인
            cuda_count = ctranslate2.get_cuda_device_count()
            target_device = "cuda" if cuda_count > 0 else "cpu"

        target_compute = compute_type
        if target_compute == "default":
            target_compute = "float16" if target_device == "cuda" else "int8"

        logger.info(f"Faster-Whisper 모델 로드 시도: {model_size} (디바이스: {target_device}, 연산: {target_compute})")

        try:
            self.model = WhisperModel(
                model_size_or_path=model_size,
                device=target_device,
                compute_type=target_compute,
                download_root="c:/118-p/data/whisper_models"
            )
            self.actual_device = target_device
            self.actual_compute_type = target_compute
            self._is_ready = True
            logger.info(f"Faster-Whisper 모델 로드 성공: {model_size} ({target_device})")

        except Exception as e:
            logger.warning(f"CUDA 모드로 모델 로드 실패 ({e}). CPU 모드로 폴백 시도...")
            try:
                self.model = WhisperModel(
                    model_size_or_path=model_size,
                    device="cpu",
                    compute_type="int8",
                    download_root="c:/118-p/data/whisper_models"
                )
                self.actual_device = "cpu"
                self.actual_compute_type = "int8"
                self._is_ready = True
                logger.info(f"Faster-Whisper CPU 폴백 성공: {model_size}")
            except Exception as e2:
                logger.error(f"Faster-Whisper 모델 로드 최종 실패: {e2}")
                self._is_ready = False
                raise RuntimeError(f"STT 모델 로드 실패: {e2}")

    def transcribe_audio(
        self,
        audio_float32: np.ndarray,
        sample_rate: int = 16000,
        is_final: bool = True,
        speaker: str = "혼합/식별중"
    ) -> STTResult:
        """오디오 샘플 전사 및 후처리"""
        if not self._is_ready or self.model is None:
            return STTResult(text="[STT 엔진 미준비]", is_final=is_final, speaker=speaker)

        start_ts = time.time()
        initial_prompt = (
            SecurityTerminologyProcessor.get_initial_prompt()
            if self.apply_security_dict
            else None
        )

        try:
            # 16kHz float32 오디오를 Faster-Whisper로 추론
            segments, info = self.model.transcribe(
                audio_float32,
                language=self.language,
                beam_size=3 if is_final else 1,
                best_of=3 if is_final else 1,
                temperature=0.0,
                initial_prompt=initial_prompt,
                vad_filter=False,  # 자체 VAD를 통과한 오디오이므로 False
                condition_on_previous_text=False
            )

            raw_texts = []
            confidences = []
            first_start = 0.0
            last_end = 0.0

            for i, seg in enumerate(segments):
                raw_texts.append(seg.text)
                if i == 0:
                    first_start = seg.start
                last_end = seg.end
                # logprob을 신뢰도 점수(0~1)로 근사
                prob = float(np.exp(seg.avg_logprob)) if seg.avg_logprob is not None else 0.85
                confidences.append(min(1.0, max(0.0, prob)))

            raw_combined = " ".join(raw_texts).strip()

            # 보안 전문용어 보정
            processed_text = raw_combined
            if self.apply_security_dict:
                processed_text = SecurityTerminologyProcessor.correct_text(processed_text)

            # 민감정보(PII) 마스킹
            if self.mask_pii:
                processed_text = PIIMasker.mask_text(processed_text)

            avg_conf = float(np.mean(confidences)) if confidences else (0.85 if processed_text else 0.0)

            return STTResult(
                text=processed_text,
                raw_text=raw_combined,
                is_final=is_final,
                start_time=round(first_start, 2),
                end_time=round(last_end, 2),
                confidence=round(avg_conf, 2),
                speaker=speaker,
                language=self.language
            )

        except Exception as e:
            logger.error(f"Faster-Whisper 전사 중 오류: {e}")
            return STTResult(
                text=f"[전사 오류: {str(e)}]",
                raw_text="",
                is_final=is_final,
                confidence=0.0,
                speaker=speaker
            )

    def get_engine_info(self) -> Dict[str, Any]:
        """엔진 메타데이터 반환"""
        return {
            "engine": "faster-whisper",
            "model_size": self.model_size,
            "device": self.actual_device,
            "compute_type": self.actual_compute_type,
            "language": self.language,
            "mask_pii": self.mask_pii,
            "security_dict": self.apply_security_dict,
            "is_ready": self._is_ready
        }
