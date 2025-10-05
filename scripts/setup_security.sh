#!/bin/bash

# Complete security system setup for the Cardiology AI project
# This script sets up the full API key protection infrastructure

set -e

echo "🔐 Setting up comprehensive security system..."
echo ""

# Make secure_env.py executable
chmod +x scripts/secure_env.py

# Install Git hooks
echo "📋 Installing Git hooks..."
if [ -d ".git" ]; then
    # Copy pre-commit hook to Git hooks directory
    cp .githooks/pre-commit .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
    echo "✅ Installed pre-commit hook"
    
    # Copy pre-push hook if it exists
    if [ -f ".githooks/pre-push" ]; then
        cp .githooks/pre-push .git/hooks/pre-push
        chmod +x .git/hooks/pre-push
        echo "✅ Installed pre-push hook"
    fi
else
    echo "⚠️  No .git directory found. Initialize git first with: git init"
fi

# Create directories if they don't exist
mkdir -p .encrypted
mkdir -p screenshots

# Create a comprehensive .gitignore if needed
if [ ! -f ".gitignore" ]; then
    echo "📝 Creating .gitignore..."
    cat > .gitignore << 'EOF'
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Environment files
.env
.env.local
.env.production
.env.staging
*.env.decrypted

# Encryption key (NEVER COMMIT!)
.encryption_key

# IDE
.vscode/settings.json
.idea/

# OS
.DS_Store
Thumbs.db

# Dependencies
node_modules/
venv/
env/
.venv/

# Logs
logs/
*.log

# Screenshots (uncomment when ready to add)
# screenshots/*.png
# screenshots/*.jpg
EOF
fi

# Create GitHub Actions workflow for CI/CD
echo "🚀 Setting up GitHub Actions..."
mkdir -p .github/workflows

cat > .github/workflows/security-check.yml << 'EOF'
name: Security Check and API Protection

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install bandit safety
        
    - name: Run security scan
      run: |
        # Check for common security issues
        bandit -r . -x tests/
        
        # Check for known vulnerabilities
        safety check
        
    - name: Verify no API keys in code
      run: |
        # Check for API key patterns
        if grep -r "sk-[a-zA-Z0-9]" --exclude-dir=.git --exclude-dir=.encrypted .; then
          echo "❌ Real API keys found in code!"
          exit 1
        fi
        echo "✅ No API keys found in code"
        
    - name: Verify encryption system
      run: |
        python scripts/secure_env.py --verify-setup
EOF

echo "✅ Created GitHub Actions security workflow"

# Create quick setup script for new developers
cat > scripts/developer_setup.sh << 'EOF'
#!/bin/bash

# Quick setup script for new developers
echo "🚀 Setting up Cardiology AI development environment..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Set up environment
echo "⚙️  Setting up environment..."
if [ ! -f ".env" ]; then
    cp .env.template .env
    echo "📝 Created .env file - Please add your API keys!"
    echo "   Edit .env and add your OpenAI API key"
fi

# Install Git hooks
echo "🔗 Installing Git hooks..."
if [ -f "scripts/setup_security.sh" ]; then
    ./scripts/setup_security.sh
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env with your real API keys"
echo "2. Run: python scripts/secure_env.py --encrypt .env"
echo "3. Start development: uvicorn main:app --reload"
echo ""
EOF

chmod +x scripts/developer_setup.sh

# Create environment management helpers
cat > scripts/env_helpers.sh << 'EOF'
#!/bin/bash

# Helper functions for environment management

encrypt_env() {
    echo "🔐 Encrypting environment files..."
    python scripts/secure_env.py --encrypt .env
}

decrypt_env() {
    echo "🔓 Decrypting environment files..."
    python scripts/secure_env.py --decrypt .env.encrypted
}

rotate_keys() {
    echo "🔄 Rotating encryption keys..."
    python scripts/secure_env.py --rotate-key
}

check_security() {
    echo "🔍 Checking security status..."
    python scripts/secure_env.py --scan
}

