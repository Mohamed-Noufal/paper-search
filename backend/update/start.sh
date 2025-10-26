#!/bin/bash

# Daily startup script for GitHub Codespaces
# Run this every time you open your Codespace

echo "🔄 Starting services..."

# Start PostgreSQL
sudo service postgresql start > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL started"
else
    echo "❌ PostgreSQL failed to start"
fi

# Start Redis
sudo service redis-server start > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Redis started"
else
    echo "❌ Redis failed to start"
fi

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Python environment activated"
else
    echo "⚠️  Virtual environment not found. Run setup_codespace.sh first"
    exit 1
fi

echo ""
echo "🎉 Ready to code!"
echo ""
echo "Quick commands:"
echo "  • Test:  python tests/test_search.py"
echo "  • Run:   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo "  • Docs:  http://localhost:8000/docs"