from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import nas_data

app = FastAPI(
    title="Weather Data API",
    description="NAS 또는 Google Drive의 기상 CSV 파일 제공 API",
    version="0.1.0"
)

# CORS 설정
origins = [
    "http://localhost:3000",   # Next.js dev 환경
    "http://127.0.0.1:3000",
    "http://localhost:8080",   # Docker frontend
    "http://127.0.0.1:8080",
    "http://localhost",        # Nginx reverse proxy
    "http://127.0.0.1",
]

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
