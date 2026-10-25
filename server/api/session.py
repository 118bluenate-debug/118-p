"""
118 팔배개 - 상담 세션 관리 API
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional

router = APIRouter(prefix="/api/session", tags=["Session"])


class TranscriptEditRequest(BaseModel):
    text: str
    speaker: Optional[str] = None


class ResetSessionRequest(BaseModel):
    counselor_id: Optional[str] = "상담사-01"


@router.get("")
def get_session(request: Request):
    """현재 활성 상담 세션 스냅샷 반환"""
    session_mgr = request.app.state.session_manager
    return session_mgr.get_session_snapshot()


@router.post("/reset")
def reset_session(req: ResetSessionRequest, request: Request):
    """새로운 상담 세션 시작 및 초기화"""
    session_mgr = request.app.state.session_manager
    session_mgr.reset_session(counselor_id=req.counselor_id)
    return session_mgr.get_session_snapshot()


@router.put("/transcript/{item_id}")
async def edit_transcript(item_id: str, req: TranscriptEditRequest, request: Request):
    """상담사가 STT 전사 텍스트 또는 화자를 수정"""
    session_mgr = request.app.state.session_manager
    ws_mgr = request.app.state.ws_manager

    success = session_mgr.edit_transcript(item_id, req.text, req.speaker)
    if not success:
        raise HTTPException(status_code=404, detail="발화 항목을 찾을 수 없습니다.")

    # 수정 사항을 연결된 모든 UI에 브로드캐스트
    await ws_mgr.broadcast_to_counselors({
        "type": "transcript_edited",
        "item_id": item_id,
        "text": req.text,
        "speaker": req.speaker
    })
    return {"status": "SUCCESS", "item_id": item_id}


@router.post("/analyze")
async def trigger_manual_analysis(request: Request):
    """상담사가 수동으로 즉시 AI 재분석 요청"""
    session_mgr = request.app.state.session_manager
    ollama_client = request.app.state.ollama_client
    ws_mgr = request.app.state.ws_manager

    transcripts = [t.model_dump() for t in session_mgr.transcripts]
    if not transcripts:
        return session_mgr.latest_analysis.model_dump()

    await ws_mgr.broadcast_to_counselors({"type": "ai_analyzing", "status": True})
    try:
        analysis = ollama_client.analyze_dialog(transcripts)
        session_mgr.latest_analysis = analysis
        await ws_mgr.broadcast_to_counselors({
            "type": "ai_analysis",
            "analysis": analysis.model_dump()
        })
        return analysis.model_dump()
    finally:
        await ws_mgr.broadcast_to_counselors({"type": "ai_analyzing", "status": False})
