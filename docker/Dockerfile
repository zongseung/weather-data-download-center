FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 데이터 디렉토리 생성 (이미 존재할 수 있음)
RUN mkdir -p data/nas-weather-data || true

# 실행 권한 부여
RUN chmod +x *.py
RUN chmod +x src/scripts/*.py

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# 기본 명령어 (데이터 수집) - 절대 경로로 실행
CMD ["python3", "/app/src/scripts/run_collection.py"]

