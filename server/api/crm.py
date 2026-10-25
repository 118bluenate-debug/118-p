"""
118 팔배개 - CRM 연계 및 JSON 내보내기 API
"""

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os

from llm_analysis.schemas import FinalConsultationSummary

router = APIRouter(prefix="/api/crm", tags=["CRM"])


class SaveCRMRequest(BaseModel):
    category: Optional[str] = None
    caller_intent: Optional[str] = None
    consultation_summary: Optional[str] = None
    action_taken: Optional[str] = None
    related_agency: Optional[str] = None
    escalation_status: Optional[str] = None


@router.post("/save")
async def save_to_crm(req: SaveCRMRequest, request: Request):
    """
    상담 종료 및 CRM 저장 (상담사 최종 확인 후 제출)
    """
    session_mgr = request.app.state.session_manager
    ollama_client = request.app.state.ollama_client
    crm_adapter = request.app.state.crm_adapter
    ws_mgr = request.app.state.ws_manager

    # 1. 만약 상담사가 수정한 요약값이 전달되지 않은 경우 Ollama로 최종 요약 자동 생성
    transcripts = [t.model_dump() for t in session_mgr.transcripts]
    summary = ollama_client.generate_final_summary(
        session_id=session_mgr.session_id,
        counselor_id=session_mgr.counselor_id,
        transcript_history=transcripts
    )

    # 2. 상담사가 UI에서 직접 수정한 필드가 있으면 덮어쓰기 (상담사 최종 권한)
    if req.category:
        summary.category = req.category
    if req.caller_intent:
        summary.caller_intent = req.caller_intent
    if req.consultation_summary:
        summary.consultation_summary = req.consultation_summary
    if req.action_taken:
        summary.action_taken = req.action_taken
    if req.related_agency:
        summary.related_agency = req.related_agency
    if req.escalation_status:
        summary.escalation_status = req.escalation_status

    # 3. CRM 저장 (중복 저장 방지 로직 적용)
    save_result = crm_adapter.save_consultation(summary)

    if save_result["status"] in ("SUCCESS", "DUPLICATE"):
        session_mgr.recording_state = "COMPLETED"
        session_mgr.final_summary = summary

        # UI에 상담 완료 및 CRM 저장 결과 브로드캐스트
        await ws_mgr.broadcast_to_counselors({
            "type": "consultation_completed",
            "crm_result": save_result,
            "final_summary": summary.model_dump()
        })

    return save_result


@router.get("/records")
def list_crm_records(request: Request, limit: int = 50):
    """저장된 최근 상담 레코드 목록 조회"""
    crm_adapter = request.app.state.crm_adapter
    return crm_adapter.list_consultations(limit=limit)


@router.get("/export/{session_id}")
def export_crm_record(session_id: str, request: Request):
    """지정된 상담 세션의 JSON 파일 다운로드"""
    crm_adapter = request.app.state.crm_adapter
    file_path = os.path.join(crm_adapter.storage_dir, f"{session_id}.json")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="해당 세션의 CRM 기록을 찾을 수 없습니다.")

    return FileResponse(
        path=file_path,
        media_type="application/json",
        filename=f"{session_id}.json"
    )
