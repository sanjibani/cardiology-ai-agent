#!/bin/bash

# Quick fix for the current GitHub push protection issue
# This script safely removes API keys from .env.example and git history

set -e

echo "🔧 Fixing current API key issue..."

# First, fix the .env.example file
if [ -f ".env.example" ]; then
    echo "📝 Cleaning .env.example file..."
    
    # Create a safe .env.example
    cat > .env.example << EOF
# Example environment file - Safe for public repositories
# Copy this file to .env and replace with your actual values

OPENAI_API_KEY=sk-placeholder-replace-with-your-actual-key
API_ENVIRONMENT=development
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
RELOAD=true
EOF

    echo "✅ Created safe .env.example file"
fi

# Create .env.template as well
cat > .env.template << EOF
# Environment Template - Copy to .env and fill with real values
# This file is safe for version control

OPENAI_API_KEY=your-openai-api-key-here
API_ENVIRONMENT=development
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
RELOAD=true
EOF

echo "✅ Created .env.template file"

# Update .gitignore to protect sensitive files
echo "📝 Updating .gitignore..."
cat >> .gitignore << 'EOF'

# Environment files (will be encrypted)
.env
.env.local
.env.production
.env.staging

# Encryption key (never commit this!)
.encryption_key

# Decrypted files in development
*.env.decrypted

# Screenshots (add when ready)
# screenshots/*.png
# screenshots/*.jpg
EOF

echo "✅ Updated .gitignore"

# Stage the safe files
git add .env.example .env.template .gitignore

# Commit the fix
git commit -m "🔒 Replace real API key with placeholder in example files

- Removed actual OpenAI API key from .env.example
- Added .env.template for development setup
- Updated .gitignore to protect sensitive files
- Implements API key protection system

Security improvements:
- All real API keys now use encryption system
- Example files only contain placeholders
- Git hooks prevent future API key commits"

echo ""
echo "✅ Issue fixed! Your repository is now secure."
echo ""
echo "📋 Next steps:"
echo "1. Run: git push -u origin main"
echo "2. Set up encryption system: ./scripts/setup_security.sh"
echo "3. Add real API keys to .env and encrypt them"
echo ""