"""
118 팔배개 - Mock CRM 연동 및 중복 저장 방지 테스트
"""

import sys
import os
import shutil
import unittest
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from crm_adapter.mock_crm import MockCRMAdapter
from llm_analysis.schemas import FinalConsultationSummary


class TestMockCRM(unittest.TestCase):

    def setUp(self):
        self.test_dir = "c:/118-p/data/test_crm_records"
        os.makedirs(self.test_dir, exist_ok=True)
        self.crm = MockCRMAdapter(storage_dir=self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_save_and_duplicate_prevention(self):
        summary = FinalConsultationSummary(
            session_id="SESSION-TEST-20261025-001",
            counselor_id="COUNSELOR-01",
            category="스미싱/악성앱",
            caller_intent="모바일 청첩장 링크 클릭 후 악성앱 삭제 및 소액결제 확인 요청",
            consultation_summary="민원인이 수신한 모바일 청첩장 URL을 통해 악성 apk가 설치되었음을 인지. 비행기탑승모드 설정 안내 및 통신사 소액결제 차단 안내 완료.",
            action_taken="스마트폰 비행기탑승모드 전환 후 엠세이퍼 명의도용방지서비스 등록 안내",
            next_steps=["통신사 고객센터 확인", "엠세이퍼 가입"],
            related_agency="KISA 118, 엠세이퍼",
            escalation_status="종결",
            raw_transcript_count=8,
            created_at=datetime.now().isoformat()
        )

        # 1. 최초 저장 성공 확인
        res1 = self.crm.save_consultation(summary)
        self.assertEqual(res1["status"], "SUCCESS")
        self.assertTrue(res1["crm_record_id"].startswith("CRM-118-"))

        # 2. 동일 세션 ID로 중복 저장 시도 -> DUPLICATE 반환 확인
        res2 = self.crm.save_consultation(summary)
        self.assertEqual(res2["status"], "DUPLICATE")

        # 3. 데이터 조회 검증
        record = self.crm.get_consultation("SESSION-TEST-20261025-001")
        self.assertIsNotNone(record)
        self.assertEqual(record["category"], "스미싱/악성앱")
        self.assertEqual(record["counselor_id"], "COUNSELOR-01")


if __name__ == "__main__":
    unittest.main()
