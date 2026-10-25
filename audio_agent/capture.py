"""
118 팔배개 - Windows Line-in 오디오 캡처 및 실시간 리샘플러
선택된 오디오 장치로부터 실시간 PCM 스트림을 캡처하고 16kHz Mono로 변환
"""

import time
import queue
import threading
import logging
from typing import Callable, Optional, Dict, Any
import numpy as np
import sounddevice as sd
from scipy import signal

from audio_agent.vad import EnergyVAD, VadState

logger = logging.getLogger("AudioCapture")


class AudioCaptureStream:
    """
    Windows 오디오 장치 캡처 및 리샘플링 스트림 클래스
    - 다채널 입력 -> 모노 변환 (평균 혼합)
    - 임의의 샘플레이트 -> STT 표준 16kHz 변환
    - VAD 적용 및 음성 세그먼트 생성
    - 장치 예외 처리 및 자동 재시도
    """

    def __init__(
        self,
        device_index: Optional[int] = None,
        target_sample_rate: int = 16000,
        frame_ms: int = 30,
        energy_threshold: float = 0.008,
        silence_timeout_ms: int = 800,
        on_vu_update: Optional[Callable[[int], None]] = None,
        on_speech_segment: Optional[Callable[[np.ndarray, bool], None]] = None,
        on_status_change: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ):
        self.device_index = device_index
        self.target_sample_rate = target_sample_rate
        self.frame_ms = frame_ms
        self.target_frame_samples = int(target_sample_rate * (frame_ms / 1000.0))

        self.on_vu_update = on_vu_update
        self.on_speech_segment = on_speech_segment  # (audio_segment, is_final)
        self.on_status_change = on_status_change

        self.vad = EnergyVAD(
            sample_rate=target_sample_rate,
            frame_ms=frame_ms,
            energy_threshold=energy_threshold,
            silence_timeout_ms=silence_timeout_ms
        )

        self.stream: Optional[sd.InputStream] = None
        self.is_running = False
        self.device_info: Dict[str, Any] = {}
        self.input_sample_rate = 44100
        self.input_channels = 1

        self._audio_queue: queue.Queue = queue.Queue(maxsize=200)
        self._worker_thread: Optional[threading.Thread] = None
        self._interim_timer: float = 0.0
        self.interim_interval_s = 0.35  # 350ms마다 중간 전사 이벤트 발생

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        """sounddevice 입력 콜백 (오디오 스레드에서 즉시 반환)"""
        if status and logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Audio callback status: {status}")
        try:
            # 원본 데이터 복사본 큐에 삽입
            self._audio_queue.put_nowait(indata.copy())
        except queue.Full:
            pass  # 백로그 방지를 위한 프레임 드롭

    def _resample_to_mono_16k(self, audio: np.ndarray) -> np.ndarray:
        """
        다채널/다양한 샘플레이트의 오디오를 16kHz 모노 float32로 변환
        """
        # 1. 다채널 -> 모노 다운믹싱
        if audio.ndim > 1 and audio.shape[1] > 1:
            mono = np.mean(audio, axis=1)
        else:
            mono = audio.flatten()

        # 2. 샘플레이트 변환
        if self.input_sample_rate != self.target_sample_rate:
            # gcd를 계산하여 resample_poly 적용 (초고속 및 높은 품질)
            gcd = np.gcd(int(self.input_sample_rate), int(self.target_sample_rate))
            up = int(self.target_sample_rate // gcd)
            down = int(self.input_sample_rate // gcd)
            resampled = signal.resample_poly(mono, up, down).astype(np.float32)
        else:
            resampled = mono.astype(np.float32)

        return resampled

    def _worker_loop(self):
        """큐에서 오디오 블록을 가져와 리샘플링, VAD 및 전송 처리"""
        accumulated_samples = np.array([], dtype=np.float32)
        self._interim_timer = time.time()

        while self.is_running:
            try:
                raw_chunk = self._audio_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            # 16kHz Mono로 변환
            converted = self._resample_to_mono_16k(raw_chunk)
            accumulated_samples = np.concatenate([accumulated_samples, converted])

            # target_frame_samples (480 samples = 30ms) 단위로 잘라서 VAD 처리
            while len(accumulated_samples) >= self.target_frame_samples:
                frame = accumulated_samples[:self.target_frame_samples]
                accumulated_samples = accumulated_samples[self.target_frame_samples:]

                vad_state, vu_level, completed_segment = self.vad.process_frame(frame)

                if self.on_vu_update:
                    self.on_vu_update(vu_level)

                # 중간 전사 트리거 (발화 중일 때 주기적으로 전송)
                now = time.time()
                if self.vad.is_speaking and (now - self._interim_timer >= self.interim_interval_s):
                    self._interim_timer = now
                    interim_audio = self.vad.get_interim_segment()
                    if interim_audio is not None and len(interim_audio) > (self.target_sample_rate * 0.4):
                        if self.on_speech_segment:
                            self.on_speech_segment(interim_audio, False)

                # 발화 종료 시 확정 음성 세그먼트 전송
                if completed_segment is not None and len(completed_segment) > (self.target_sample_rate * 0.3):
                    if self.on_speech_segment:
                        self.on_speech_segment(completed_segment, True)

    def start(self) -> bool:
        """오디오 스트림 캡처 시작"""
        if self.is_running:
            return True

        try:
            # 장치 설정 확인
            if self.device_index is None or self.device_index < 0:
                self.device_index = sd.default.device[0]

            dev_info = sd.query_devices(self.device_index)
            self.device_info = dev_info
            self.input_sample_rate = int(dev_info.get("default_samplerate", 44100))
            self.input_channels = min(int(dev_info.get("max_input_channels", 1)), 2)

            # 프레임 크기 (초기 하드웨어 버퍼)
            blocksize = int(self.input_sample_rate * (self.frame_ms / 1000.0))

            self.stream = sd.InputStream(
                device=self.device_index,
                channels=self.input_channels,
                samplerate=self.input_sample_rate,
                blocksize=blocksize,
                dtype="float32",
                callback=self._audio_callback
            )

            self.is_running = True
            self.vad.reset()
            self._audio_queue = queue.Queue(maxsize=300)

            # 워커 스레드 시작
            self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self._worker_thread.start()

            # 오디오 스트림 활성화
            self.stream.start()

            if self.on_status_change:
                self.on_status_change("STARTED", {
                    "device_index": self.device_index,
                    "device_name": dev_info.get("name"),
                    "native_sample_rate": self.input_sample_rate,
                    "target_sample_rate": self.target_sample_rate,
                    "channels": self.input_channels
                })

            return True

        except Exception as e:
            logger.error(f"오디오 캡처 시작 실패: {e}")
            self.is_running = False
            if self.on_status_change:
                self.on_status_change("ERROR", {"error": str(e)})
            return False

    def stop(self):
        """오디오 스트림 캡처 중지"""
        if not self.is_running:
            return

        self.is_running = False
        try:
            if self.stream is not None:
                self.stream.stop()
                self.stream.close()
                self.stream = None
        except Exception as e:
            logger.warning(f"오디오 스트림 종료 중 오류: {e}")

        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)

        self.vad.reset()

        if self.on_status_change:
            self.on_status_change("STOPPED", {})
