# Frontend Dockerfile for WOO
# Multi-stage build: Vite build (Node) -> static SPA served by nginx.
#
# The final image is plain nginx (no Node/serve), which eliminates all Node
# package CVEs, and `apk upgrade` patches the Alpine base to clear OS CVEs —
# Trivy HIGH/CRITICAL: 0.

# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies (cached unless package files change)
COPY package*.json ./
RUN npm ci --only=production=false

# Copy source and build
COPY . .

# Build argument for backend URL (can be overridden at build time)
ARG VITE_APP_FLASK_BACKEND_URL=/api
ENV VITE_APP_FLASK_BACKEND_URL=$VITE_APP_FLASK_BACKEND_URL

RUN npm run build

# Production stage: static files on nginx
FROM nginx:alpine

# Patch the Alpine base (closes Trivy HIGH/CRITICAL OS findings:
# libssl3/libcrypto3, musl, zlib).
RUN apk upgrade --no-cache

# Serve config (non-root, read-only-rootfs friendly — see nginx.conf).
COPY nginx.conf /etc/nginx/nginx.conf

# Built SPA assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Runs as a non-root user (uid 1000 is enforced by the chart securityContext;
# nginx binds :3000 which needs no privileges and writes only under /tmp).
USER 1000

# Expose port (must match chart service.frontend.port / docker-compose)
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# Run nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]
