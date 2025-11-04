#!/bin/bash

# Docker 실행 스크립트

echo "=== Weather Data Collection Docker 실행 ==="

# Docker 이미지 빌드
echo "1. Docker 이미지 빌드 중..."
docker build -t weather-data-collector .

# 데이터 디렉토리 생성
echo "2. 데이터 디렉토리 생성 중..."
mkdir -p data/nas-weather-data

# Docker Compose로 실행
echo "3. Docker Compose로 서비스 시작 중..."
docker-compose -f docker-compose.simple.yml up -d

echo "=== 실행 완료 ==="
echo "서비스 상태 확인: docker-compose -f docker-compose.simple.yml ps"
echo "로그 확인: docker-compose -f docker-compose.simple.yml logs -f"
echo "서비스 중지: docker-compose -f docker-compose.simple.yml down"
