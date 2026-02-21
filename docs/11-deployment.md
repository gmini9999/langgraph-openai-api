# 11. 배포

## 개요

`langgraph-openai-api` 기반 서비스의 Docker 빌드, docker-compose 구성,
프로덕션 체크리스트, 클라우드 배포 방법을 정의합니다.

---

## Docker 빌드

### openlang build 사용

```bash
# 기본 빌드
openlang build

# 커스텀 태그
openlang build -t my-api:v1.0

# 플랫폼 지정
openlang build --platform linux/amd64
```

> **상세**: [10. CLI 레퍼런스](./10-cli-reference.md#openlang-build) 참조

### 수동 Dockerfile

직접 Dockerfile을 작성할 수도 있습니다.

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# langgraph-openai-api 설치
RUN pip install --no-cache-dir langgraph-openai-api

# 프로젝트 파일 복사
COPY . .

# 포트 노출
EXPOSE 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/v1/models || exit 1

# 프로덕션 서버 실행
CMD ["openlang", "serve", "--host", "0.0.0.0", "--port", "8000"]
```

### 빌드 및 실행

```bash
# 빌드
docker build -t my-langgraph-api:latest .

# 실행
docker run -d \
  --name langgraph-api \
  -p 8000:8000 \
  -e OPENLANG_API_KEY=sk-my-secret-key \
  -e OPENAI_API_KEY=sk-... \
  my-langgraph-api:latest
```

---

## docker-compose

### 기본 구성

```yaml
# docker-compose.yml

services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - OPENLANG_API_KEY=${OPENLANG_API_KEY}
      - OPENLANG_HOST=0.0.0.0
      - OPENLANG_PORT=8000
      - OPENLANG_WORKERS=2
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/v1/models"]
      interval: 30s
      timeout: 5s
      retries: 3
```

### 외부 DB 포함 구성

```yaml
# docker-compose.yml

services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      postgres:
        condition: service_healthy
      qdrant:
        condition: service_healthy
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: langgraph
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: langgraph
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U langgraph"]
      interval: 10s
      timeout: 5s
      retries: 5

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/healthz"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  qdrant_data:
```

### 실행

```bash
# 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f api

# 종료
docker-compose down
```

---

## 프로덕션 체크리스트

### 필수 항목

| 항목 | 설명 | 확인 |
|------|------|------|
| API 키 설정 | `OPENLANG_API_KEY` 환경변수 설정 | [ ] |
| HTTPS | TLS 인증서 적용 (리버스 프록시 또는 클라우드 LB) | [ ] |
| 환경변수 보안 | `.env` 파일 gitignore, 시크릿 매니저 사용 | [ ] |
| 헬스체크 | `/v1/models` 엔드포인트 헬스체크 설정 | [ ] |
| 로깅 | 구조화 로깅 설정, API 키 마스킹 | [ ] |
| 리소스 제한 | 컨테이너 CPU/메모리 리밋 설정 | [ ] |

### 권장 항목

| 항목 | 설명 | 확인 |
|------|------|------|
| 워커 수 | CPU 코어 수에 맞는 `--workers` 설정 | [ ] |
| CORS | 허용 오리진 설정 | [ ] |
| 레이트 리밋 | 요청 제한 설정 (리버스 프록시 레벨) | [ ] |
| 모니터링 | 메트릭 수집 (Prometheus 등) | [ ] |
| 백업 | 체크포인트/스토리지 백업 전략 | [ ] |
| 자동 확장 | 부하에 따른 인스턴스 스케일링 | [ ] |

---

## 리버스 프록시 (Nginx)

```nginx
# nginx.conf

upstream langgraph_api {
    server 127.0.0.1:8000;
}

server {
    listen 443 ssl;
    server_name api.example.com;

    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;

    # SSE 스트리밍을 위한 설정
    proxy_buffering off;
    proxy_cache off;

    location /v1/ {
        proxy_pass http://langgraph_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 스트리밍 지원
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
        proxy_read_timeout 300s;
    }
}
```

> SSE 스트리밍을 위해 `proxy_buffering off`와 `chunked_transfer_encoding off` 설정이 필수입니다.

---

## 클라우드 배포

### AWS ECS / Fargate

```bash
# ECR에 이미지 푸시
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin <account>.dkr.ecr.ap-northeast-2.amazonaws.com

docker tag my-langgraph-api:latest <account>.dkr.ecr.ap-northeast-2.amazonaws.com/langgraph-api:latest
docker push <account>.dkr.ecr.ap-northeast-2.amazonaws.com/langgraph-api:latest
```

ECS 태스크 정의 핵심 설정:

| 항목 | 값 |
|------|-----|
| 이미지 | ECR 이미지 URI |
| 포트 | 8000 |
| 환경변수 | Secrets Manager에서 주입 |
| 헬스체크 | `GET /v1/models` |
| CPU | 최소 512 (0.5 vCPU) |
| 메모리 | 최소 1024 MB |

### GCP Cloud Run

```bash
# 이미지 빌드 및 푸시
gcloud builds submit --tag gcr.io/<project>/langgraph-api

# 서비스 배포
gcloud run deploy langgraph-api \
  --image gcr.io/<project>/langgraph-api \
  --port 8000 \
  --set-env-vars OPENLANG_API_KEY=sk-... \
  --set-env-vars OPENAI_API_KEY=sk-... \
  --min-instances 1 \
  --max-instances 10 \
  --memory 1Gi \
  --cpu 1 \
  --region asia-northeast3
```

### Azure Container Apps

```bash
az containerapp create \
  --name langgraph-api \
  --resource-group my-rg \
  --image my-registry.azurecr.io/langgraph-api:latest \
  --target-port 8000 \
  --ingress external \
  --env-vars OPENLANG_API_KEY=sk-... OPENAI_API_KEY=sk-... \
  --min-replicas 1 \
  --max-replicas 10 \
  --cpu 1 \
  --memory 2Gi
```

---

## 환경별 설정 요약

| 환경 | 명령어 | 인증 | 리로드 | 워커 | HTTPS |
|------|--------|------|--------|------|-------|
| 로컬 개발 | `openlang dev` | Off | On | 1 | 불필요 |
| 스테이징 | `openlang serve` | On | Off | 2 | 권장 |
| 프로덕션 | `openlang serve` | On | Off | CPU 수 | 필수 |
| Docker | `openlang serve` | On | Off | 설정 | LB에서 |

---

## 관련 문서

- [10. CLI 레퍼런스](./10-cli-reference.md) - build/serve 명령어 상세
- [09. 인증](./09-authentication.md) - API 키 설정
- [03. 설정](./03-configuration.md) - 환경변수 설정
- [Appendix A. 환경변수](./appendix/A-environment-variables.md) - 배포 관련 환경변수
- [Appendix D. 트러블슈팅](./appendix/D-troubleshooting.md) - 배포 문제 해결
