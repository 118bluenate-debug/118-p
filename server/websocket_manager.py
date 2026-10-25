"""
118 팔배개 - WebSocket 브로드캐스트 및 실시간 오디오/STT/AI 연동 관리자
Windows 오디오 에이전트와 React 상담사 웹 UI 사이의 실시간 브릿지 역할
"""

import json
import base64
import logging
import asyncio
from typing import Set, Optional, Dict, Any
import numpy as np
from fastapi import WebSocket

from server.session_manager import SessionManager
from stt_engine.base import STTEngineBase
from llm_analysis.ollama_client import OllamaClient

logger = logging.getLogger("WebSocketManager")


class WebSocketManager:
    """통합 웹소켓 허브"""

    def __init__(self):
        # 연결된 상담사 UI 웹소켓 집합
        self.counselor_clients: Set[WebSocket] = set()
        # Windows 오디오 에이전트 소켓
        self.audio_agent_ws: Optional[WebSocket] = None
        self._analysis_task: Optional[asyncio.Task] = None

    async def connect_counselor(self, ws: WebSocket, session_mgr: SessionManager):
        """상담사 UI 접속 처리 및 초기 스냅샷 전송"""
        await ws.accept()
        self.counselor_clients.add(ws)
        # 초기 세션 상태 동기화
        await ws.send_text(json.dumps({
            "type": "session_init",
            "snapshot": session_mgr.get_session_snapshot()
        }))
        logger.info(f"상담사 UI 연결됨 (현재 접속자: {len(self.counselor_clients)}명)")

    def disconnect_counselor(self, ws: WebSocket):
        """상담사 UI 접속 해제"""
        self.counselor_clients.discard(ws)
        logger.info(f"상담사 UI 연결 해제 (남은 접속자: {len(self.counselor_clients)}명)")

    async def broadcast_to_counselors(self, payload: Dict[str, Any]):
        """모든 연결된 상담사 UI로 메시지 전파"""
        if not self.counselor_clients:
            return

        msg_str = json.dumps(payload, ensure_ascii=False)
        disconnected = set()

        for client in self.counselor_clients:
            try:
                await client.send_text(msg_str)
            except Exception:
                disconnected.add(client)

        for dc in disconnected:
            self.counselor_clients.discard(dc)

    async def send_to_audio_agent(self, command: Dict[str, Any]):
        """Windows 오디오 캡처 에이전트로 제어 명령 전달"""
        if self.audio_agent_ws:
            try:
                await self.audio_agent_ws.send_text(json.dumps(command))
            except Exception as e:
                logger.warning(f"오디오 에이전트로 명령 전달 실패: {e}")

    async def handle_audio_agent_message(
        self,
        raw_msg: str,
        session_mgr: SessionManager,
        stt_engine: STTEngineBase,
        ollama_client: OllamaClient
    ):
        """오디오 에이전트로부터 전달된 메시지 파싱 및 처리 파이프라인"""
        try:
            data = json.loads(raw_msg)
        except Exception:
            return

        msg_type = data.get("type")

        # 1. VU 레벨 업데이트
        if msg_type == "vu_meter":
            level = data.get("level", 0)
            await self.broadcast_to_counselors({
                "type": "vu_meter",
                "level": level
            })

        # 2. 오디오 세그먼트 수신 -> STT 전사 및 AI 분석
        elif msg_type == "audio_segment":
            is_final = data.get("is_final", True)
            b64_pcm = data.get("pcm_base64", "")
            sample_rate = data.get("sample_rate", 16000)

            if not b64_pcm:
                return

            # int16 PCM -> float32 numpy 변환
            pcm_bytes = base64.b64decode(b64_pcm)
            int16_arr = np.frombuffer(pcm_bytes, dtype=np.int16)
            audio_float32 = (int16_arr.astype(np.float32) / 32767.0)

            # STT 엔진 호출
            stt_result = stt_engine.transcribe_audio(
                audio_float32=audio_float32,
                sample_rate=sample_rate,
                is_final=is_final,
                speaker="혼합/식별중"
            )

            if not is_final:
                # 중간 전사 결과 전송
                session_mgr.interim_text = stt_result.text
                await self.broadcast_to_counselors({
                    "type": "interim_stt",
                    "text": stt_result.text,
                    "confidence": stt_result.confidence
                })
            else:
                # 확정 전사 결과 반영
                item = session_mgr.add_stt_result(stt_result)
                if item:
                    await self.broadcast_to_counselors({
                        "type": "final_stt",
                        "item": item.model_dump()
                    })

                    # 발화가 추가되었으므로 백그라운드에서 Ollama LLM 비동기 분석 실행
                    self._trigger_background_analysis(session_mgr, ollama_client)

        # 3. 에이전트 상태 변경
        elif msg_type == "agent_status":
            status = data.get("status", "UNKNOWN")
            details = data.get("details", {})
            if status == "STARTED":
                session_mgr.recording_state = "RECORDING"
            elif status == "STOPPED":
                session_mgr.recording_state = "IDLE"

            await self.broadcast_to_counselors({
                "type": "recording_status",
                "recording_state": session_mgr.recording_state,
                "status": status,
                "details": details
            })

    def _trigger_background_analysis(self, session_mgr: SessionManager, ollama_client: OllamaClient):
        """이전 분석 작업이 진행 중이면 유지하고, 발화 누적 시 새로운 분석 비동기 실행"""
        # 진행 중인 분석 태스크가 없다면 새로 생성
        if self._analysis_task is None or self._analysis_task.done():
            self._analysis_task = asyncio.create_task(
                self._run_llm_analysis(session_mgr, ollama_client)
            )

    async def _run_llm_analysis(self, session_mgr: SessionManager, ollama_client: OllamaClient):
        """Ollama LLM 분석 실행 후 결과를 모든 상담사 UI로 전송"""
        try:
            # 최근 발화 내역 추출
            transcripts = [t.model_dump() for t in session_mgr.transcripts]
            if not transcripts:
                return

            # 분석 시작 알림 전송 (UI 로딩 인디케이터)
            await self.broadcast_to_counselors({"type": "ai_analyzing", "status": True})

            # 비동기 실행 (I/O 블로킹 방지)
            loop = asyncio.get_running_loop()
            analysis_res = await loop.run_in_executor(
                None,
                ollama_client.analyze_dialog,
                transcripts
            )

            # 세션에 저장 및 상담사 UI 브로드캐스트
            session_mgr.latest_analysis = analysis_res
            await self.broadcast_to_counselors({
                "type": "ai_analysis",
                "analysis": analysis_res.model_dump()
            })

        except Exception as e:
            logger.error(f"비동기 LLM 분석 중 예외 발생: {e}")
        finally:
            await self.broadcast_to_counselors({"type": "ai_analyzing", "status": False})
