"""
118 팔배개 - Windows 오디오 WebSocket 클라이언트 모듈
캡처된 오디오 스트림 및 VU 레벨을 STT 서버로 전송
"""

import asyncio
import json
import logging
import base64
import time
from typing import Optional, Dict, Any
import numpy as np
import websockets

from audio_agent.capture import AudioCaptureStream

logger = logging.getLogger("AudioWsClient")


class AudioWebSocketClient:
    """
    Windows 호스트에서 동작하며 오디오 데이터를 STT 서버 WebSocket 엔드포인트로 중계
    """

    def __init__(
        self,
        server_ws_url: str = "ws://127.0.0.1:8000/ws/audio",
        device_index: Optional[int] = None,
        target_sample_rate: int = 16000,
        energy_threshold: float = 0.008,
        silence_timeout_ms: int = 800
    ):
        self.server_ws_url = server_ws_url
        self.device_index = device_index
        self.target_sample_rate = target_sample_rate
        self.energy_threshold = energy_threshold
        self.silence_timeout_ms = silence_timeout_ms

        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.is_running = False
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.capture_stream: Optional[AudioCaptureStream] = None

        self._last_vu_send_time = 0.0
        self._vu_send_interval = 0.08  # 80ms마다 VU 업데이트 (약 12fps로 부하 최소화)

    def _on_vu_update(self, level: int):
        """캡처 스레드에서 호출되는 VU 레벨 콜백"""
        now = time.time()
        if now - self._last_vu_send_time >= self._vu_send_interval:
            self._last_vu_send_time = now
            if self.loop and self.ws and not self.ws.closed:
                payload = json.dumps({
                    "type": "vu_meter",
                    "level": level,
                    "timestamp": time.time()
                })
                asyncio.run_coroutine_threadsafe(self._safe_send(payload), self.loop)

    def _on_speech_segment(self, segment: np.ndarray, is_final: bool):
        """캡처 스레드에서 호출되는 음성 세그먼트 전송 콜백"""
        if self.loop and self.ws and not self.ws.closed:
            # float32 -> int16 PCM 직렬화
            int16_pcm = (np.clip(segment, -1.0, 1.0) * 32767).astype(np.int16).tobytes()
            b64_pcm = base64.b64encode(int16_pcm).decode("ascii")

            payload = json.dumps({
                "type": "audio_segment",
                "is_final": is_final,
                "sample_rate": self.target_sample_rate,
                "duration_s": round(len(segment) / self.target_sample_rate, 3),
                "timestamp": time.time(),
                "pcm_base64": b64_pcm
            })
            asyncio.run_coroutine_threadsafe(self._safe_send(payload), self.loop)

    def _on_status_change(self, status: str, details: Dict[str, Any]):
        """장치 상태 변화 콜백"""
        logger.info(f"Audio Agent Status: {status} - {details}")
        if self.loop and self.ws and not self.ws.closed:
            payload = json.dumps({
                "type": "agent_status",
                "status": status,
                "details": details,
                "timestamp": time.time()
            })
            asyncio.run_coroutine_threadsafe(self._safe_send(payload), self.loop)

    async def _safe_send(self, message: str):
        """WebSocket 전송 안전 래퍼"""
        try:
            if self.ws and not self.ws.closed:
                await self.ws.send(message)
        except Exception as e:
            logger.debug(f"WS 전송 실패: {e}")

    async def run(self):
        """클라이언트 메인 루프 (자동 재연결 지원)"""
        self.is_running = True
        self.loop = asyncio.get_running_loop()

        self.capture_stream = AudioCaptureStream(
            device_index=self.device_index,
            target_sample_rate=self.target_sample_rate,
            energy_threshold=self.energy_threshold,
            silence_timeout_ms=self.silence_timeout_ms,
            on_vu_update=self._on_vu_update,
            on_speech_segment=self._on_speech_segment,
            on_status_change=self._on_status_change
        )

        logger.info(f"STT 서버 연결 대기 중: {self.server_ws_url}")

        while self.is_running:
            try:
                async with websockets.connect(self.server_ws_url) as ws:
                    self.ws = ws
                    logger.info("STT 서버와 WebSocket 연결 성공! 오디오 캡처를 시작합니다.")
                    self.capture_stream.start()

                    # 서버로부터의 제어 명령 수신 (장치 변경, 정지 등)
                    async for msg_str in ws:
                        try:
                            msg = json.loads(msg_str)
                            cmd = msg.get("command")
                            if cmd == "SET_DEVICE":
                                new_dev_idx = msg.get("device_index")
                                logger.info(f"오디오 장치 변경 명령: {new_dev_idx}")
                                self.capture_stream.stop()
                                self.capture_stream.device_index = new_dev_idx
                                self.capture_stream.start()
                            elif cmd == "STOP":
                                self.capture_stream.stop()
                            elif cmd == "START":
                                self.capture_stream.start()
                        except Exception as e:
                            logger.error(f"메시지 처리 오류: {e}")

            except (websockets.ConnectionClosed, ConnectionRefusedError, OSError) as e:
                logger.warning(f"서버 연결 끊김 또는 연결 불가 ({e}). 3초 후 재연결 시도...")
                if self.capture_stream:
                    self.capture_stream.stop()
                await asyncio.sleep(3.0)
            except Exception as e:
                logger.error(f"예상치 못한 예외: {e}")
                await asyncio.sleep(3.0)

    def stop(self):
        """클라이언트 정지"""
        self.is_running = False
        if self.capture_stream:
            self.capture_stream.stop()
