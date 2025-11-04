from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import nas_data
import os

app = FastAPI(
    title="Weather Data API",
    description="NAS 또는 Google Drive의 기상 CSV 파일 제공 API",
    version="0.1.0"
)

# CORS 설정
# 환경변수에서 허용할 origin을 가져오거나 기본값 사용
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    # 쉼표로 구분된 여러 origin 지원
    origins = [origin.strip() for origin in allowed_origins_env.split(",")]
else:
    # 기본값: localhost 및 환경변수로 추가된 IP들
    origins = [
        "http://localhost:3000",   # Next.js dev 환경
        "http://127.0.0.1:3000",
        "http://localhost:8080",   # Docker frontend
        "http://127.0.0.1:8080",
        "http://localhost",        # Nginx reverse proxy
        "http://127.0.0.1",
    ]
    # 추가로 환경변수로 지정된 IP들 추가
    additional_origins = os.getenv("ADDITIONAL_ORIGINS", "")
    if additional_origins:
        origins.extend([origin.strip() for origin in additional_origins.split(",")])

# 모든 origin 허용 옵션 (개발 환경용, 프로덕션에서는 사용 비권장)
if os.getenv("CORS_ALLOW_ALL", "").lower() == "true":
    origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# ✅ API 라우터 추가
app.include_router(nas_data.router)
