# 118 팔배개 (118 PAL-BEGAE)

> **한국인터넷진흥원(KISA) 118 상담센터 내부망 전용 실시간 AI 상담지원 시스템**  
> *전화 음성 실시간 STT 전사, 로컬 LLM 상담 분석, 표준 스크립트 추천 및 Mock CRM 연계*

---

## 1. 개요 및 설계 원칙

**118 팔배개**는 한국인터넷진흥원(KISA) 118 상담센터 상담사가 민원인과의 유선전화 통화 중에 음성을 실시간으로 텍스트로 변환(STT)하고, 로컬 LLM(Ollama)을 통해 피해 유형 분석, 핵심 요구사항 추출, 표준 응대 스크립트를 추천하는 내부망 전용 상담지원 시스템입니다.

### 핵심 원칙
1. **상담사 보조 원칙**: AI는 상담사의 판단을 보조하며 독자적으로 상담을 종료하거나 법적 판단을 내리지 않습니다.
2. **폐쇄망/내부망 운영**: 외부 AI 클라우드 API 호출을 전면 금지하며 모든 처리는 내부 GPU(RTX 5080)에서 로컬로 수행됩니다.
3. **오디오 보안**: 원본 오디오는 영구 저장하지 않으며 메모리 상에서 실시간 16kHz PCM으로 변환되어 STT 엔진으로 전달됩니다.
4. **민감정보 보호(PII)**: 주민등록번호, 전화번호, 신용카드번호는 전사 단계에서 자동 마스킹 처리됩니다.

---

## 2. 시스템 아키텍처 및 데이터 흐름

```
+----------------------------------------------------------------------------------------------------+
|                                      Windows 11 Host OS                                            |
|                                                                                                    |
|  [USB 오디오 인터페이스 Line-in] ────► [audio_agent (Windows 호스트 프로세스)]                     |
|                                         ├─ 오디오 장치 검색 & Line-in 자동 식별                     |
|                                         ├─ 실시간 16kHz Mono PCM 리샘플링                           |
|                                         ├─ RMS 에너지 기반 VAD (음성/묵음 분할)                     |
|                                         └─ 실시간 VU 레벨 및 PCM 스트리밍 (WebSocket)              |
+───────────────────────────────────────────────────┬────────────────────────────────────────────────+
                                                    │ ws://127.0.0.1:8000/ws/audio
                                                    ▼
+----------------------------------------------------------------------------------------------------+
|                                FastAPI & WebSocket 서버 (포트: 8000)                                |
|                                                                                                    |
|  [STT 엔진 어댑터]                               [로컬 LLM 분석 모듈]                              |
|   Faster-Whisper (CUDA RTX 5080 가속)             Ollama API (EXAONE 3.5 / Qwen 4B)                |
|   ├─ 중간 전사 (Interim) & 확정 전사 (Final)       ├─ 상담 유형 자동 분류 (스미싱, 피싱 등)          |
|   ├─ 118 보안 전문용어 보정 사전 적용              ├─ 객관적 사실 vs 민원인 주장 분리               |
|   └─ PII 민감정보 자동 마스킹                     ├─ KISA 118 표준 권고 스크립트 도출               |
|                                                   └─ 상급자/유관기관 이관 필요성 판단               |
|                                                                                                    |
|  [상담 세션 관리자]                             [CRM 연계 모듈]                                   |
|   실시간 발화 기록, 화자 관리, 편집 이력 보존     Mock CRM 어댑터 (JSON 내보내기, 중복 방지)        |
+───────────────────────────────────────────────────┬────────────────────────────────────────────────+
                                                    │ ws://127.0.0.1:8000/ws/counselor
                                                    ▼
+----------------------------------------------------------------------------------------------------+
|                                상담사 실시간 웹 대시보드 (React + TypeScript)                      |
|                                                                                                    |
|  [상단 바]      Line-in VU 미터, 녹음 상태(LIVE), 오디오 장치 설정, 세션 리셋                      |
|  [A. 스크립트]  상담사/민원인 발화 타임라인, 실시간 중간 전사, 오인식 즉시 수정                    |
|  [B. AI 분석]   피해 유형 태그, 핵심 요구, 확인된 사실 vs 주장 체크리스트                          |
|  [C. 추천 응대] 118 표준 멘트 1클릭 복사, 추가 확인할 질문 Q1/Q2, 긴급 주의사항 배지               |
|  [D. 상담 종료] 최종 상담 요약 검토, CRM 등록 및 상담 기록 JSON 다운로드                           |
+----------------------------------------------------------------------------------------------------+
```

---

## 3. 디렉터리 구조

