#!/bin/bash
set -euo pipefail

# Build and Push Docker Images for WOO
# Usage: ./build-push.sh [--push] [--version VERSION]

# Default values
PUSH=false
API_VERSION="${API_VERSION:-latest}"
FRONTEND_VERSION="${FRONTEND_VERSION:-latest}"
REGISTRY="${REGISTRY:-ghcr.io}"
PLATFORMS="${PLATFORMS:-linux/amd64,linux/arm64}"

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
echo "Platforms:         ${PLATFORMS}"
echo "Push to registry:  ${PUSH}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Setup buildx if not already configured
echo "🔧 Setting up Docker Buildx..."
if ! docker buildx inspect woo-builder >/dev/null 2>&1; then
    echo "Creating new buildx builder 'woo-builder'..."
    docker buildx create --name woo-builder --driver docker-container --bootstrap --use
else
    echo "Using existing buildx builder 'woo-builder'..."
    docker buildx use woo-builder
fi
echo ""

# Determine build action based on push flag
if [ "$PUSH" = true ]; then
    BUILD_ACTION="--push"
    echo "📦 Building and pushing multi-arch images..."
else
    BUILD_ACTION="--load"
    echo "📦 Building images locally (single arch)..."
    echo "⚠️  Note: Local builds only support current platform."
    echo "    Use --push to build multi-arch and push to registry."
    PLATFORMS="linux/$(uname -m | sed 's/x86_64/amd64/' | sed 's/aarch64/arm64/')"
fi
echo ""

# Build API image
echo "📦 Building API image for ${PLATFORMS}..."
docker buildx build \
    --platform "${PLATFORMS}" \
    -t "${API_IMAGE}:${API_VERSION}" \
    -t "${API_IMAGE}:latest" \
    -f backend/Dockerfile \
    ${BUILD_ACTION} \
    ./backend

echo "✅ API image built: ${API_IMAGE}:${API_VERSION}"
echo ""

# Build Frontend image
echo "📦 Building Frontend image for ${PLATFORMS}..."
docker buildx build \
    --platform "${PLATFORMS}" \
    -t "${FRONTEND_IMAGE}:${FRONTEND_VERSION}" \
    -t "${FRONTEND_IMAGE}:latest" \
    -f frontend/Dockerfile \
    ${BUILD_ACTION} \
    ./frontend

echo "✅ Frontend image built: ${FRONTEND_IMAGE}:${FRONTEND_VERSION}"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Done!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$PUSH" = true ]; then
    echo "Pushed multi-arch images (${PLATFORMS}):"
    echo "  ${API_IMAGE}:${API_VERSION}"
    echo "  ${FRONTEND_IMAGE}:${FRONTEND_VERSION}"
    echo ""
    echo "These images are now available for both amd64 (x86_64) and arm64 (Apple Silicon)."
else
    echo "Built images locally for current platform:"
    echo "  ${API_IMAGE}:${API_VERSION}"
    echo "  ${FRONTEND_IMAGE}:${FRONTEND_VERSION}"
    echo ""
    echo "To build and push multi-arch images to registry, run:"
    echo "  $0 --push"
fi

echo ""

