# Frontend Dockerfile for WOO
# Multi-stage build: Build stage + Production stage with Nginx

# Build stage
FROM node:20-alpine as builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production=false

# Copy source code
COPY . .

# Build argument for backend URL (can be overridden at build time)
ARG VITE_APP_FLASK_BACKEND_URL=/api
ENV VITE_APP_FLASK_BACKEND_URL=$VITE_APP_FLASK_BACKEND_URL

# Build the application
RUN npm run build

# Production stage
FROM node:20-alpine

# Install serve for serving static files
RUN npm install -g serve

# Set working directory
WORKDIR /app

# Copy built files from builder (node user already exists in alpine image with uid 1000)
COPY --from=builder --chown=node:node /app/dist ./dist

# Switch to non-root user (node user is built-in)
USER node

# Expose port (must match docker-compose)
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# Serve the application
CMD ["serve", "-s", "dist", "-l", "3000"]

