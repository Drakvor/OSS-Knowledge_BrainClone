# Build stage
FROM node:18-alpine AS build-stage

# 작업 디렉토리 설정
WORKDIR /app

# 빌드 단계에서는 개발 환경으로 설정
ENV NODE_ENV=development
ENV CI=true

# 빌드 시점에 환경변수 주입 (ARG로 받아서 ENV로 설정)
ARG VITE_API_BASE_URL=http://oss-knowledge-meta-api-dev.4.230.158.187.nip.io
ARG VITE_EMBEDDING_API_BASE_URL=http://oss-knowledge-embedding-dev.4.230.158.187.nip.io
ARG VITE_SEARCH_API_BASE_URL=http://oss-knowledge-search-dev.4.230.158.187.nip.io

ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_EMBEDDING_API_BASE_URL=$VITE_EMBEDDING_API_BASE_URL
ENV VITE_SEARCH_API_BASE_URL=$VITE_SEARCH_API_BASE_URL

# 의존성 캐싱을 위해 package 파일 먼저 복사
COPY package*.json ./

# 모든 의존성 설치 (devDependencies 포함)
RUN npm ci --no-audit --no-fund

# 소스 코드 복사
COPY . .

# 프로덕션 빌드 실행
RUN npm run build

# 빌드 결과물 크기 확인
RUN ls -la dist/ && du -sh dist/

# Production stage
FROM nginx:1.24-alpine AS production-stage

# 보안을 위한 사용자 추가
RUN addgroup -g 1001 -S nginx-custom && \
    adduser -S nginx-custom -u 1001

# 빌드된 애플리케이션을 nginx 디렉토리로 복사
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Nginx 설정 파일 복사
COPY nginx.conf /etc/nginx/nginx.conf

# 권한 설정
RUN chown -R nginx-custom:nginx-custom /usr/share/nginx/html && \
    chown -R nginx-custom:nginx-custom /var/cache/nginx && \
    chown -R nginx-custom:nginx-custom /etc/nginx/conf.d && \
    chmod -R 755 /usr/share/nginx/html

# 비root 사용자로 실행
USER nginx-custom

# 포트 노출
EXPOSE 8080

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# nginx 실행
CMD ["nginx", "-g", "daemon off;"]