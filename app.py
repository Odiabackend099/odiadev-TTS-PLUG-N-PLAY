import os
import sys
import asyncio
import tempfile
import platform
from datetime import datetime, timezone
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

import edge_tts  # online (needs internet)

# Optional offline fallback on Windows only
USE_OFFLINE_FALLBACK = os.getenv("USE_OFFLINE_FALLBACK", "0") == "1"
WINDOWS = platform.system().lower().startswith("win")
if USE_OFFLINE_FALLBACK and WINDOWS:
    try:
        import pyttsx3  # offline (Windows SAPI5)
        HAVE_PYTTSX3 = True
    except Exception:
        HAVE_PYTTSX3 = False
else:
    HAVE_PYTTSX3 = False

app = Flask(__name__)
CORS(app)

_VALID_KEYS = set(k.strip() for k in os.getenv("VALID_API_KEYS", "").split(",") if k.strip())

VOICE_MAP = {
    "nigerian-female": "en-NG-EzinneNeural",
    "nigerian-male": "en-NG-AbeoNeural",
    "en-NG-EzinneNeural": "en-NG-EzinneNeural",
    "en-NG-AbeoNeural": "en-NG-AbeoNeural",
}

def _check_auth():
    if not _VALID_KEYS:
        return True
    supplied = request.headers.get("x-api-key", "")
    return supplied in _VALID_KEYS

def _pick_voice(v):
    if not v:
        return VOICE_MAP["nigerian-female"]
    return VOICE_MAP.get(v, VOICE_MAP["nigerian-female"])

def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    finally:
        loop.close()

async def _edge_tts_bytes_mp3(text: str, voice_id: str) -> bytes:
    comm = edge_tts.Communicate(text=text, voice=voice_id)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmpf:
        out_path = tmpf.name
    try:
        # No 'format' arg -> universally supported; default is MP3
        await comm.save(out_path)
        with open(out_path, "rb") as f:
            return f.read()
    finally:
        try:
            os.remove(out_path)
        except:
            pass

def _offline_windows_wav(text: str) -> bytes:
    # Requires Windows + pyttsx3 available (SAPI5)
    if not (WINDOWS and HAVE_PYTTSX3):
        raise RuntimeError("Offline fallback not available on this system.")
    engine = pyttsx3.init()
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpf:
        out_path = tmpf.name
    try:
        engine.save_to_file(text, out_path)
        engine.runAndWait()
        with open(out_path, "rb") as f:
            return f.read()
    finally:
        try:
            os.remove(out_path)
        except:
            pass

@app.get("/health")
def health():
    return jsonify({
        "status": "healthy",
        "service": "ODIADEV Nigerian TTS",
        "backend": "EdgeTTS (online) + Windows pyttsx3 fallback (offline)",
        "voices_available": list(VOICE_MAP.keys()),
        "offline_fallback_enabled": USE_OFFLINE_FALLBACK and WINDOWS and HAVE_PYTTSX3,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200

@app.get("/voices")
def voices():
    data = [
        {"id": "nigerian-female", "description": "Nigerian English Female  en-NG-EzinneNeural"},
        {"id": "nigerian-male", "description": "Nigerian English Male  en-NG-AbeoNeural"},
        {"id": "en-NG-EzinneNeural", "description": "Microsoft Ezinne Neural (Professional)"},
        {"id": "en-NG-AbeoNeural", "description": "Microsoft Abeo Neural (Professional)"},
    ]
    return jsonify(data), 200

@app.get("/speak")
def speak():
    if not _check_auth():
        return jsonify({"error": "Unauthorized"}), 401

    text = (request.args.get("text") or "").strip()
    voice = _pick_voice(request.args.get("voice"))
    if not text:
        return jsonify({"error": "Missing 'text'"}), 400
    if len(text) > 2000:
        return jsonify({"error": "Text too long (max 2000 chars)"}), 413

    # Prefer online Edge TTS (MP3). If it fails with DNS/connection and fallback is enabled, use offline WAV.
    try:
        audio = _run_async(_edge_tts_bytes_mp3(text, voice))
        resp = Response(audio, mimetype="audio/mpeg")
        resp.headers["Content-Disposition"] = 'inline; filename="speech.mp3"'
        return resp
    except Exception as e:
        err_msg = str(e)
        # If DNS/connectivity issue OR forced fallback, try offline Windows WAV
        if (("getaddrinfo failed" in err_msg) or ("Cannot connect to host" in err_msg) or USE_OFFLINE_FALLBACK) and (WINDOWS and HAVE_PYTTSX3):
            try:
                audio = _offline_windows_wav(text)
                resp = Response(audio, mimetype="audio/wav")
                resp.headers["Content-Disposition"] = 'inline; filename="speech.wav"'
                return resp
            except Exception as e2:
                return jsonify({"error": "TTS failed (offline fallback error)", "details": str(e2)}), 500
        return jsonify({"error": "TTS failed", "details": err_msg}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)