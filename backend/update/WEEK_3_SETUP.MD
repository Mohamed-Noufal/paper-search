# GitHub Codespaces Setup Guide

## 🎯 Overview

GitHub Codespaces runs on a Linux VM in the cloud. We'll install PostgreSQL and Redis **inside the Codespace** (not locally).

---

## 🚀 Quick Setup (5 Minutes)

### Step 1: Install PostgreSQL in Codespace

```bash
# Update package list
sudo apt-get update

# Install PostgreSQL
sudo apt-get install -y postgresql postgresql-contrib

# Start PostgreSQL service
sudo service postgresql start

# Check if running
sudo service postgresql status
```

You should see: `postgresql is running`

### Step 2: Install Redis in Codespace

```bash
# Install Redis
sudo apt-get install -y redis-server

# Start Redis service
sudo service redis-server start

# Test Redis
redis-cli ping
```

You should see: `PONG`

### Step 3: Setup PostgreSQL Database

```bash
# Switch to postgres user and create database
sudo -u postgres psql -c "CREATE DATABASE research_db;"

# Create user (optional, for better security)
sudo -u postgres psql -c "CREATE USER research_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE research_db TO research_user;"

# Verify database exists
sudo -u postgres psql -l | grep research_db
```

### Step 4: Update .env File

Create/update your `.env` file in the `backend/` directory:

```env
# Database (using default postgres user for simplicity)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/research_db

# Or if you created research_user:
# DATABASE_URL=postgresql://research_user:your_password@localhost:5432/research_db

# Redis
REDIS_URL=redis://localhost:6379

# API Settings
API_V1_PREFIX=/api/v1

# Optional: External APIs
SEMANTIC_SCHOLAR_API_KEY=
OPENALEX_EMAIL=your-email@example.com

# CORS (add your Codespace URL)
CORS_ORIGINS=["https://*.githubpreview.dev","https://*.github.dev"]
```

### Step 5: Install Python Dependencies

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 6: Initialize Database Tables

```bash
# Still in backend/ with venv activated
python3 -c "from app.core.database import init_db; init_db()"
```

You should see: `✅ Database tables created`

### Step 7: Run Tests

```bash
python tests/test_search.py
```

Expected: All 6 tests pass ✅

### Step 8: Start the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🔧 Troubleshooting Codespaces

### Issue 1: PostgreSQL Not Starting

```bash
# Check status
sudo service postgresql status

# If not running, start it
sudo service postgresql start

# If still issues, check logs
sudo tail -f /var/log/postgresql/postgresql-*-main.log
```

### Issue 2: Redis Not Starting

```bash
# Check if Redis is running
redis-cli ping

# If not, start it
sudo service redis-server start

# Check Redis logs
sudo tail -f /var/log/redis/redis-server.log
```

### Issue 3: Permission Denied (PostgreSQL)

```bash
# Reset postgres user password
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"

# Update .env with correct password
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/research_db
```

### Issue 4: Port Already in Use

```bash
# Check what's using port 8000
sudo lsof -i :8000

# Kill the process
sudo kill -9 <PID>

# Or use different port
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

---

## 🤖 Automated Setup Script for Codespaces

Save this as `setup_codespace.sh` in your backend folder:

```bash
#!/bin/bash

echo "🚀 Setting up Codespace Environment..."

# Install PostgreSQL
echo "📦 Installing PostgreSQL..."
sudo apt-get update -qq
sudo apt-get install -y postgresql postgresql-contrib

# Install Redis
echo "📦 Installing Redis..."
sudo apt-get install -y redis-server

# Start services
echo "▶️  Starting services..."
sudo service postgresql start
sudo service redis-server start

# Setup PostgreSQL database
echo "🗄️  Creating database..."
sudo -u postgres psql -c "CREATE DATABASE research_db;" 2>/dev/null || echo "Database already exists"

# Install Python packages
echo "🐍 Installing Python dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Initialize database
echo "📊 Initializing database tables..."
python3 -c "from app.core.database import init_db; init_db()"

# Test services
echo "🧪 Testing services..."
echo -n "PostgreSQL: "
sudo service postgresql status | grep -q "online" && echo "✅ Running" || echo "❌ Failed"

echo -n "Redis: "
redis-cli ping | grep -q "PONG" && echo "✅ Running" || echo "❌ Failed"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. source venv/bin/activate"
echo "  2. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
```

Run it:
```bash
chmod +x setup_codespace.sh
./setup_codespace.sh
```

---

## 📝 Daily Workflow in Codespaces

Every time you open your Codespace:

```bash
# 1. Navigate to backend
cd backend

# 2. Start services (they stop when Codespace sleeps)
sudo service postgresql start
sudo service redis-server start

# 3. Activate virtual environment
source venv/bin/activate

# 4. Start API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🌐 Accessing Your API

### In Codespaces:

When you run the API, Codespaces will show a popup:
- "Your application running on port 8000 is available"
- Click **"Open in Browser"**

Or manually:
1. Go to **PORTS** tab (next to Terminal)
2. Find port 8000
3. Click the globe icon 🌐

### Your API will be at:
```
https://your-codespace-name-8000.preview.app.github.dev
```

### Test it:
```bash
# Inside Codespace terminal
curl http://localhost:8000/health

# From your browser
https://your-codespace-name-8000.preview.app.github.dev/docs
```

---

## 💾 Data Persistence

**Important:** Data in Codespaces persists, but:

✅ **Persists:**
- Your code
- Database data (PostgreSQL)
- Redis data
- Installed packages

❌ **Resets on rebuild:**
- Running services (need to restart PostgreSQL/Redis)
- Virtual environment (if you rebuild container)

**Pro Tip:** Services stop when Codespace sleeps. Always restart them:
```bash
sudo service postgresql start
sudo service redis-server start
```

---

## 🎯 Verification Checklist

Run these commands to verify everything works:

```bash
# 1. Check PostgreSQL
sudo service postgresql status
# Should show: "online"

# 2. Check Redis
redis-cli ping
# Should return: "PONG"

# 3. Check database
sudo -u postgres psql -l | grep research_db
# Should show your database

# 4. Test connection
python3 -c "from app.core.database import engine; print('✅ Database connected')"

# 5. Test Redis
python3 -c "from app.utils.cache import CacheService; c = CacheService('redis://localhost:6379'); print('✅ Redis connected' if c.is_connected() else '❌ Redis failed')"

# 6. Run tests
python tests/test_search.py
```

---

## 🔒 Security Notes

**For Development (Codespaces):**
- Default postgres password is fine
- Services are only accessible within your Codespace
- API is behind GitHub authentication

**For Production (Later):**
- Use environment variables for all passwords
- Use Railway/Render managed databases
- Enable SSL/TLS
- Add rate limiting

---

## 🚨 Common Codespaces Issues

### "Cannot connect to database"
```bash
# Restart PostgreSQL
sudo service postgresql restart

# Check if it's running
sudo service postgresql status

# Check connection
psql -U postgres -d research_db -c "SELECT 1;"
```

### "Redis connection refused"
```bash
# Restart Redis
sudo service redis-server restart

# Test connection
redis-cli ping
```

### "Port 8000 not accessible"
```bash
# Make sure you're binding to 0.0.0.0, not 127.0.0.1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Check PORTS tab in Codespace
# Make sure port 8000 is set to "Public"
```

---

## 🎉 You're Ready!

Once setup is complete, you can:
- ✅ Develop in the cloud (no local setup needed)
- ✅ Access from any device
- ✅ Share preview URLs with others
- ✅ Automatic environment sync via GitHub

**Next:** Run the tests and start building! 🚀