```text
c:\118-p\
├── audio_agent/                    # Windows Line-in 오디오 수집 에이전트
│   ├── __init__.py
│   ├── device_manager.py           # 오디오 입력 장치 열거 및 Line-in 식별
│   ├── vad.py                      # RMS 에너지 기반 VAD & VU 미터 계산기
│   ├── capture.py                  # 실시간 16kHz Mono 리샘플링 캡처 스트림
│   ├── ws_client.py                # STT 서버로 오디오 스트리밍하는 WS 클라이언트
│   └── run_agent.py                # 에이전트 단독 실행 CLI (장치 목록/테스트 지원)
├── stt_engine/                     # Whisper STT 엔진 및 어댑터
│   ├── __init__.py
│   ├── base.py                     # STTEngineBase 추상 클래스 및 STTResult
│   ├── faster_whisper_engine.py    # Faster-Whisper 구현체 (CUDA 가속 & CPU 폴백)
│   ├── mock_engine.py              # 테스트/CI용 Mock 엔진
│   ├── terminology.py              # 118 보안 전문용어 교정 사전 (스미싱, KISA 등)
│   ├── pii_masker.py               # 주민번호, 전화번호, 카드번호 마스킹
│   └── factory.py                  # STT 엔진 팩토리
├── llm_analysis/                   # Ollama 기반 로컬 LLM 분석 모듈
│   ├── __init__.py
│   ├── schemas.py                  # Pydantic 분석 결과 스키마
│   └── ollama_client.py            # 프롬프트 템플릿 및 JSON Schema 검증기
├── crm_adapter/                    # CRM 연계 모듈
│   ├── __init__.py
│   ├── base.py                     # CRMAdapterBase 추상 클래스
│   └── mock_crm.py                 # Mock CRM (JSON 파일 저장, 중복 방지, 감사 로그)
├── server/                         # FastAPI 백엔드
│   ├── __init__.py
│   ├── config.py                   # 환경설정
│   ├── session_manager.py          # 활성 상담 세션 상태 관리자
│   ├── websocket_manager.py        # 오디오 에이전트 및 상담사 UI 웹소켓 허브
│   ├── main.py                     # FastAPI 앱 진입점
│   └── api/                        # REST API (devices, session, crm)
│       ├── __init__.py
│       ├── devices.py
│       ├── session.py
│       └── crm.py
├── frontend/                       # React + TypeScript 상담사 대시보드
│   ├── package.json
│   ├── vite.config.ts
│   ├── dist/                       # 프로덕션 번들
│   └── src/
│       ├── App.tsx
│       ├── index.css               # 글래스모피즘 & 다크 사이버 디자인
│       ├── types/index.ts
│       ├── hooks/useWebSocket.ts
│       └── components/             # Header, ScriptPanel, AnalysisPanel 등
├── scripts/                        # 실행 및 설치 스크립트
│   ├── install_windows.ps1         # Windows 원클릭 설치
│   ├── install_wsl2.sh             # WSL2 Ubuntu 설치
│   ├── run_server.ps1              # 서버 기동
│   ├── run_agent.ps1               # 오디오 에이전트 기동
│   └── test_all.ps1                # 전체 자동 테스트 실행
├── tests/                          # 단위 및 통합 테스트
│   ├── test_pii_and_terms.py
│   ├── test_vad.py
│   ├── test_mock_crm.py
│   ├── test_server_init.py
│   └── test_ollama.py
├── .env.example                    # 환경설정 예시 파일
├── requirements.txt                # 파이썬 의존성
├── Dockerfile                      # 백엔드 도커 이미지
├── docker-compose.yml              # GPU 컨테이너 배포 구성
└── gitlab-ci.yml                   # GitLab CI/CD 파이프라인
```

---

## 4. 설치 및 실행 가이드

### [사전 요구사항]
- **OS**: Windows 11 (또는 WSL2 Ubuntu)
- **GPU**: NVIDIA RTX 5080 (또는 CUDA 호환 GPU, 드라이버 최신 유지)
- **Ollama**: 설치 후 로컬 모델(`qwen3:4b` 또는 `exaone3.5:7.8b`) 사전 다운로드:
  ```bash
  ollama pull qwen3:4b
  ollama pull exaone3.5:7.8b
  ```

### 1단계: Windows 원클릭 설치
PowerShell에서 다음 스크립트를 실행합니다:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_windows.ps1
```

### 2단계: 서버 기동
```powershell
powershell scripts\run_server.ps1
```
- 서버가 기동되면 Faster-Whisper(CUDA 가속) 및 Ollama 연결이 자동으로 활성화됩니다.
- 브라우저에서 `http://127.0.0.1:8000` 접속 시 상담사 대시보드가 열립니다.

### 3단계: Windows 오디오 입력 장치 확인 및 에이전트 실행
사용 가능한 오디오 장치 및 Line-in 목록을 확인합니다:
```powershell
powershell scripts\run_agent.ps1 -ListDevices
```
확인된 Line-in 장치 번호(예: ID 3)를 지정하여 오디오 캡처를 시작합니다:
```powershell
powershell scripts\run_agent.ps1 -Device 3
```
*(장치 번호를 생략하면 Windows 기본 입력 장치로 자동 실행됩니다)*

---

## 5. 테스트 실행 방법

전체 단위 및 통합 테스트를 한 번에 검증할 수 있습니다:
```powershell
powershell scripts\test_all.ps1
```

개별 테스트 실행:
1. **PII 마스킹 및 보안 용어 사전 테스트**:
   ```bash
   python tests/test_pii_and_terms.py
   ```
2. **VAD 및 음성 구간 분할 테스트**:
   ```bash
   python tests/test_vad.py
   ```
3. **Mock CRM 저장 및 중복 방지 테스트**:
   ```bash
   python tests/test_mock_crm.py
   ```
4. **FastAPI 서버 및 Faster-Whisper GPU 초기화 테스트**:
   ```bash
   python tests/test_server_init.py
   ```
5. **Ollama LLM 실시간 상담 분석 테스트**:
   ```bash
   python tests/test_ollama.py
   ```

---

## 6. 보안 및 감사 규정

- **오디오 영구 저장 금지**: 정책 승인이 없는 한 통화 음성 파일은 디스크에 저장되지 않습니다.
- **비식별 조치**: 주민등록번호(6자리-*******), 휴대전화번호(010-****-****), 카드번호(****-****-****-XXXX) 마스킹이 STT 단계에서 즉시 적용됩니다.
- **감사 로그(Audit Trail)**: CRM 저장, 수정, 다운로드 이력은 `data/crm_records/crm_audit.log`에 일시, 상담사 ID, 세션 ID와 함께 암호화 및 무결성 검증 가능한 형태로 기록됩니다.
