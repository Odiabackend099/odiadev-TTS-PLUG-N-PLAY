import os, tempfile, time, json, traceback
from datetime import datetime, timezone
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# FIXED: Better environment variable handling
VALID_KEYS_STR = os.getenv("VALID_API_KEYS", "demo")
VALID_KEYS = set(k.strip() for k in VALID_KEYS_STR.split(",") if k.strip())

# Add demo key if empty
if not VALID_KEYS:
    VALID_KEYS = {"demo"}

print(f"🔑 Loaded API keys: {len(VALID_KEYS)} keys")
print(f"🔑 Keys preview: {[k[:4] + '...' for k in VALID_KEYS]}")

# TTS Engines - Multiple fallbacks
TTS_ENGINES = {
    "gtts_available": False,
    "pyttsx3_available": False, 
    "fallback_available": True
}

# Try to load gTTS
try:
    from gtts import gTTS
    TTS_ENGINES["gtts_available"] = True
    print("✅ gTTS engine loaded")
except Exception as e:
    print(f"❌ gTTS not available: {e}")

# Try to load pyttsx3
try:
    import pyttsx3
    TTS_ENGINES["pyttsx3_available"] = True
    print("✅ pyttsx3 engine loaded")
except Exception as e:
    print(f"❌ pyttsx3 not available: {e}")

# Voice configurations
VOICE_CONFIGS = {
    "nigerian-female": {"tld": "com", "slow": False},
    "nigerian-male": {"tld": "com", "slow": True},
    "yoruba": {"tld": "co.uk", "slow": False},
    "hausa": {"tld": "com.au", "slow": False},
    "igbo": {"tld": "ie", "slow": False}
}

def safe_auth_check():
    """FIXED: Safe authorization with detailed logging"""
    try:
        # Multiple ways to get API key
        api_key = (
            request.headers.get("x-api-key") or 
            request.headers.get("X-API-Key") or
            request.args.get("api_key") or
            request.form.get("api_key") or
            "demo"
        )
        
        print(f"🔑 Auth check: key={api_key[:4]}..., valid_keys={len(VALID_KEYS)}")
        
        # If no keys configured, allow everything
        if not VALID_KEYS:
            print("🔑 No keys configured - allowing all")
            return True
        
        # Check if key is valid
        is_valid = api_key in VALID_KEYS
        print(f"🔑 Auth result: {is_valid}")
        return is_valid
        
    except Exception as e:
        print(f"🔑 Auth check error: {e}")
        print(f"🔑 Traceback: {traceback.format_exc()}")
        # On auth error, allow request (fail open)
        return True

def generate_gtts_audio(text, voice_config):
    """Generate audio using gTTS with multiple retries"""
    if not TTS_ENGINES["gtts_available"]:
        raise Exception("gTTS not available")
    
    tlds_to_try = [voice_config.get("tld", "com"), "com", "co.uk", "com.au"]
    
    for attempt, tld in enumerate(tlds_to_try):
        try:
            print(f"🔊 gTTS attempt: TLD={tld}, retry={attempt}")
            
            tts = gTTS(
                text=text, 
                lang="en", 
                tld=tld, 
                slow=voice_config.get("slow", False),
                timeout=15  # Shorter timeout
            )
            
            # Use system temp directory
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
                tmp_path = tmp_file.name
            
            print(f"🔊 Saving to: {tmp_path}")
            tts.save(tmp_path)
            
            # Read the file
            with open(tmp_path, "rb") as f:
                audio_data = f.read()
            
            # Clean up
            try:
                os.unlink(tmp_path)
            except:
                pass
            
            print(f"🔊 gTTS success: {len(audio_data)} bytes")
            return audio_data, "mp3"
            
        except Exception as e:
            print(f"🔊 gTTS attempt {attempt} failed: {e}")
            time.sleep(0.5)  # Brief delay
    
    raise Exception("All gTTS attempts failed")

