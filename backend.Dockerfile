FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential pkg-config curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN pip install "uv>=0.4.0"

WORKDIR /app
COPY backend/pyproject.toml ./
COPY backend/uv.lock* ./
RUN uv sync --no-cache 2>/dev/null || (echo "uv sync failed, installing dependencies..." && uv pip install --system fastapi uvicorn python-jose passlib python-multipart redis pandas)

COPY backend/ ./

# NAS 데이터 마운트 포인트 (docker-compose.yml에서 볼륨 마운트)
# WEATHER_DATA_PATH 환경변수가 설정되지 않으면 기본적으로 /nas-weather-data 사용
ENV WEATHER_DATA_PATH=/nas-weather-data

EXPOSE 8081
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8081"]
