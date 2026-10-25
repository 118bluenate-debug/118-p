"""
118 팔배개 - 보안 전문용어 사전 및 음성인식 후처리 모듈
KISA 118 상담 도메인 특화 용어 보정 및 발음 오인식 수정
"""

import re
from typing import Dict, List, Tuple


class SecurityTerminologyProcessor:
    """118 상담센터 보안 전문용어 후처리 클래스"""

    # 1. 빈출 발음 오인식 치환 사전 (Regex Pattern -> 정규화 단어)
    PHONETIC_REPLACEMENTS: List[Tuple[re.Pattern, str]] = [
        # 피싱 / 스미싱 / 파밍 / 큐싱
        (re.compile(r"\b(스미신|슴이싱|스밋싱)\b", re.IGNORECASE), "스미싱"),
        (re.compile(r"\b(보이스\s*피신|보이스\s*피싱)\b", re.IGNORECASE), "보이스피싱"),
        (re.compile(r"\b(큐알\s*피싱|큐알피싱|큐씽)\b", re.IGNORECASE), "큐싱"),
        (re.compile(r"\b(파민|팜잉)\b", re.IGNORECASE), "파밍"),
        (re.compile(r"\b(랜섬\s*웨어|랜섬웨\s*어)\b", re.IGNORECASE), "랜섬웨어"),
        (re.compile(r"\b(악성\s*코드|악성\s*앱|악성\s*apk)\b", re.IGNORECASE), lambda m: m.group(0).replace(" ", "")),
        (re.compile(r"\b(명의\s*도용)\b", re.IGNORECASE), "명의도용"),
        (re.compile(r"\b(인증\s*번호)\b", re.IGNORECASE), "인증번호"),
        (re.compile(r"\b(보안\s*카드)\b", re.IGNORECASE), "보안카드"),
        (re.compile(r"\b(원격\s*제어|원격\s*조종)\b", re.IGNORECASE), "원격제어"),
        (re.compile(r"\b(팀\s*뷰어|팀뷰어)\b", re.IGNORECASE), "팀뷰어"),
        (re.compile(r"\b(애니\s*데스크|애니데스)\b", re.IGNORECASE), "애니데스크"),

        # 주요 기관 및 서비스명
        (re.compile(r"\b(키사|키싸|기사)\s*(에서)?\b", re.IGNORECASE), "KISA "),
        (re.compile(r"\b(한국\s*인터넷\s*진흥원)\b", re.IGNORECASE), "한국인터넷진흥원"),
        (re.compile(r"\b(보호\s*나라)\b", re.IGNORECASE), "보호나라"),
        (re.compile(r"\b(개인\s*정보\s*보호\s*위원회)\b", re.IGNORECASE), "개인정보보호위원회"),
        (re.compile(r"\b(사이버\s*수사대|사이버\s*경찰청)\b", re.IGNORECASE), "사이버수사대"),
        (re.compile(r"\b(금융\s*감독원|금감원)\b", re.IGNORECASE), "금융감독원"),

        # 기술 및 프로토콜
        (re.compile(r"\b(디도스|디\s*도스)\b", re.IGNORECASE), "DDoS"),
        (re.compile(r"\b(피싱\s*사이트)\b", re.IGNORECASE), "피싱사이트"),
        (re.compile(r"\b(취약점\s*점검)\b", re.IGNORECASE), "취약점 점검"),
        (re.compile(r"\b(침해\s*사고)\b", re.IGNORECASE), "침해사고"),
    ]

    # Whisper 초기 프롬프트에 주입하여 인식률을 높이는 도메인 용어 리스트
    PROMPT_KEYWORDS = (
        "118 상담센터, 한국인터넷진흥원, KISA, 보호나라, 스미싱, 보이스피싱, 파밍, 큐싱, "
        "랜섬웨어, 악성코드, 악성앱, 원격제어, 팀뷰어, 애니데스크, 명의도용, 개인정보유출, "
        "금융감독원, 경찰청 182, 인증번호, 계좌이체, 소액결제, 사이버범죄"
    )

    @classmethod
    def correct_text(cls, text: str) -> str:
        """STT 결과 텍스트에 보안 용어 교정 규칙 적용"""
        if not text:
            return ""

        corrected = text
        for pattern, replacement in cls.PHONETIC_REPLACEMENTS:
            if callable(replacement):
                corrected = pattern.sub(replacement, corrected)
            else:
                corrected = pattern.sub(replacement, corrected)

        # 다중 공백 정리
        corrected = re.sub(r"\s+", " ", corrected).strip()
        return corrected

    @classmethod
    def get_initial_prompt(cls) -> str:
        """Faster-Whisper 디코딩 시 사용할 도메인 가이드 프롬프트"""
        return cls.PROMPT_KEYWORDS
