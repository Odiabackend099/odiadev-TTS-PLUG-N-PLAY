import os
import asyncio
import tempfile
from datetime import datetime, timezone
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import edge_tts

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

async def _tts_to_bytes(text: str, voice_id: str) -> bytes:
    """
    Edge TTS default save() returns MP3. We avoid 'format=' to support all versions.
    """
    comm = edge_tts.Communicate(text=text, voice=voice_id)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmpf:
        out_path = tmpf.name
    try:
        await comm.save(out_path)  # no 'format' arg
        with open(out_path, "rb") as f:
            return f.read()
    finally:
        try: os.remove(out_path)
        except: pass

def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@app.get("/health")
def health():
    return jsonify({
        "status": "healthy",
        "service": "ODIADEV Nigerian TTS (EdgeTTS MP3)",
        "voices_available": list(VOICE_MAP.keys()),
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

    try:
        audio = _run_async(_tts_to_bytes(text, voice))
        resp = Response(audio, mimetype="audio/mpeg")  # MP3
        resp.headers["Content-Disposition"] = 'inline; filename="speech.mp3"'
        return resp
    except Exception as e:
        return jsonify({"error": "TTS failed", "details": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)