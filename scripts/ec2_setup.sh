#!/bin/bash
# ================================================================
# EC2 Instance Bootstrap Script
# Run this ONCE on a fresh Amazon Linux 2023 / Ubuntu EC2 instance
# Usage: chmod +x ec2_setup.sh && sudo ./ec2_setup.sh
# ================================================================

set -e

echo "======================================"
echo "  ClaimShield AI — EC2 Setup"
echo "======================================"

# 1. System updates
echo "[1/6] Updating system packages..."
if command -v yum &> /dev/null; then
    sudo yum update -y
    sudo yum install -y git docker
elif command -v apt-get &> /dev/null; then
    sudo apt-get update -y
    sudo apt-get install -y git docker.io docker-compose-plugin curl
fi

# 2. Install Docker Compose (if not included)
echo "[2/6] Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    COMPOSE_VERSION="v2.24.0"
    sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" \
        -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# 3. Start Docker
echo "[3/6] Starting Docker service..."
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# 4. Clone the repository
echo "[4/6] Cloning repository..."
cd /home/$(whoami)
if [ ! -d "health_claims_project" ]; then
    git clone https://github.com/varshith19-ctrl/health_claims.git health_claims_project
fi
cd health_claims_project

# 5. Create .env file (EDIT THESE VALUES)
echo "[5/6] Creating .env file..."
if [ ! -f .env ]; then
    cat > .env << 'EOF'
# OpenAI
OPENAI_API_KEY=your-openai-api-key

# AWS S3
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=health-claims-bny-2026
STORAGE_BACKEND=s3

# API
API_TOKEN=health-claims-secret-token
EOF
    echo "  ⚠️  IMPORTANT: Edit .env with your actual keys!"
    echo "     nano /home/$(whoami)/health_claims_project/.env"
fi

# 6. Build and start
echo "[6/6] Building and starting containers..."
docker compose build
docker compose up -d

echo ""
echo "======================================"
echo "  ✅ Setup Complete!"
echo "======================================"
echo ""
echo "  API:       http://$(curl -s ifconfig.me):8000"
echo "  Frontend:  http://$(curl -s ifconfig.me):8000"
echo "  Health:    http://$(curl -s ifconfig.me):8000/api/health"
echo ""
echo "  Next steps:"
echo "    1. Edit .env with your actual API keys"
echo "    2. docker compose restart"
echo "    3. Configure Security Group: allow ports 8000, 22"
echo "    4. (Optional) Allocate an Elastic IP"
echo ""
