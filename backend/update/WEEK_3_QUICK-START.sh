#!/bin/bash

# GitHub Codespaces - One-Click Setup Script
# Run this ONCE when you first create your Codespace

set -e  # Exit on error

echo "========================================"
echo "🚀 GitHub Codespaces Setup for Week 3"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if we're in Codespaces
if [ -z "$CODESPACES" ]; then
    echo -e "${YELLOW}⚠️  Warning: This script is designed for GitHub Codespaces${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 1: Install PostgreSQL
echo -e "${YELLOW}📦 Step 1/7: Installing PostgreSQL...${NC}"
sudo apt-get update -qq > /dev/null 2>&1
sudo apt-get install -y postgresql postgresql-contrib > /dev/null 2>&1
echo -e "${GREEN}✅ PostgreSQL installed${NC}"

# Step 2: Install Redis
echo -e "${YELLOW}📦 Step 2/7: Installing Redis...${NC}"
sudo apt-get install -y redis-server > /dev/null 2>&1
echo -e "${GREEN}✅ Redis installed${NC}"

# Step 3: Start services
echo -e "${YELLOW}▶️  Step 3/7: Starting services...${NC}"
sudo service postgresql start > /dev/null 2>&1
sudo service redis-server start > /dev/null 2>&1
sleep 2
echo -e "${GREEN}✅ Services started${NC}"

# Step 4: Create database
echo -e "${YELLOW}🗄️  Step 4/7: Creating database...${NC}"
sudo -u postgres psql -c "CREATE DATABASE research_db;" > /dev/null 2>&1 || echo "  (Database already exists)"
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';" > /dev/null 2>&1
echo -e "${GREEN}✅ Database 'research_db' ready${NC}"

# Step 5: Create .env file
echo -e "${YELLOW}⚙️  Step 5/7: Creating .env file...${NC}"
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/research_db

# Redis
REDIS_URL=redis://localhost:6379

# API Settings
API_V1_PREFIX=/api/v1

# Optional: External APIs
SEMANTIC_SCHOLAR_API_KEY=
OPENALEX_EMAIL=your-email@example.com

# CORS for Codespaces
CORS_ORIGINS=["http://localhost:3000","https://*.githubpreview.dev","https://*.github.dev"]
EOF
    echo -e "${GREEN}✅ .env file created${NC}"
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi

# Step 6: Install Python dependencies
echo -e "${YELLOW}🐍 Step 6/7: Installing Python dependencies...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "${GREEN}✅ Python dependencies installed${NC}"

# Step 7: Initialize database
echo -e "${YELLOW}📊 Step 7/7: Initializing database tables...${NC}"
python3 << 'PYTHON'
try:
    from app.core.database import init_db
    init_db()
    print("✅ Database tables created")
except Exception as e:
    print(f"❌ Error: {e}")
PYTHON

# Verify services
echo ""
echo "========================================"
echo "🧪 Verifying Installation"
echo "========================================"

# Check PostgreSQL
echo -n "PostgreSQL: "
if sudo service postgresql status | grep -q "online"; then
    echo -e "${GREEN}✅ Running${NC}"
else
    echo -e "${RED}❌ Not running${NC}"
fi

# Check Redis
echo -n "Redis: "
if redis-cli ping 2>/dev/null | grep -q "PONG"; then
    echo -e "${GREEN}✅ Running${NC}"
else
    echo -e "${RED}❌ Not running${NC}"
fi

# Check database
echo -n "Database: "
if sudo -u postgres psql -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw research_db; then
    echo -e "${GREEN}✅ Created${NC}"
else
    echo -e "${RED}❌ Not found${NC}"
fi

# Check Python environment
echo -n "Python venv: "
if [ -d "venv" ]; then
    echo -e "${GREEN}✅ Created${NC}"
else
    echo -e "${RED}❌ Not found${NC}"
fi

# Final summary
echo ""
echo "========================================"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "========================================"
echo ""
echo "📝 Next steps:"
echo ""
echo "  1. Activate Python environment:"
echo -e "     ${YELLOW}source venv/bin/activate${NC}"
echo ""
echo "  2. Run tests:"
echo -e "     ${YELLOW}python tests/test_search.py${NC}"
echo ""
echo "  3. Start the API:"
echo -e "     ${YELLOW}uvicorn app.main:app --reload --host 0.0.0.0 --port 8000${NC}"
echo ""
echo "  4. Open in browser (Codespaces will show a popup)"
echo -e "     ${YELLOW}http://localhost:8000/docs${NC}"
echo ""
echo "💡 Tip: Services stop when Codespace sleeps. Restart with:"
echo -e "   ${YELLOW}sudo service postgresql start && sudo service redis-server start${NC}"
echo ""
echo "🎉 Happy coding!"