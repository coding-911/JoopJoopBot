# Builder stage
FROM node:18-slim as builder

WORKDIR /build

# pnpm 설치
RUN npm install -g pnpm

# 의존성 파일 복사
COPY services/frontend/package.json services/frontend/pnpm-lock.yaml ./

# 의존성 설치 (--no-frozen-lockfile 옵션으로 변경)
RUN pnpm install

# 소스 코드 복사
COPY services/frontend/src ./src
COPY services/frontend/public ./public
COPY services/frontend/index.html \
     services/frontend/vite.config.ts \
     services/frontend/tsconfig.json \
     services/frontend/tsconfig.node.json \
     services/frontend/env.d.ts \
     ./

# 환경 변수 설정
ARG VITE_API_URL
ARG VITE_PORT
ENV VITE_API_URL=${VITE_API_URL:-http://localhost:18000}
ENV VITE_PORT=${VITE_PORT:-18173}

# 빌드
RUN pnpm run build

# Production stage
FROM node:18-slim

WORKDIR /app

# pnpm 설치
RUN npm install -g pnpm

# 개발 의존성 제외하고 프로덕션 의존성만 설치
COPY services/frontend/package.json services/frontend/pnpm-lock.yaml ./
RUN pnpm install --prod

# 빌드 결과물 복사
COPY --from=builder /build/dist ./dist

# Vite 설정 파일 복사
COPY services/frontend/vite.config.ts ./

# 환경 변수 설정
ARG VITE_API_URL
ARG VITE_PORT
ENV VITE_API_URL=${VITE_API_URL:-http://localhost:18000}
ENV VITE_PORT=${VITE_PORT:-18173}

# 프로덕션 서버 실행
CMD ["pnpm", "run", "preview", "--host"] 