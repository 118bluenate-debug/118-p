"""
118 팔배개 - 서버 통합 환경설정 모듈
"""

import os
from typing import Optional


class ServerSettings:
    """118 팔배개 서버 설정"""

    def __init__(self):
        # 서버 바인딩
        self.server_host: str = os.getenv("SERVER_HOST", "0.0.0.0")
        self.server_port: int = int(os.getenv("SERVER_PORT", "8000"))

        # STT 엔진 설정
        self.stt_engine: str = os.getenv("STT_ENGINE", "faster-whisper")
        self.stt_model_size: str = os.getenv("STT_MODEL_SIZE", "base")
        self.stt_device: str = os.getenv("STT_DEVICE", "auto")
        self.stt_compute_type: str = os.getenv("STT_COMPUTE_TYPE", "default")
        self.stt_language: str = os.getenv("STT_LANGUAGE", "ko")
        self.mask_pii_enabled: bool = os.getenv("MASK_PII_ENABLED", "true").lower() == "true"
        self.security_dictionary_enabled: bool = os.getenv("SECURITY_DICTIONARY_ENABLED", "true").lower() == "true"

        # 로컬 LLM 설정 (Ollama)
        self.ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        self.ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen3:4b")
        self.ollama_timeout_seconds: float = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "45.0"))

        # CRM 설정
        self.crm_adapter: str = os.getenv("CRM_ADAPTER", "mock")
        self.crm_data_dir: str = os.getenv("CRM_DATA_DIR", "c:/118-p/data/crm_records")

        # 오디오 설정
        self.audio_target_sample_rate: int = int(os.getenv("AUDIO_TARGET_SAMPLE_RATE", "16000"))
        self.vad_energy_threshold: float = float(os.getenv("VAD_ENERGY_THRESHOLD", "0.008"))
        self.vad_silence_timeout_ms: int = int(os.getenv("VAD_SILENCE_TIMEOUT_MS", "800"))


settings = ServerSettings()
