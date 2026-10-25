"""
118 팔배개 - 개발 및 검증용 Mock CRM 어댑터
로컬 JSON 파일 저장, 중복 방지, 감사 로그 및 내보내기 지원
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from crm_adapter.base import CRMAdapterBase
from llm_analysis.schemas import FinalConsultationSummary

logger = logging.getLogger("MockCRM")


class MockCRMAdapter(CRMAdapterBase):
    """로컬 파일 기반 Mock CRM 시스템"""

    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = storage_dir or os.getenv("CRM_DATA_DIR", "c:/118-p/data/crm_records")
        os.makedirs(self.storage_dir, exist_ok=True)
        self.audit_log_path = os.path.join(self.storage_dir, "crm_audit.log")

    def _generate_record_id(self) -> str:
        """KISA 118 상담 접수번호 양식 생성"""
        today_str = datetime.now().strftime("%Y%m%d")
        millis = int(datetime.now().microsecond / 1000)
        return f"CRM-118-{today_str}-{millis:03d}"

    def _log_audit(self, action: str, session_id: str, counselor_id: str, details: str):
        """내부 보안 규정에 따른 CRM 접근/저장 감사 로그 기록"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "session_id": session_id,
            "counselor_id": counselor_id,
            "details": details
        }
        try:
            with open(self.audit_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"감사 로그 기록 실패: {e}")

    def save_consultation(self, summary: FinalConsultationSummary) -> Dict[str, Any]:
        """
        상담 최종 기록 저장 (중복 저장 방지 포함)
        """
        file_path = os.path.join(self.storage_dir, f"{summary.session_id}.json")

        # 중복 저장 방지 검사
        if os.path.exists(file_path):
            self._log_audit(
                action="SAVE_ATTEMPT_DUPLICATE",
                session_id=summary.session_id,
                counselor_id=summary.counselor_id,
                details="이미 동일한 세션 ID로 등록된 상담 레코드가 존재합니다."
            )
            return {
                "status": "DUPLICATE",
                "crm_record_id": "",
                "message": f"세션 ID '{summary.session_id}'는 이미 저장되었습니다. 중복 저장이 방지되었습니다.",
                "file_path": file_path
            }

        crm_id = self._generate_record_id()
        payload = summary.model_dump()
        payload["crm_record_id"] = crm_id
        payload["saved_at"] = datetime.now().isoformat()

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

            self._log_audit(
                action="SAVE_SUCCESS",
                session_id=summary.session_id,
                counselor_id=summary.counselor_id,
                details=f"CRM 레코드 생성 완료: {crm_id}"
            )

            return {
                "status": "SUCCESS",
                "crm_record_id": crm_id,
                "message": "118 상담 기록이 Mock CRM에 성공적으로 저장되었습니다.",
                "file_path": file_path
            }

        except Exception as e:
            logger.error(f"CRM 저장 실패: {e}")
            self._log_audit(
                action="SAVE_ERROR",
                session_id=summary.session_id,
                counselor_id=summary.counselor_id,
                details=f"저장 중 예외 발생: {str(e)}"
            )
            return {
                "status": "FAILED",
                "crm_record_id": "",
                "message": f"CRM 저장 중 오류가 발생했습니다: {str(e)}"
            }

    def get_consultation(self, session_id: str) -> Optional[Dict[str, Any]]:
        file_path = os.path.join(self.storage_dir, f"{session_id}.json")
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def list_consultations(self, limit: int = 50) -> Dict[str, Any]:
        """저장된 최근 상담 레코드 목록 조회"""
        records = []
        if not os.path.exists(self.storage_dir):
            return {"records": [], "total": 0}

        files = [f for f in os.listdir(self.storage_dir) if f.endswith(".json")]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(self.storage_dir, x)), reverse=True)

        for filename in files[:limit]:
            filepath = os.path.join(self.storage_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    records.append(data)
            except Exception:
                continue

        return {"records": records, "total": len(records)}
