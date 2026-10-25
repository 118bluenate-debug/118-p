"""
118 팔배개 - PII 마스킹 및 보안 용어 사전 단위 테스트
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from stt_engine.pii_masker import PIIMasker
from stt_engine.terminology import SecurityTerminologyProcessor


class TestPIIAndTerminology(unittest.TestCase):

    def test_security_terminology_correction(self):
        # 1. 스미싱 발음 오인식
        raw = "스미신 문자가 왔는데요 키사 에 신고하고 싶습니다."
        corrected = SecurityTerminologyProcessor.correct_text(raw)
        self.assertIn("스미싱", corrected)
        self.assertIn("KISA", corrected)

        # 2. 보이스피싱 및 악성코드
        raw2 = "보이스 피신 인 것 같고 악성 apk 가 깔렸어요."
        corrected2 = SecurityTerminologyProcessor.correct_text(raw2)
        self.assertIn("보이스피싱", corrected2)
        self.assertIn("악성apk", corrected2)

        # 3. 원격제어 및 팀뷰어
        raw3 = "상대방이 팀 뷰어 랑 원격 제어 앱을 설치하라고 했어요."
        corrected3 = SecurityTerminologyProcessor.correct_text(raw3)
        self.assertIn("팀뷰어", corrected3)
        self.assertIn("원격제어", corrected3)

    def test_pii_masking(self):
        # 1. 주민등록번호 마스킹
        text_rrn = "민원인 주민번호는 950515-1029384 입니다."
        masked_rrn = PIIMasker.mask_text(text_rrn)
        self.assertIn("950515-*******", masked_rrn)
        self.assertNotIn("1029384", masked_rrn)

        # 2. 휴대전화번호 마스킹
        text_phone = "연락처는 010-9876-5432 로 연락주세요."
        masked_phone = PIIMasker.mask_text(text_phone)
        self.assertIn("010-****-****", masked_phone)
        self.assertNotIn("9876-5432", masked_phone)

        # 3. 카드번호 마스킹
        text_card = "카드번호 9410-1234-5678-9012 에서 출금되었습니다."
        masked_card = PIIMasker.mask_text(text_card)
        self.assertIn("9410-****-****-9012", masked_card)
        self.assertNotIn("1234-5678", masked_card)


if __name__ == "__main__":
    unittest.main()
