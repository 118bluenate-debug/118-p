"""
118 팔배개 - 실시간 상담 세션 상태 관리 모듈
발화 기록, 화자 관리, 편집 이력, AI 분석 캐시 및 상태 전이 제어
"""

import uuid
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from stt_engine.base import STTResult
from llm_analysis.schemas import RealtimeAnalysisResult, FinalConsultationSummary


class TranscriptItem(BaseModel):
    """개별 발화 항목 모델"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    speaker: str = Field(default="혼합/식별중")  # 상담사 | 민원인 | 혼합/식별중
    text: str = Field(description="전사 텍스트")
    raw_text: str = Field(default="")
    is_final: bool = Field(default=True)
    confidence: float = Field(default=0.90)
    start_time: float = Field(default=0.0)
    end_time: float = Field(default=0.0)
    timestamp_str: str = Field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))
    edited_by_counselor: bool = Field(default=False)


class SessionManager:
    """실시간 단일/다중 상담 세션 관리자"""

    def __init__(self):
        self.session_id: str = self._generate_session_id()
        self.counselor_id: str = "상담사-01"
        self.counselor_name: str = "118 전문상담사"
        self.start_time: str = datetime.now().isoformat()
        self.recording_state: str = "IDLE"  # IDLE | RECORDING | PAUSED | COMPLETED
        self.transcripts: List[TranscriptItem] = []
        self.interim_text: str = ""
        self.latest_analysis: RealtimeAnalysisResult = RealtimeAnalysisResult()
        self.final_summary: Optional[FinalConsultationSummary] = None

    def _generate_session_id(self) -> str:
        today = datetime.now().strftime("%Y%m%d")
        rand = uuid.uuid4().hex[:6].upper()
        return f"118-CALL-{today}-{rand}"

    def reset_session(self, counselor_id: Optional[str] = None):
        """새 상담 세션으로 초기화"""
        self.session_id = self._generate_session_id()
        if counselor_id:
            self.counselor_id = counselor_id
        self.start_time = datetime.now().isoformat()
        self.recording_state = "IDLE"
        self.transcripts = []
        self.interim_text = ""
        self.latest_analysis = RealtimeAnalysisResult()
        self.final_summary = None

    def add_stt_result(self, stt_res: STTResult) -> Optional[TranscriptItem]:
        """STT 엔진 결과를 세션 발화 목록에 반영"""
        if not stt_res.is_final:
            self.interim_text = stt_res.text
            return None

        # 확정 발화 추가
        self.interim_text = ""
        item = TranscriptItem(
            speaker=stt_res.speaker,
            text=stt_res.text,
            raw_text=stt_res.raw_text,
            is_final=True,
            confidence=stt_res.confidence,
            start_time=stt_res.start_time,
            end_time=stt_res.end_time,
            timestamp_str=datetime.now().strftime("%H:%M:%S")
        )
        self.transcripts.append(item)
        return item

    def edit_transcript(self, item_id: str, new_text: str, new_speaker: Optional[str] = None) -> bool:
        """상담사가 화면에서 직접 STT 오류를 교정하거나 화자를 변경"""
        for item in self.transcripts:
            if item.id == item_id:
                item.text = new_text
                if new_speaker:
                    item.speaker = new_speaker
                item.edited_by_counselor = True
                return True
        return False

    def get_session_snapshot(self) -> Dict[str, Any]:
        """UI에 전송할 세션 전체 스냅샷 반환"""
        return {
            "session_id": self.session_id,
            "counselor_id": self.counselor_id,
            "counselor_name": self.counselor_name,
            "start_time": self.start_time,
            "recording_state": self.recording_state,
            "interim_text": self.interim_text,
            "transcripts": [t.model_dump() for t in self.transcripts],
            "latest_analysis": self.latest_analysis.model_dump(),
            "final_summary": self.final_summary.model_dump() if self.final_summary else None,
            "transcript_count": len(self.transcripts)
        }