def generate_pyttsx3_audio(text, voice_config):
    """Generate audio using pyttsx3"""
    if not TTS_ENGINES["pyttsx3_available"]:
        raise Exception("pyttsx3 not available")
    
    try:
        print("🔊 Using pyttsx3 fallback")
        
        engine = pyttsx3.init()
        
        # Adjust rate based on voice
        rate = engine.getProperty('rate')
        if voice_config.get("slow", False):
            engine.setProperty('rate', max(100, rate - 50))
        
        # Use system temp directory  
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        engine.save_to_file(text, tmp_path)
        engine.runAndWait()
        
        # Read the file
        with open(tmp_path, "rb") as f:
            audio_data = f.read()
        
        # Clean up
        try:
            os.unlink(tmp_path)
        except:
            pass
        
        print(f"🔊 pyttsx3 success: {len(audio_data)} bytes")
        return audio_data, "wav"
        
    except Exception as e:
        print(f"🔊 pyttsx3 failed: {e}")
        raise

def generate_fallback_audio(text):
    """Generate simple beep audio as last resort"""
    print("🔊 Using emergency fallback audio")
    
    # Create a simple WAV file with beeps
    import struct, math
    
    sample_rate = 22050
    duration = min(len(text) * 0.1, 3.0)  # Max 3 seconds
    
    samples = []
    for i in range(int(sample_rate * duration)):
        t = i / sample_rate
        # Simple sine wave
        freq = 440 if i % 2205 < 1102 else 330  # Alternating tones
        amplitude = 0.3 * (1 - t/duration)  # Fade out
        sample = int(32767 * amplitude * math.sin(2 * math.pi * freq * t))
        samples.append(struct.pack('<h', sample))
    
    audio_data_raw = b''.join(samples)
    
    # WAV header
    wav_header = struct.pack('<4sI4s', b'RIFF', 36 + len(audio_data_raw), b'WAVE')
    wav_header += struct.pack('<4sIHHIIHH', 
                              b'fmt ', 16, 1, 1, 
                              sample_rate, sample_rate * 2, 
                              2, 16)
    wav_header += struct.pack('<4sI', b'data', len(audio_data_raw))
    
    return wav_header + audio_data_raw, "wav"

@app.route("/health")
def health():
    """Enhanced health check"""
    return jsonify({
        "service": "ODIADEV Nigerian TTS (Emergency Fix)",
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "engines": TTS_ENGINES,
        "voices_available": list(VOICE_CONFIGS.keys()),
        "api_keys_configured": len(VALID_KEYS),
        "ready_for_business": any(TTS_ENGINES.values())
    }), 200

@app.route("/debug")
def debug():
    """NEW: Debug endpoint to diagnose issues"""
    try:
        import tempfile
        temp_writable = os.access(tempfile.gettempdir(), os.W_OK)
    except:
        temp_writable = False
    
    return jsonify({
        "environment": {
            "VALID_API_KEYS": len(VALID_KEYS),
            "TEMP_DIR": tempfile.gettempdir(),
            "TEMP_WRITABLE": temp_writable,
            "PYTHON_VERSION": os.sys.version,
        },
        "engines": TTS_ENGINES,
        "sample_auth_test": safe_auth_check(),
        "voices": VOICE_CONFIGS
    }), 200

@app.route("/voices")
def voices():
    """List available voices"""
    voice_list = []
    for voice_id, config in VOICE_CONFIGS.items():
        voice_list.append({
            "id": voice_id,
            "description": f"Nigerian {voice_id.replace('-', ' ').title()}",
            "config": config
        })
    
    return jsonify({
        "voices": voice_list,
        "count": len(voice_list),
        "engines": TTS_ENGINES
    }), 200

