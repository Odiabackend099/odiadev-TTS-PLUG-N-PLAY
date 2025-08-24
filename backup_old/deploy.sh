#!/bin/bash

echo "🇳🇬 ODIADEV NIGERIAN TTS ENGINE - DEPLOYMENT SCRIPT"
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ app.py not found. Please ensure all files are in the current directory:"
    echo "   - app.py (main TTS engine)"
    echo "   - requirements.txt"
    echo "   - render.yaml"
    exit 1
fi

echo "✅ All required files found!"

# Test local installation (optional)
echo ""
read -p "🧪 Do you want to test locally first? (y/n): " test_local

if [ "$test_local" = "y" ]; then
    echo ""
    echo "📦 Installing dependencies locally..."
    
    # Create virtual environment
    python -m venv nigerian_tts_env
    
    # Activate virtual environment
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        source nigerian_tts_env/Scripts/activate
    else
        source nigerian_tts_env/bin/activate
    fi
    
    # Install dependencies
    pip install --upgrade pip
    pip install torch==2.1.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cpu
    pip install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        echo "✅ Local installation successful!"
        echo ""
        echo "🚀 Starting local test server..."
        echo "   Open http://localhost:5000 in your browser"
        echo "   Press Ctrl+C to stop and continue with deployment"
        echo ""
        
        python app.py &
        LOCAL_PID=$!
        
        # Wait a bit for server to start
        sleep 5
        
        # Test the local server
        echo "🧪 Testing local TTS..."
        curl -s "http://localhost:5000/health" | python -m json.tool
        
        echo ""
        echo "Press Enter when ready to continue with Render deployment..."
        read
        
        # Stop local server
        kill $LOCAL_PID 2>/dev/null
    else
        echo "❌ Local installation failed. Continuing with deployment anyway..."
    fi
fi

# Git setup and push
echo ""
echo "📦 Preparing for Render deployment..."

# Initialize git if not already done
if [ ! -d ".git" ]; then
    git init
    git branch -M main
fi

# Add all files
git add .
git commit -m "🇳🇬 Deploy Nigerian TTS Engine with Coqui TTS - v2.0.0" || echo "Nothing new to commit"

# Check if remote exists
if ! git remote get-url origin >/dev/null 2>&1; then
    echo ""
    echo "⚠️  No Git remote configured. Please set up your repository:"
    echo ""
    echo "   1. Create a new repository on GitHub"
    echo "   2. Run: git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git"
    echo "   3. Run this script again"
    echo ""
    exit 1
fi

# Push to remote
echo "⬆️  Pushing to GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo "✅ Code pushed to GitHub successfully!"
else
    echo "❌ Git push failed. Please check your repository setup."
    exit 1
fi

# Deployment instructions
echo ""
echo "🎯 RENDER DEPLOYMENT INSTRUCTIONS:"
echo "=================================="
echo ""
echo "1️⃣  Go to: https://dashboard.render.com"
echo "2️⃣  Click: New + → Web Service"
echo "3️⃣  Connect your GitHub repository"
echo "4️⃣  Render will auto-detect the render.yaml configuration"
echo "5️⃣  Click: Create Web Service"
echo ""
echo "⏱️  Deployment takes 5-10 minutes (TTS models are large)"
echo ""
echo "🎤 YOUR NIGERIAN TTS API WILL BE LIVE AT:"
echo "   https://nigerian-tts-engine.onrender.com"
echo ""
echo "📋 TESTING YOUR DEPLOYED API:"
echo "   curl https://nigerian-tts-engine.onrender.com/health"
echo "   curl 'https://nigerian-tts-engine.onrender.com/speak?text=Hello%20Nigeria&voice=en-NG-EzinneNeural' --output test.wav"
echo ""
echo "🎭 VOICE CLONING:"
echo "   Upload audio samples to /clone-voice endpoint"
echo "   Train custom Nigerian voices for your projects"
echo ""
echo "=================================================="
echo "✨ Deployment preparation complete!"
echo "   Follow the Render instructions above to go live"
echo "=================================================="
