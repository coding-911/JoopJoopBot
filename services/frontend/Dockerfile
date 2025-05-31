FROM node:18-slim

WORKDIR /app

# pnpm 설치
RUN npm install -g pnpm

# 의존성 파일 복사
COPY services/web/package.json services/web/pnpm-lock.yaml ./

# 의존성 설치
RUN pnpm install

# 소스 코드 복사
COPY services/web/src ./src
COPY services/web/index.html services/web/vite.config.ts services/web/tsconfig.json services/web/tsconfig.node.json ./

# 개발 서버 실행
CMD ["pnpm", "run", "dev", "--host"] 