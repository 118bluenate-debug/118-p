"""
118 팔배개 - Ollama AI 분석 결과 Pydantic 스키마 및 JSON Schema 정의
상담 내용 실시간 분석, 객관적 사실/주장 구분, 추천 스크립트 및 이관 판단
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class RealtimeAnalysisResult(BaseModel):
    """실시간 상담 분석 결과 모델"""
    counseling_category: str = Field(
        default="상담 유형 분류중",
        description="상담 유형 (스미싱/악성앱 | 보이스피싱 | 개인정보유출/명의도용 | 해킹/계정도용 | 침해사고 신고 | 기타 사이버피해)"
    )
    core_intent: str = Field(
        default="",
        description="민원인의 핵심 요구사항 및 문의 목적 요약 (1~2문장)"
    )
    current_summary: str = Field(
        default="",
        description="현재까지의 상담 진행 상황 요약"
    )
    objective_facts: List[str] = Field(
        default_factory=list,
        description="객관적으로 확인된 사실 (예: 문자 수신 여부, 실제 앱 설치 여부, 금전 송금 여부 등)"
    )
    caller_claims: List[str] = Field(
        default_factory=list,
        description="민원인의 주장 또는 아직 확인되지 않은 내용 (추측 금지, '확인 필요' 표시)"
    )
    recommended_questions: List[str] = Field(
        default_factory=list,
        description="상담사가 민원인에게 추가로 확인해야 할 질문 (우선순위 순)"
    )
    recommended_response_script: str = Field(
        default="",
        description="상담사가 민원인에게 즉시 안내할 표준 추천 멘트"
    )
    responsible_agency: str = Field(
        default="KISA 118 상담센터",
        description="관련 소관 기관 및 연락처 (예: KISA 118, 경찰청 182, 금융감독원 1332, 엠세이퍼 등)"
    )
    caution_notes: List[str] = Field(
        default_factory=list,
        description="민원인 긴급 조치사항 (예: 즉시 비행기탑승모드 설정, 계좌 지급정지, 소액결제 차단 등)"
    )
    escalation_needed: str = Field(
        default="정상 진행",
        description="상급자 이관 필요성 (정상 진행 | 확인 필요 | 즉시 이관 권고)"
    )
    escalation_reason: Optional[str] = Field(
        default="",
        description="이관 필요 시 구체적 사유"
    )


class FinalConsultationSummary(BaseModel):
    """상담 종료 후 최종 요약 및 CRM 저장 모델"""
    session_id: str = Field(description="상담 세션 고유 ID")
    counselor_id: str = Field(default="상담사-01", description="상담사 식별자")
    category: str = Field(description="최종 확정된 상담 유형")
    caller_intent: str = Field(description="민원인 요구사항")
    consultation_summary: str = Field(description="상담 내용 종합 요약")
    action_taken: str = Field(description="상담사가 취한 조치 및 안내 사항")
    next_steps: List[str] = Field(default_factory=list, description="민원인 추가 조치 또는 사후 처리 계획")
    related_agency: str = Field(default="", description="연계/안내 기관")
    escalation_status: str = Field(default="종결", description="처리 상태 (종결 | 상급자 이관 | 유관기관 이첩)")
    raw_transcript_count: int = Field(default=0, description="전체 발화 건수")
    created_at: str = Field(description="상담 완료 일시 (ISO-8601)")
