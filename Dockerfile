FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-dev \
    python3-pip \
    libsndfile1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN python3.11 -m pip install --upgrade pip && \
    python3.11 -m pip install --no-cache-dir -r requirements.txt

COPY . .

# 프론트엔드 정적 파일 빌드본 포함
EXPOSE 8000

CMD ["python3.11", "-m", "uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
