#!/bin/bash

# PWA Setup Script for AI Ambassador Platform
# This script helps set up the PWA for development and production

set -e

echo "🚀 AI Ambassador Platform - PWA Setup"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check prerequisites
echo "Checking prerequisites..."

# Check Node.js
if command -v node &> /dev/null; then
    print_success "Node.js installed: $(node --version)"
else
    print_error "Node.js not found. Please install Node.js 16+"
    exit 1
fi

# Check npm
if command -v npm &> /dev/null; then
    print_success "npm installed: $(npm --version)"
else
    print_error "npm not found. Please install npm"
    exit 1
fi

# Check Python
if command -v python3 &> /dev/null; then
    print_success "Python installed: $(python3 --version)"
else
    print_error "Python 3 not found. Please install Python 3.11"
    exit 1
fi

echo ""

# Install dependencies
echo "📦 Installing dependencies..."

# Install web-push for VAPID keys
if ! command -v web-push &> /dev/null; then
    echo "Installing web-push CLI..."
    npm install -g web-push
    print_success "web-push installed"
else
    print_success "web-push already installed"
fi

# Install Python dependencies for Azure Functions
if [ -d "Copilot-Agent-365-main" ]; then
    cd Copilot-Agent-365-main

    if [ ! -d ".venv" ]; then
        echo "Creating Python virtual environment..."
        python3 -m venv .venv
        print_success "Virtual environment created"
    fi

    echo "Installing Python dependencies..."
    source .venv/bin/activate
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    pip install -q pywebpush
    print_success "Python dependencies installed"

    deactivate
    cd ..
else
    print_warning "Copilot-Agent-365-main directory not found. Skipping Python setup."
fi

echo ""

# Generate VAPID keys
echo "🔑 Generating VAPID keys for push notifications..."

if [ ! -f ".vapid-keys.txt" ]; then
    web-push generate-vapid-keys > .vapid-keys.txt
    print_success "VAPID keys generated and saved to .vapid-keys.txt"

    echo ""
    echo "📋 Your VAPID keys:"
    cat .vapid-keys.txt
    echo ""
    print_warning "Save these keys securely! You'll need them for push notifications."
else
    print_warning "VAPID keys already exist in .vapid-keys.txt"
fi

echo ""

# Check for icons
echo "🎨 Checking app icons..."

if [ ! -d "icons" ]; then
    mkdir icons
    print_success "Icons directory created"
fi

if [ -z "$(ls -A icons/*.png 2>/dev/null)" ]; then
    print_warning "No icons found in icons/ directory"
    echo "   Please generate icons using the instructions in icons/README.md"
    echo "   Required sizes: 72, 96, 128, 144, 152, 192, 384, 512"
else
    icon_count=$(ls -1 icons/*.png 2>/dev/null | wc -l)
    print_success "Found $icon_count icons"
fi

echo ""

# Test service worker
echo "🔧 Validating service worker..."

if [ -f "service-worker.js" ]; then
    # Check if it's valid JavaScript
    if node -c service-worker.js 2>/dev/null; then
        print_success "service-worker.js is valid"
    else
        print_error "service-worker.js has syntax errors"
    fi
else
    print_error "service-worker.js not found"
fi

echo ""

# Test manifest
echo "📱 Validating manifest..."

if [ -f "manifest.json" ]; then
    # Check if it's valid JSON
    if python3 -m json.tool manifest.json > /dev/null 2>&1; then
        print_success "manifest.json is valid"
    else
        print_error "manifest.json has syntax errors"
    fi
else
    print_error "manifest.json not found"
fi

echo ""

# Setup local development
echo "💻 Setting up local development..."

# Create a simple server script
cat > start-dev.sh << 'EOF'
#!/bin/bash
echo "Starting development server on http://localhost:8080"
echo "Press Ctrl+C to stop"
echo ""
python3 -m http.server 8080
EOF

chmod +x start-dev.sh
print_success "Created start-dev.sh"

echo ""

# Setup instructions
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo ""
echo "1. Generate app icons:"
echo "   cd icons"
echo "   # Use ImageMagick or online tool to create icons"
echo "   # See icons/README.md for instructions"
echo ""
echo "2. Update VAPID keys in code:"
echo "   - scripts/push-notifications.js (line ~28)"
echo "   - Copilot-Agent-365-main/push_notification_function.py (lines 12-14)"
echo ""
echo "3. Start development server:"
echo "   ./start-dev.sh"
echo "   # Then open http://localhost:8080/mobile-chat.html"
echo ""
echo "4. Test PWA features:"
echo "   - Open Chrome DevTools > Application tab"
echo "   - Check Service Workers and Manifest"
echo "   - Test offline mode with Network > Offline"
echo ""
echo "5. Deploy to production:"
echo "   - See PWA_GUIDE.md for deployment instructions"
echo ""
echo "📚 Documentation: PWA_GUIDE.md"
echo ""
