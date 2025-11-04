# Docker 설정 가이드

이 문서는 기상 데이터 플랫폼을 Docker로 실행하는 방법을 설명합니다.

## 🎯 주요 변경사항

### 기존 (Google Drive)
- Google Drive 경로에서 단기예보 데이터만 제공
- 경로: `/Users/ijongseung/Library/CloudStorage/GoogleDrive-solution.hkn@gmail.com/내 드라이브/단기예보`

### 현재 (NAS 마운트)
- NAS에서 3가지 예보 유형 데이터 모두 제공
- 경로: `/Volumes/nas-weather-data/`
  - `단기예보/`
  - `초단기예보/`
  - `초단기실황/`

## 🚀 실행 방법

### 1. NAS 마운트 확인
먼저 NAS가 올바르게 마운트되어 있는지 확인하세요:
```bash
ls /Volumes/nas-weather-data/
# 출력: 단기예보  초단기예보  초단기실황
```

### 2. Docker Compose로 실행
```bash
# 프로젝트 루트에서
cd docker

# 빌드 및 실행
docker-compose up -d --build

# 로그 확인 (실시간)
docker-compose logs -f

# 특정 서비스만 로그 확인
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 3. 서비스 확인
- 프론트엔드: http://localhost:3000
- 백엔드 API: http://localhost:8081
- API 문서: http://localhost:8081/docs
- NAS 정보: http://localhost:3000/nas-info

### 4. 중지 및 제거
```bash
# 중지
docker-compose down

# 컨테이너, 네트워크, 볼륨 모두 제거
docker-compose down -v

# 이미지까지 제거
docker-compose down --rmi all
```

## 🔧 설정 커스터마이징

### NAS 경로 변경
다른 NAS 경로를 사용하려면 `docker-compose.yml` 파일을 수정하세요:

```yaml
services:
  backend:
    volumes:
      # 여기를 수정
      - /your/custom/nas/path:/nas-weather-data:ro
```

### 포트 변경
기본 포트를 변경하려면:

```yaml
services:
  backend:
    ports:
      - "9000:8081"  # 외부:내부 (외부 포트만 변경)
  
  frontend:
    ports:
      - "4000:3000"  # 외부:내부 (외부 포트만 변경)
    environment:
      - NEXT_PUBLIC_API_BASE_URL=http://localhost:9000  # 백엔드 포트에 맞춰 변경
```

## 🐛 문제 해결

### 1. NAS 마운트 오류
```bash
# NAS가 마운트되어 있는지 확인
mount | grep nas-weather-data

# 수동으로 마운트 (macOS Finder에서)
# Finder > 이동 > 서버에 연결... > NAS 주소 입력
```

### 2. 컨테이너가 시작되지 않음
```bash
# 로그 확인
docker-compose logs backend
docker-compose logs frontend

# 컨테이너 상태 확인
docker-compose ps

# 강제 재빌드
docker-compose build --no-cache
docker-compose up -d
```

### 3. NAS 데이터를 찾을 수 없음
```bash
# 백엔드 컨테이너 내부 확인
docker exec -it weather-data-platform-backend bash

# 컨테이너 내부에서
ls /nas-weather-data/
ls /nas-weather-data/단기예보/
```

### 4. 권한 오류
NAS 볼륨이 읽기 전용(`:ro`)으로 마운트되어 있는지 확인하세요. 쓰기가 필요한 경우:
```yaml
volumes:
  - /Volumes/nas-weather-data:/nas-weather-data  # :ro 제거
```

## 📊 성능 최적화

### 프로덕션 배포
프로덕션 환경에서는 다음 설정을 추가하세요:

```yaml
services:
  backend:
    restart: always  # unless-stopped 대신
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          memory: 512M
  
  frontend:
    restart: always
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
```

### 로깅 설정
```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 🔒 보안 권장사항

1. **읽기 전용 마운트**: NAS를 읽기 전용(`:ro`)으로 마운트하여 실수로 데이터를 변경하는 것을 방지
2. **네트워크 격리**: 필요한 경우 Docker 네트워크를 사용하여 서비스 간 통신 격리
3. **환경변수**: 민감한 정보는 `.env` 파일로 관리 (`.gitignore`에 추가)

## 📝 환경변수 파일 (.env)

프로젝트 루트에 `.env` 파일을 생성하여 설정을 관리할 수 있습니다:

```bash
# .env
NAS_MOUNT_PATH=/Volumes/nas-weather-data
BACKEND_PORT=8081
FRONTEND_PORT=3000
```

그리고 `docker-compose.yml`에서 사용:
```yaml
services:
  backend:
    ports:
      - "${BACKEND_PORT}:8081"
    volumes:
      - ${NAS_MOUNT_PATH}:/nas-weather-data:ro
```

## ✅ 체크리스트

배포 전 확인사항:
- [ ] NAS가 올바르게 마운트되어 있음
- [ ] Docker 및 Docker Compose 설치됨
- [ ] 포트 8081, 3000이 사용 가능함
- [ ] NAS 경로에 읽기 권한이 있음
- [ ] `docker-compose.yml`의 볼륨 경로가 올바름

## 📚 추가 자료

- [Docker 공식 문서](https://docs.docker.com/)
- [Docker Compose 문서](https://docs.docker.com/compose/)
- [FastAPI 배포 가이드](https://fastapi.tiangolo.com/deployment/)
- [Next.js Docker 배포](https://nextjs.org/docs/deployment#docker-image)

