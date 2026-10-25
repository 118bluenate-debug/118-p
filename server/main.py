"""
118 팔배개 (118 PAL-BEGAE) - KISA 118 AI 상담지원 시스템 메인 서버
FastAPI 백엔드, 실시간 WebSocket 브로드캐스터, STT 엔진 및 Ollama LLM 오케스트레이션
"""

import sys
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# 경로 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from server.config import settings
from server.session_manager import SessionManager
from server.websocket_manager import WebSocketManager
from server.api.devices import router as devices_router
from server.api.session import router as session_router
from server.api.crm import router as crm_router

from stt_engine.factory import STTEngineFactory
from llm_analysis.ollama_client import OllamaClient
from crm_adapter.mock_crm import MockCRMAdapter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s"
)
logger = logging.getLogger("118PalBegaeServer")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 수명주기 초기화 및 자원 해제"""
    logger.info("=" * 60)
    logger.info("  [118 팔배개] KISA 118 AI 상담지원 시스템 서버 기동")
    logger.info("=" * 60)

    # 1. 상태 및 매니저 초기화
    app.state.session_manager = SessionManager()
    app.state.ws_manager = WebSocketManager()
    app.state.crm_adapter = MockCRMAdapter(storage_dir=settings.crm_data_dir)

    # 2. Ollama 클라이언트 초기화
    app.state.ollama_client = OllamaClient(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        timeout_seconds=settings.ollama_timeout_seconds
    )
    ollama_ok = app.state.ollama_client.check_health()
    logger.info(f"Ollama 로컬 LLM 연결 상태: {'정상 (온라인)' if ollama_ok else '오프라인 (확인 필요)'} - 모델: {settings.ollama_model}")

    # 3. STT 엔진 로드 (Faster-Whisper CUDA / CPU)
    logger.info(f"STT 엔진 초기화 중: {settings.stt_engine} (모델: {settings.stt_model_size})")
    try:
        app.state.stt_engine = STTEngineFactory.create_engine(
            engine_type=settings.stt_engine,
            model_size=settings.stt_model_size,
            device=settings.stt_device,
            compute_type=settings.stt_compute_type,
            mask_pii=settings.mask_pii_enabled,
            apply_security_dict=settings.security_dictionary_enabled
        )
        logger.info(f"STT 엔진 준비 완료: {app.state.stt_engine.get_engine_info()}")
    except Exception as e:
        logger.warning(f"Faster-Whisper 로드 실패 ({e}), Mock STT 엔진으로 폴백합니다.")
        app.state.stt_engine = STTEngineFactory.create_engine(engine_type="mock")

    logger.info(f"서버 준비 완료: http://{settings.server_host}:{settings.server_port}")
    yield

    logger.info("서버가 안전하게 종료되었습니다.")


app = FastAPI(
    title="118 팔배개 (118 PAL-BEGAE) API",
    description="한국인터넷진흥원(KISA) 118 상담센터 전용 로컬 AI 상담지원 시스템",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 미들웨어 (React 프론트엔드 통신 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST API 라우터 등록
app.include_router(devices_router)
app.include_router(session_router)
app.include_router(crm_router)


@app.get("/api/health")
def health_check():
    """서버 헬스체크 및 엔진 상태 반환"""
    stt_info = getattr(app.state, "stt_engine", None)
    ollama_client = getattr(app.state, "ollama_client", None)

    return {
        "status": "HEALTHY",
        "system": "118 팔배개 (118 PAL-BEGAE)",
        "organization": "한국인터넷진흥원(KISA) 118 상담센터",
        "stt_engine": stt_info.get_engine_info() if stt_info else "NOT_INITIALIZED",
        "ollama_online": ollama_client.check_health() if ollama_client else False,
        "ollama_model": settings.ollama_model
    }


# ==============================================================================
# WebSocket 엔드포인트
# ==============================================================================

@app.websocket("/ws/counselor")
async def websocket_counselor(websocket: WebSocket):
    """상담사 웹 UI 실시간 전사 및 AI 분석 결과 전송 소켓"""
    ws_mgr: WebSocketManager = app.state.ws_manager
    session_mgr: SessionManager = app.state.session_manager
    await ws_mgr.connect_counselor(websocket, session_mgr)

    try:
        while True:
            # 상담사 UI로부터의 명령 수신 (화자 변경, 세션 제어 등)
            data_text = await websocket.receive_text()
            # 필요 시 클라이언트 이벤트 처리
    except WebSocketDisconnect:
        ws_mgr.disconnect_counselor(websocket)
    except Exception as e:
        logger.debug(f"상담사 소켓 예외: {e}")
        ws_mgr.disconnect_counselor(websocket)


@app.websocket("/ws/audio")
async def websocket_audio_agent(websocket: WebSocket):
    """Windows 호스트 오디오 수집 에이전트 전용 PCM 스트리밍 소켓"""
    await websocket.accept()
    ws_mgr: WebSocketManager = app.state.ws_manager
    session_mgr: SessionManager = app.state.session_manager
    stt_engine = app.state.stt_engine
    ollama_client = app.state.ollama_client

    ws_mgr.audio_agent_ws = websocket
    logger.info("Windows 오디오 에이전트가 WebSocket에 연결되었습니다.")

    try:
        while True:
            raw_msg = await websocket.receive_text()
            await ws_mgr.handle_audio_agent_message(
                raw_msg=raw_msg,
                session_mgr=session_mgr,
                stt_engine=stt_engine,
                ollama_client=ollama_client
            )
    except WebSocketDisconnect:
        logger.warning("Windows 오디오 에이전트 연결이 끊어졌습니다.")
        ws_mgr.audio_agent_ws = None
        session_mgr.recording_state = "IDLE"
        await ws_mgr.broadcast_to_counselors({
            "type": "recording_status",
            "recording_state": "IDLE",
            "status": "DISCONNECTED",
            "details": {}
        })
    except Exception as e:
        logger.error(f"오디오 에이전트 소켓 예외: {e}")
        ws_mgr.audio_agent_ws = None


# 빌드된 정적 UI 파일이 있는 경우 서빙
dist_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(dist_path):
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=False
    )
