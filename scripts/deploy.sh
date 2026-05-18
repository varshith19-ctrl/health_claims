#!/bin/bash
# ================================================================
# Deploy Script — Pulls latest code and restarts on EC2
# Usage: ./scripts/deploy.sh <EC2_HOST> <SSH_KEY_PATH>
# Example: ./scripts/deploy.sh 54.123.45.67 ~/.ssh/health-claims.pem
# ================================================================

set -e

EC2_HOST="${1:?Usage: deploy.sh <EC2_HOST> <SSH_KEY_PATH>}"
SSH_KEY="${2:?Usage: deploy.sh <EC2_HOST> <SSH_KEY_PATH>}"
EC2_USER="${3:-ec2-user}"
PROJECT_DIR="/home/${EC2_USER}/health_claims_project"

echo "======================================"
echo "  Deploying to ${EC2_HOST}"
echo "======================================"

ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "${EC2_USER}@${EC2_HOST}" << REMOTE
    set -e
    cd ${PROJECT_DIR}
    echo "[1/3] Pulling latest code..."
    git pull origin main
    echo "[2/3] Building Docker image..."
    docker compose build --no-cache
    echo "[3/3] Restarting containers..."
    docker compose down
    docker compose up -d
    echo "✅ Deployment complete!"
    docker compose ps
REMOTE

echo ""
echo "  ✅ Deployed successfully!"
echo "  Frontend: http://${EC2_HOST}:8000"
echo "  API:      http://${EC2_HOST}:8000/api/health"
