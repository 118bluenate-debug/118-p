"""
118 팔배개 - Ollama 로컬 LLM 연동 클라이언트
KISA 118 상담 도메인 프롬프트 주입 및 JSON Schema 기반 검증
"""

import os
import json
import re
import logging
from typing import List, Dict, Any, Optional
import httpx

from llm_analysis.schemas import RealtimeAnalysisResult, FinalConsultationSummary

logger = logging.getLogger("OllamaClient")


class OllamaClient:
    """로컬 Ollama LLM API 통신 및 구조화된 분석 수행 클래스"""

    SYSTEM_PROMPT = """당신은 한국인터넷진흥원(KISA) 118 상담센터의 전문 AI 상담지원 비서 '118 팔배개'입니다.
상담사가 전화로 민원인과 통화하는 실시간 전사 스크립트를 분석하여 상담사를 지원합니다.

[행동 원칙]
1. AI는 상담사를 보조하는 도구입니다. 임의로 해킹 여부나 범죄 성립을 단정하거나 법적 판단을 내리지 마십시오.
2. 민원인이 말한 내용 중 객관적으로 확인된 사실(예: 특정 앱 설치, 문자 링크 클릭, 금전 이체 여부)과 단순 주장/의심을 명확히 구분하십시오.
3. 확인되지 않은 사실은 절대 지어내지 말고 '확인 필요'로 기재하십시오.
4. 민원인이 급박하거나 금전 피해 위험(계좌이체, 원격제어, 인증번호 유출)이 있는 경우 즉시 취해야 할 긴급 주의사항(비행기탑승모드, 지급정지 등)을 최우선으로 안내하십시오.
5. 유관기관(경찰청 182, 금융감독원 1332, 통신사, 엠세이퍼 등)을 정확히 매칭하십시오.
6. 반드시 지정된 JSON 포맷으로만 답변하십시오. 다른 인사말이나 설명 문장은 절대 포함하지 마십시오.
"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: float = 30.0
    ):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "exaone3.5:7.8b")
        self.timeout_seconds = timeout_seconds

    def check_health(self) -> bool:
        """Ollama 서비스 연결 상태 점검"""
        try:
            r = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            return r.status_code == 200
        except Exception:
            return False

    def list_available_models(self) -> List[str]:
        """설치된 모델 목록 조회"""
        try:
            r = httpx.get(f"{self.base_url}/api/tags", timeout=5.0)
            if r.status_code == 200:
                data = r.json()
                return [m.get("name") for m in data.get("models", [])]
        except Exception as e:
            logger.warning(f"Ollama 모델 목록 조회 실패: {e}")
        return []

    def analyze_dialog(
        self,
        transcript_history: List[Dict[str, Any]]
    ) -> RealtimeAnalysisResult:
        """
        현재까지의 상담 발화 기록을 기반으로 실시간 분석 수행
        """
        if not transcript_history:
            return RealtimeAnalysisResult(
                counseling_category="상담 대기",
                core_intent="민원인 발화 대기 중",
                current_summary="아직 발화 내용이 없습니다."
            )

        # 발화 내용 포맷팅
        formatted_script = []
        for item in transcript_history:
            spk = item.get("speaker", "혼합/식별중")
            txt = item.get("text", "")
            ts = item.get("timestamp_str", "")
            formatted_script.append(f"[{spk}] {txt}")

        script_text = "\n".join(formatted_script[-15:])  # 최근 15개 발화 위주 집중 분석

        prompt = f"""다음은 현재 118 상담센터에서 진행 중인 통화 대화 내용입니다:

[실시간 상담 대화]
{script_text}

