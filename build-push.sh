#!/bin/bash
set -euo pipefail

# Build and Push Docker Images for WOO
# Usage: ./build-push.sh [--push] [--version VERSION]

# Default values
PUSH=false
API_VERSION="${API_VERSION:-latest}"
FRONTEND_VERSION="${FRONTEND_VERSION:-latest}"
REGISTRY="${REGISTRY:-ghcr.io}"

# Determine owner (priority: env var > hardcoded default)
if [ -n "${GITHUB_REPOSITORY_OWNER:-}" ]; then
    OWNER=$(echo "$GITHUB_REPOSITORY_OWNER" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
elif [ -n "${GITHUB_USERNAME:-}" ]; then
    OWNER=$(echo "$GITHUB_USERNAME" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
elif [ -n "${OWNER:-}" ]; then
    # OWNER already set, keep it
    OWNER="$OWNER"
else
    # Default to gradient-ds organization
    OWNER="gradient-ds"
fi

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --push)
            PUSH=true
            shift
            ;;
        --version)
            API_VERSION="$2"
            FRONTEND_VERSION="$2"
            shift 2
            ;;
        --api-version)
            API_VERSION="$2"
            shift 2
            ;;
        --frontend-version)
            FRONTEND_VERSION="$2"
            shift 2
            ;;
        --owner)
            OWNER="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--push] [--version VERSION] [--api-version VERSION] [--frontend-version VERSION] [--owner OWNER]"
            exit 1
            ;;
    esac
done

# Image names
API_IMAGE="${REGISTRY}/${OWNER}/woo-api"
FRONTEND_IMAGE="${REGISTRY}/${OWNER}/woo-frontend"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Building WOO Docker Images"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Registry:          ${REGISTRY}"
echo "Owner:             ${OWNER}"
echo "API Version:       ${API_VERSION}"
echo "Frontend Version:  ${FRONTEND_VERSION}"
echo "Push to registry:  ${PUSH}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Build API image
echo "📦 Building API image..."
docker build \
    -t "${API_IMAGE}:${API_VERSION}" \
    -t "${API_IMAGE}:latest" \
    -f backend/Dockerfile \
    ./backend

echo "✅ API image built: ${API_IMAGE}:${API_VERSION}"
echo ""

# Build Frontend image
echo "📦 Building Frontend image..."
docker build \
    -t "${FRONTEND_IMAGE}:${FRONTEND_VERSION}" \
    -t "${FRONTEND_IMAGE}:latest" \
    -f frontend/Dockerfile \
    ./frontend

echo "✅ Frontend image built: ${FRONTEND_IMAGE}:${FRONTEND_VERSION}"
echo ""

# Push if requested
if [ "$PUSH" = true ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Pushing images to registry..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    echo "⬆️  Pushing API image..."
    docker push "${API_IMAGE}:${API_VERSION}"
    docker push "${API_IMAGE}:latest"
    echo "✅ API image pushed"
    echo ""
    
    echo "⬆️  Pushing Frontend image..."
    docker push "${FRONTEND_IMAGE}:${FRONTEND_VERSION}"
    docker push "${FRONTEND_IMAGE}:latest"
    echo "✅ Frontend image pushed"
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Done!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Built images:"
echo "  ${API_IMAGE}:${API_VERSION}"
echo "  ${FRONTEND_IMAGE}:${FRONTEND_VERSION}"

if [ "$PUSH" = false ]; then
    echo ""
    echo "To push images to registry, run:"
    echo "  $0 --push"
    echo ""
    echo "Or push manually:"
    echo "  docker push ${API_IMAGE}:${API_VERSION}"
    echo "  docker push ${FRONTEND_IMAGE}:${FRONTEND_VERSION}"
fi

echo ""

