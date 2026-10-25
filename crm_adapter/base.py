"""
118 팔배개 - CRM 연동 추상 어댑터 인터페이스
향후 Oracle, Tibero, 공공기관 통합 CRM REST API 연계를 위한 확장 가능한 구조
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from llm_analysis.schemas import FinalConsultationSummary


class CRMAdapterBase(ABC):
    """CRM 연동 기본 인터페이스"""

    @abstractmethod
    def save_consultation(self, summary: FinalConsultationSummary) -> Dict[str, Any]:
        """
        상담 최종 기록 저장 (상담사 승인 후 호출)
        
        Returns:
            {"status": "SUCCESS" | "FAILED" | "DUPLICATE", "crm_record_id": str, "message": str}
        """
        pass

    @abstractmethod
    def get_consultation(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 ID로 저장된 상담 기록 조회"""
        pass

    @abstractmethod
    def list_consultations(self, limit: int = 50) -> Dict[str, Any]:
        """저장된 최근 상담 기록 목록 조회"""
        pass
