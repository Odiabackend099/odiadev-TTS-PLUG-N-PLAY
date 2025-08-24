# 🇳🇬 ODIADEV NIGERIAN TTS ENGINE - QUICK SETUP

**Realistic conversational Nigerian voices with voice cloning support**

## ⚡ INSTANT DEPLOYMENT (5 Minutes)

### Step 1: Save Files to Your Computer
Copy these 4 files to a new folder:

1. **app.py** - Main TTS engine (Nigerian Coqui TTS implementation)
2. **requirements.txt** - Python dependencies  
3. **render.yaml** - Deployment configuration
4. **deploy.sh** - One-click deployment script

### Step 2: Run Deployment Script
```bash
# Make script executable (Linux/Mac)
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

**Windows users:** Run commands manually or use Git Bash

### Step 3: Deploy to Render
1. Go to: https://dashboard.render.com
2. Click: **New +** → **Web Service**
3. Connect your GitHub repository
4. Render auto-detects `render.yaml` settings
5. Click: **Create Web Service**

**⏱️ Deployment takes 5-10 minutes** (TTS models are large)

---

## 🎯 YOUR TTS API ENDPOINTS

Once deployed at `https://nigerian-tts-engine.onrender.com`:

### 🎤 Generate Speech
```bash
# GET Request (simple)
curl "https://nigerian-tts-engine.onrender.com/speak?text=Hello Nigeria&voice=en-NG-EzinneNeural" --output speech.wav

# POST Request (advanced)
curl -X POST https://nigerian-tts-engine.onrender.com/speak \
  -H "Content-Type: application/json" \
  -d '{"text":"Welcome to Nigeria!","voice":"en-NG-EzinneNeural","format":"mp3"}' \
  --output welcome.wav
```

### 🗣️ Available Voices
```bash
curl https://nigerian-tts-engine.onrender.com/voices
```

**Nigerian Voice Options:**
- `en-NG-EzinneNeural` - Nigerian English Female (Ezinne) 
- `en-NG-AbeolaNeural` - Nigerian English Male (Abeola)
- `yo-NG-AyotundeNeural` - Yoruba-influenced English Female
- `ig-NG-ObinnaNeural` - Igbo-influenced English Male  
- `ha-NG-MaryamNeural` - Hausa-influenced English Female
- `pcm-NG-ChiomaNeural` - Nigerian Pidgin Female

### 🎭 Voice Cloning
Upload audio samples to create custom voices:

```bash
curl -X POST https://nigerian-tts-engine.onrender.com/clone-voice \
  -F "audio=@your_voice_sample.wav" \
  -F "voice_id=custom_voice_name"
```

---

## 🧪 TESTING YOUR DEPLOYMENT

### Option 1: Automated Testing
```bash
# Download and run the tester
python tts_tester.py https://nigerian-tts-engine.onrender.com
```

### Option 2: Manual Testing  
```bash
# Health check
curl https://nigerian-tts-engine.onrender.com/health

# Generate test audio
curl "https://nigerian-tts-engine.onrender.com/speak?text=Testing Nigerian TTS&voice=en-NG-EzinneNeural" --output test.wav

# Play audio (Windows)
start test.wav
```

---

## 🤖 INTEGRATION WITH YOUR PROJECTS

### Python Integration
```python
import requests

def generate_nigerian_speech(text, voice="en-NG-EzinneNeural"):
    response = requests.get(
        "https://nigerian-tts-engine.onrender.com/speak",
        params={"text": text, "voice": voice, "format": "mp3"}
    )
    
    if response.status_code == 200:
        with open("speech.mp3", "wb") as f:
            f.write(response.content)
        return "speech.mp3"
    else:
        return None

# Example usage
audio_file = generate_nigerian_speech(
    "Hello! Welcome to Nigeria's premier voice AI platform.",
    voice="en-NG-EzinneNeural"
)
```

### JavaScript Integration
```javascript
async function generateNigerianSpeech(text, voice = "en-NG-EzinneNeural") {
    const response = await fetch(
        `https://nigerian-tts-engine.onrender.com/speak?text=${encodeURIComponent(text)}&voice=${voice}`
    );
    
    if (response.ok) {
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audio.play();
    }
}

// Example usage
generateNigerianSpeech("Sannu! Welcome to our platform!", "ha-NG-MaryamNeural");
```

---

## 🔧 TROUBLESHOOTING

### Common Issues:

**1. "Health check failed"**
- Wait 5-10 minutes for full deployment
- TTS models are large and take time to download

**2. "TTS generation failed"**  
- Check Render logs for memory issues
- Upgrade to paid plan if needed (free tier has limitations)

**3. "Audio quality issues"**
- Upload higher quality voice samples for cloning
- Use shorter text snippets for better quality

### 📊 Performance Tips:
- **Free Tier**: Works for testing, 1-2 concurrent users
- **Paid Tier**: Better for production, multiple users
- **Voice Cloning**: Upload 10-30 second clear audio samples
- **Caching**: Identical requests return cached audio

---

## 🎯 WHY THIS SOLUTION IS PERFECT FOR YOU:

✅ **Works on Render** - No HTTPS bouncing issues  
✅ **100% Free** - Coqui TTS is open source  
✅ **Nigerian Voices** - Realistic multilingual accents  
✅ **Voice Cloning** - Train custom voices with your audio  
✅ **Conversational** - Natural sounding, not robotic  
✅ **API Ready** - Integrate with any project immediately  
✅ **No Limits** - Generate unlimited audio  

---

## 🚀 NEXT STEPS:

1. **Deploy Now** - Follow the 3 steps above
2. **Test Voices** - Try all Nigerian voice options  
3. **Clone Voices** - Upload samples for custom training
4. **Integrate** - Add to your AI agents and projects
5. **Scale** - Upgrade Render plan when ready for production

**Your Nigerian TTS engine will be ready in under 10 minutes!** 🎉

---

*Need help? The comprehensive tester script will diagnose any issues automatically.*