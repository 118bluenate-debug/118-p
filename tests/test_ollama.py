"""
118 팔배개 - Ollama LLM 연동 및 스키마 검증 테스트
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from llm_analysis.ollama_client import OllamaClient
from llm_analysis.schemas import RealtimeAnalysisResult


class TestOllamaAnalysis(unittest.TestCase):

    def setUp(self):
        self.client = OllamaClient()

    def test_ollama_health(self):
        is_healthy = self.client.check_health()
        print(f"\n[Ollama 연결 상태] 건강함: {is_healthy}")
        if is_healthy:
            models = self.client.list_available_models()
            print(f"[설치된 모델 목록] {models}")
            self.assertGreater(len(models), 0)

    def test_realtime_analysis_schema(self):
        # 모의 상담 대화
        sample_script = [
            {"speaker": "민원인", "text": "아침에 모바일 청첩장 문자를 받고 링크를 눌렀는데 이상한 앱이 깔렸어요.", "timestamp_str": "09:00:15"},
            {"speaker": "상담사", "text": "네, 민원인님. 현재 스마트폰 화면에 이상한 팝업이나 원격제어 문구가 뜨시나요?", "timestamp_str": "09:00:25"},
            {"speaker": "민원인", "text": "네, 은행 앱에서 인증번호 문자가 계속 오고 화면 터치가 잘 안 됩니다.", "timestamp_str": "09:00:35"}
        ]

        if not self.client.check_health():
            self.skipTest("Ollama 서버가 오프라인이므로 분석 추론 테스트는 건너뜁니다.")

        print(f"\n[Ollama 추론 실행 중...] 모델: {self.client.model}")
        result = self.client.analyze_dialog(sample_script)

        self.assertIsInstance(result, RealtimeAnalysisResult)
        print(f"분류 결과: {result.counseling_category}")
        print(f"핵심 의도: {result.core_intent}")
        print(f"사실 관계: {result.objective_facts}")
        print(f"추천 멘트: {result.recommended_response_script}")
        print(f"긴급 주의사항: {result.caution_notes}")
        self.assertIsNotNone(result.counseling_category)


if __name__ == "__main__":
    unittest.main()