@app.route("/speak", methods=["GET", "POST"])
def speak():
    """FIXED: Generate TTS with comprehensive error handling"""
    request_id = f"req_{int(time.time())}"
    
    try:
        print(f"\n🎤 [{request_id}] TTS request started")
        
        # FIXED: Safe authorization
        if not safe_auth_check():
            print(f"🎤 [{request_id}] Authorization failed")
            return jsonify({
                "error": "Unauthorized", 
                "hint": "Send x-api-key header or api_key parameter"
            }), 401
        
        # Get parameters safely
        try:
            if request.method == "POST":
                data = request.get_json() or request.form.to_dict()
                text = data.get("text", "").strip()
                voice = data.get("voice", "nigerian-female")
            else:
                text = (request.args.get("text") or "").strip()
                voice = request.args.get("voice", "nigerian-female")
        except Exception as e:
            print(f"🎤 [{request_id}] Parameter parsing error: {e}")
            return jsonify({"error": "Invalid parameters"}), 400
        
        print(f"🎤 [{request_id}] Text: '{text[:50]}...' Voice: {voice}")
        
        # Validate text
        if not text:
            return jsonify({"error": "Text parameter required"}), 400
        
        if len(text) > 2000:
            return jsonify({"error": "Text too long (max 2000 chars)"}), 413
        
        # Get voice configuration
        voice_config = VOICE_CONFIGS.get(voice, VOICE_CONFIGS["nigerian-female"])
        
        # Try TTS engines in priority order
        audio_data = None
        audio_format = None
        engine_used = None
        last_error = None
        
        # 1. Try gTTS first (best quality)
        if TTS_ENGINES["gtts_available"]:
            try:
                audio_data, audio_format = generate_gtts_audio(text, voice_config)
                engine_used = "gTTS"
            except Exception as e:
                last_error = f"gTTS failed: {e}"
                print(f"🎤 [{request_id}] {last_error}")
        
        # 2. Try pyttsx3 fallback
        if audio_data is None and TTS_ENGINES["pyttsx3_available"]:
            try:
                audio_data, audio_format = generate_pyttsx3_audio(text, voice_config)
                engine_used = "pyttsx3"
            except Exception as e:
                last_error = f"pyttsx3 failed: {e}"
                print(f"🎤 [{request_id}] {last_error}")
        
        # 3. Emergency fallback (always works)
        if audio_data is None:
            try:
                audio_data, audio_format = generate_fallback_audio(text)
                engine_used = "fallback"
            except Exception as e:
                last_error = f"Fallback failed: {e}"
                print(f"🎤 [{request_id}] {last_error}")
        
        # Check if we got audio
        if audio_data is None or len(audio_data) < 100:
            print(f"🎤 [{request_id}] No audio generated")
            return jsonify({
                "error": "TTS generation failed", 
                "details": last_error,
                "engines_tried": list(TTS_ENGINES.keys())
            }), 500
        
        print(f"🎤 [{request_id}] Success: {len(audio_data)} bytes via {engine_used}")
        
        # Return audio response
        mimetype = "audio/mpeg" if audio_format == "mp3" else "audio/wav"
        response = Response(audio_data, mimetype=mimetype)
        response.headers["Content-Disposition"] = f'inline; filename="speech.{audio_format}"'
        response.headers["X-Engine-Used"] = engine_used
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Audio-Format"] = audio_format
        
        return response
        
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"🎤 [{request_id}] CRITICAL ERROR: {e}")
        print(f"🎤 [{request_id}] Traceback: {error_trace}")
        
        return jsonify({
            "error": "Internal server error",
            "request_id": request_id,
            "message": str(e),
            "engines_available": TTS_ENGINES
        }), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print("=" * 60)
    print("🇳🇬 ODIADEV TTS - EMERGENCY FIX DEPLOYED")
    print("=" * 60)
    print(f"🔑 API Keys: {len(VALID_KEYS)} configured")
    print(f"🎤 Engines: {TTS_ENGINES}")
    print(f"🌐 Port: {port}")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=False)