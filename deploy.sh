#!/bin/bash
# H3 Auctions Deployment Script for Hostinger VPS
# Run this script on your VPS after uploading files

set -e  # Exit on error

echo "🚀 Starting H3 Auctions Deployment..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found!${NC}"
    echo "Please create .env file with your configuration."
    exit 1
fi

echo -e "${YELLOW}📦 Activating virtual environment...${NC}"
source venv/bin/activate

echo -e "${YELLOW}📥 Installing/updating dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${YELLOW}🗄️  Running database migrations...${NC}"
python manage.py migrate

echo -e "${YELLOW}📁 Collecting static files...${NC}"
python manage.py collectstatic --noinput

echo -e "${YELLOW}✅ Checking Django configuration...${NC}"
python manage.py check

echo -e "${GREEN}✅ Deployment preparation complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Configure Nginx (see DEPLOYMENT.md)"
echo "2. Configure Supervisor (see DEPLOYMENT.md)"
echo "3. Set up SSL certificate"
echo "4. Restart services: sudo supervisorctl restart h3auctions"

