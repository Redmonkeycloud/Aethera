#!/bin/bash
# Development environment setup script for AETHERA

set -e

echo "🚀 Setting up AETHERA development environment..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
REQUIRED_VERSION="3.11"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
    echo "❌ Error: Python 3.11+ required. Found: $PYTHON_VERSION"
    echo "   Install Python 3.11+ or use pyenv: pyenv install 3.11.0"
    exit 1
fi

echo "✅ Python version: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install backend dependencies
echo "📥 Installing backend dependencies..."
cd backend
pip install -e ".[dev]"
cd ..

# Install pre-commit
echo "🔧 Installing pre-commit hooks..."
pip install pre-commit
pre-commit install

# Check Docker
if command -v docker &> /dev/null; then
    echo "🐳 Docker found. Starting services..."
    docker compose up -d || echo "⚠️  Docker compose failed. Make sure Docker Desktop is running."
else
    echo "⚠️  Docker not found. Install Docker Desktop to run the database."
fi

# Initialize database if Docker is running
if docker ps | grep -q postgres; then
    echo "🗄️  Initializing database..."
    sleep 2  # Wait for postgres to be ready
    cd backend
    python -m src.db.init_db || echo "⚠️  Database initialization failed. Check Docker logs."
    cd ..
else
    echo "⚠️  Database not running. Start Docker and run: make db-init"
fi

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "Next steps:"
echo "  1. Activate virtual environment: source .venv/bin/activate"
echo "  2. Run tests: make test"
echo "  3. Start API server: cd backend && uvicorn src.api.app:app --reload"
echo ""
echo "See DEVELOPMENT.md for more information."