# Make functions available
export -f encrypt_env decrypt_env rotate_keys check_security
EOF

chmod +x scripts/env_helpers.sh

# Create quick commands for common tasks
cat > scripts/quick_commands.sh << 'EOF'
#!/bin/bash

# Quick commands for common development tasks

case "$1" in
    "start")
        echo "🚀 Starting Cardiology AI system..."
        python scripts/secure_env.py --decrypt .env.encrypted --quiet
        uvicorn main:app --reload --host 0.0.0.0 --port 8000
        ;;
    "encrypt")
        echo "🔐 Encrypting environment..."
        python scripts/secure_env.py --encrypt .env
        ;;
    "decrypt")
        echo "🔓 Decrypting environment..."
        python scripts/secure_env.py --decrypt .env.encrypted
        ;;
    "test")
        echo "🧪 Running tests..."
        python -m pytest tests/ -v
        ;;
    "security")
        echo "🔍 Security check..."
        python scripts/secure_env.py --scan
        ;;
    "deploy")
        echo "🚀 Preparing for deployment..."
        python scripts/secure_env.py --encrypt .env
        git add .encrypted/
        echo "✅ Environment encrypted and ready for commit"
        ;;
    *)
        echo "Usage: $0 {start|encrypt|decrypt|test|security|deploy}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the application with decrypted env"
        echo "  encrypt  - Encrypt .env file"
        echo "  decrypt  - Decrypt .env.encrypted file"
        echo "  test     - Run test suite"
        echo "  security - Run security scan"
        echo "  deploy   - Prepare for secure deployment"
        ;;
esac
EOF

chmod +x scripts/quick_commands.sh

# Update README with security information
echo "📚 Updating README with security information..."

# Add security section to README if it doesn't exist
if ! grep -q "## Security" README.md; then
    cat >> README.md << 'EOF'

## Security

This project implements comprehensive API key protection for safe public repository hosting.

### 🔐 API Key Protection System

All sensitive API keys are encrypted using AES-256 encryption before being committed to the repository.

#### Quick Setup
```bash
# Initial setup
./scripts/setup_security.sh

# Fix current API key issue
./scripts/fix_current_issue.sh

# Encrypt your .env file
python scripts/secure_env.py --encrypt .env
```

#### Daily Workflow
```bash
# Start development
./scripts/quick_commands.sh start

# Before committing
./scripts/quick_commands.sh deploy
```

#### Security Features
- 🔒 AES-256 encryption for all API keys
- 🚫 Git hooks prevent accidental API key commits
- 🔍 Automated security scanning
- 🔄 Key rotation capabilities
- 📊 Security audit trail

#### Environment Files
- `.env.template` - Template for new developers
- `.env.example` - Safe example file (public)
- `.env` - Your real environment (encrypted before commit)
- `.encrypted/env.encrypted` - Encrypted version (safe to commit)

### Security Commands

```bash
# Encrypt environment
python scripts/secure_env.py --encrypt .env

# Decrypt for development
python scripts/secure_env.py --decrypt .env.encrypted

# Scan for exposed keys
python scripts/secure_env.py --scan

# Rotate encryption key
python scripts/secure_env.py --rotate-key
```

EOF
fi

echo ""
echo "🎉 Security system setup complete!"
echo ""
echo "📋 Summary of installed components:"
echo "   ✅ Git hooks for API key protection"
echo "   ✅ GitHub Actions security workflow"
echo "   ✅ Developer setup scripts"
echo "   ✅ Environment management tools"
echo "   ✅ Quick command helpers"
echo "   ✅ Comprehensive documentation"
echo ""
echo "🚀 Next steps:"
echo "1. Run: ./scripts/fix_current_issue.sh (to fix immediate Git issue)"
echo "2. Add your real API keys to .env"
echo "3. Run: python scripts/secure_env.py --encrypt .env"
echo "4. Test: ./scripts/quick_commands.sh start"
echo ""
echo "💡 Pro tip: Use './scripts/quick_commands.sh deploy' before each commit"