import os, tempfile
from datetime import datetime, timezone
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from gtts import gTTS

app = Flask(__name__)
CORS(app)

VALID_KEYS = set(k.strip() for k in os.getenv("VALID_API_KEYS", "").split(",") if k.strip())
VOICE_MAP = {
    "nigerian-female": "com",        # all voices map to the same tld for now
    "nigerian-male": "com",
    "en-NG-EzinneNeural": "com",
    "en-NG-AbeoNeural": "com",
}

def check_auth():
    return not VALID_KEYS or request.headers.get("x-api-key", "") in VALID_KEYS

def pick_tld(v):
    return VOICE_MAP.get(v, "com")

def tts_bytes(text, tld):
    tts = gTTS(text, lang='en', tld=tld)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmpf:
        tts.save(tmpf.name)
    try:
        with open(tmpf.name, "rb") as f:
            return f.read()
    finally:
        os.remove(tmpf.name)

@app.get("/health")
def health():
    return jsonify({
        "status": "healthy",
        "service": "ODIADEV Nigerian TTS (gTTS)",
        "voices_available": list(VOICE_MAP.keys()),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.get("/voices")
def voices():
    return jsonify([
        {"id": v, "description": f"gTTS English voice (TLD: {t})"}
        for v, t in VOICE_MAP.items()
    ])

@app.get("/speak")
def speak():
    if not check_auth():
        return jsonify({"error": "Unauthorized"}), 401
    text = (request.args.get("text") or "").strip()
    voice = request.args.get("voice", "nigerian-female")
    if not text:
        return jsonify({"error": "Missing 'text'"}), 400
    if len(text) > 2000:
        return jsonify({"error": "Text too long (max 2000 chars)"}), 413
    try:
        mp3_data = tts_bytes(text, pick_tld(voice))
        resp = Response(mp3_data, mimetype="audio/mpeg")
        resp.headers["Content-Disposition"] = 'inline; filename="speech.mp3"'
        return resp
    except Exception as e:
        return jsonify({"error": "TTS failed", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