위 대화를 바탕으로 아래 JSON 구조에 정확히 맞춰 실시간 분석 결과를 출력하십시오:
{{
  "counseling_category": "상담 유형 (스미싱/악성앱 | 보이스피싱 | 개인정보유출/명의도용 | 해킹/계정도용 | 침해사고 신고 | 기타 사이버피해)",
  "core_intent": "민원인의 핵심 요구사항 (1~2문장)",
  "current_summary": "현재까지의 핵심 상황 요약",
  "objective_facts": ["확인된 객관적 사실 1", "확인된 객관적 사실 2"],
  "caller_claims": ["민원인의 주장 또는 미확인 사항 1", "확인 필요 사항"],
  "recommended_questions": ["상담사가 추가로 물어봐야 할 질문 1", "질문 2"],
  "recommended_response_script": "상담사가 민원인에게 안내할 표준 추천 멘트",
  "responsible_agency": "권고 기관 및 안내처",
  "caution_notes": ["긴급 주의사항 1", "주의사항 2"],
  "escalation_needed": "정상 진행 | 확인 필요 | 즉시 이관 권고",
  "escalation_reason": "이관 사유 (해당 없으면 빈 문자열)"
}}
"""

        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "system": self.SYSTEM_PROMPT,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False,
                    "options": {
                        "temperature": 0.2,
                        "top_p": 0.9,
                    }
                },
                timeout=self.timeout_seconds
            )

            if response.status_code == 200:
                raw_json_str = response.json().get("response", "{}")
                parsed_data = self._clean_and_parse_json(raw_json_str)
                return RealtimeAnalysisResult(**parsed_data)
            else:
                logger.error(f"Ollama 호출 실패 ({response.status_code}): {response.text}")

        except Exception as e:
            logger.error(f"Ollama 실시간 분석 중 오류: {e}")

        # 에러 발생 시 안전 폴백 결과 반환
        return RealtimeAnalysisResult(
            counseling_category="분석 대기 (로컬 LLM 응답 지연)",
            core_intent="민원인 발화 내용 청취 중",
            current_summary="대화 내용을 계속 수집하고 있습니다.",
            objective_facts=["상담 연결 진행 중"],
            caller_claims=["확인 필요"],
            recommended_questions=["정확한 피해 일시와 수신하신 문자/링크 내용을 확인해 주시겠습니까?"],
            recommended_response_script="네, 민원인님. 118 상담센터입니다. 침착하게 상황을 말씀해주시면 확인 후 안내해 드리겠습니다.",
            responsible_agency="KISA 118 상담센터"
        )

    def generate_final_summary(
        self,
        session_id: str,
        counselor_id: str,
        transcript_history: List[Dict[str, Any]]
    ) -> FinalConsultationSummary:
        """상담 종료 시 최종 요약 및 CRM 저장용 레코드 생성"""
        from datetime import datetime

        full_script = "\n".join([
            f"[{item.get('speaker', '혼합')}]: {item.get('text', '')}"
            for item in transcript_history
        ])

        prompt = f"""다음 통화 녹취 전문을 종합하여 상담 종료 보고서를 작성하십시오:

[상담 전문]
{full_script}

반드시 다음 JSON 형식으로 출력하십시오:
{{
  "category": "최종 확정 상담 분류",
  "caller_intent": "민원인 핵심 요구",
  "consultation_summary": "전체 상담 경과 및 피해 정황 종합 요약",
  "action_taken": "상담사가 안내한 조치 및 취한 대응",
  "next_steps": ["민원인 후속 조치 1", "후속 조치 2"],
  "related_agency": "안내된 유관기관",
  "escalation_status": "종결 | 상급자 이관 | 유관기관 이첩"
}}
"""

        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "system": self.SYSTEM_PROMPT,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False,
                    "options": {"temperature": 0.1}
                },
                timeout=self.timeout_seconds
            )

            if response.status_code == 200:
                raw_json = response.json().get("response", "{}")
                data = self._clean_and_parse_json(raw_json)
                return FinalConsultationSummary(
                    session_id=session_id,
                    counselor_id=counselor_id,
                    category=data.get("category", "일반 상담"),
                    caller_intent=data.get("caller_intent", "상담 종료"),
                    consultation_summary=data.get("consultation_summary", "상담 완료"),
                    action_taken=data.get("action_taken", "기본 안내 완료"),
                    next_steps=data.get("next_steps", []),
                    related_agency=data.get("related_agency", "KISA 118"),
                    escalation_status=data.get("escalation_status", "종결"),
                    raw_transcript_count=len(transcript_history),
                    created_at=datetime.now().isoformat()
                )
        except Exception as e:
            logger.error(f"최종 요약 생성 실패: {e}")

        # 기본 폴백 요약
        return FinalConsultationSummary(
            session_id=session_id,
            counselor_id=counselor_id,
            category="사이버피해 상담",
            caller_intent="민원 상담",
            consultation_summary="118 상담 접수 및 기본 대응 안내 완료",
            action_taken="민원 내용 확인 및 주의사항 안내",
            next_steps=["추가 피해 발생 시 118 재인입 안내"],
            related_agency="KISA 118",
            escalation_status="종결",
            raw_transcript_count=len(transcript_history),
            created_at=datetime.now().isoformat()
        )

    def _clean_and_parse_json(self, raw_str: str) -> Dict[str, Any]:
        """JSON 코드블록 마크다운 제거 및 파싱"""
        cleaned = raw_str.strip()
        # ```json ... ``` 패턴 제거
        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
            if match:
                cleaned = match.group(1).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning(f"JSON 파싱 실패, 정규식 추출 시도: {cleaned[:100]}")
            # 첫 번째 { 와 마지막 } 사이 추출
            s = cleaned.find("{")
            e = cleaned.rfind("}")
            if s != -1 and e != -1 and e > s:
                return json.loads(cleaned[s:e+1])
            return {}
