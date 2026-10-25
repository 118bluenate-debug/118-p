"""
118 팔배개 - 민감 개인정보(PII) 마스킹 모듈
상담 발화 및 텍스트 내 주민등록번호, 전화번호, 계좌번호, 카드번호 마스킹
"""

import re
from typing import Dict, List, Tuple


class PIIMasker:
    """개인정보보호법 및 118 보안 지침에 따른 민감정보 비식별화"""

    # 1. 주민등록번호 (생년월일 6자리 - 뒷자리 7자리)
    # 예: 900101-1234567 -> 900101-*******
    PATTERN_RRN = re.compile(r"\b(\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01]))[- ]?([1-8]\d{6})\b")

    # 2. 휴대폰 및 유선전화번호
    # 예: 010-1234-5678 -> 010-****-5678 (또는 전체 마스킹 010-****-****)
    PATTERN_PHONE = re.compile(r"\b(01[016789]|02|0[3-6][1-5])[- ]?(\d{3,4})[- ]?(\d{4})\b")

    # 3. 신용카드 번호 (16자리)
    # 예: 1234-5678-9012-3456 -> 1234-****-****-3456
    PATTERN_CARD = re.compile(r"\b(\d{4})[- ]?(\d{4})[- ]?(\d{4})[- ]?(\d{4})\b")

    # 4. 은행 계좌번호 (통상 11~14자리 연속 숫자)
    PATTERN_ACCOUNT = re.compile(r"\b(\d{3,6})[- ]?(\d{2,6})[- ]?(\d{4,8})\b")

    @classmethod
    def mask_text(cls, text: str, full_phone_mask: bool = True) -> str:
        """
        텍스트 내 민감정보 탐지 및 마스킹 적용
        """
        if not text:
            return ""

        masked = text

        # 1. 주민등록번호 마스킹
        masked = cls.PATTERN_RRN.sub(r"\1-*******", masked)

        # 2. 카드번호 마스킹 (계좌번호보다 먼저 적용)
        masked = cls.PATTERN_CARD.sub(r"\1-****-****-\4", masked)

        # 3. 전화번호 마스킹
        if full_phone_mask:
            masked = cls.PATTERN_PHONE.sub(r"\1-****-****", masked)
        else:
            masked = cls.PATTERN_PHONE.sub(r"\1-****-\3", masked)

        return masked

    @classmethod
    def contains_pii(cls, text: str) -> bool:
        """텍스트에 민감정보가 포함되어 있는지 여부 검사"""
        if not text:
            return False
        return bool(
            cls.PATTERN_RRN.search(text) or
            cls.PATTERN_PHONE.search(text) or
            cls.PATTERN_CARD.search(text)
        )
