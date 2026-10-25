#!/usr/bin/env bash
# ==============================================================================
# 118 팔배개 (118 PAL-BEGAE) - WSL2 Ubuntu 환경 자동 설치 스크립트
# 한국인터넷진흥원(KISA) 118 AI 상담지원 시스템
# ==============================================================================

set -e

echo "============================================================"
echo " [118 팔배개] WSL2 Ubuntu + RTX 5080 환경 설치 시작"
echo "============================================================"

# 1. 시스템 패키지 업데이트 및 오디오/C++ 의존성 설치
sudo apt-get update
sudo apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    ffmpeg \
    libsndfile1 \
    portaudio19-dev \
    curl \
    git \
    build-essential

# 2. 가상환경 생성 및 활성화
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$WORKSPACE_ROOT"

if [ ! -d "venv" ]; then
    echo "가상환경(venv) 생성 중..."
    python3.11 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip

# 3. Python 의존성 설치
echo "Python 의존성 설치 중..."
pip install -r requirements.txt

# 4. 디렉터리 생성
mkdir -p data/crm_records data/whisper_models

# 5. WSL2에서 Windows 호스트 IP 확인 및 .env 설정 안내
WIN_HOST_IP=$(ip route | grep default | awk '{print $3}')
echo "------------------------------------------------------------"
echo "Windows 호스트 IP 주소 감지됨: $WIN_HOST_IP"
echo "WSL2에서 호스트 Ollama 접근 시: http://$WIN_HOST_IP:11434"
echo "============================================================"
echo " [118 팔배개] WSL2 환경 설치가 완료되었습니다."
echo " 실행 방법: source venv/bin/activate && uvicorn server.main:app --host 0.0.0.0 --port 8000"
echo "============================================================"
