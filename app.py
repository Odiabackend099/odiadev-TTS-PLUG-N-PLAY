import os, tempfile, time, json
from datetime import datetime, timezone
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from gtts import gTTS

app = Flask(__name__)
CORS(app)

# Optional auth: set VALID_API_KEYS="key1,key2"
VALID_KEYS = set(k.strip() for k in os.getenv("VALID_API_KEYS","").split(",") if k.strip())
DEFAULT_TLDS = [os.getenv("GTTS_TLD","com"), "co.uk", "co.za", "com.au", "ie"]

VOICE_TO_TLD = {
    "nigerian-female": "com",
    "nigerian-male":   "com",
    "en-NG-EzinneNeural": "com",
    "en-NG-AbeoNeural":   "com",
}

def _authorized():
    return (not VALID_KEYS) or (request.headers.get("x-api-key","") in VALID_KEYS)

def _pick_tlds(voice, override_tld):
    # allow ?tld=co.uk for quick experiments
    if override_tld:
        return [override_tld] + [t for t in DEFAULT_TLDS if t != override_tld]
    base = VOICE_TO_TLD.get(voice or "", "com")
    ordered = [base] + [t for t in DEFAULT_TLDS if t != base]
    # de-dup preserving order
    seen, out = set(), []
    for t in ordered:
        if t not in seen:
            out.append(t); seen.add(t)
    return out

def _speak_gtts(text, tlds, retries=2, timeout=20):
    last_err = None
    for tld in tlds:
        for attempt in range(retries+1):
            try:
                tts = gTTS(text=text, lang="en", tld=tld, timeout=timeout)
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmpf:
                    tmp_path = tmpf.name
                try:
                    tts.save(tmp_path)
                    with open(tmp_path, "rb") as f:
                        return f.read(), {"engine":"gTTS","format":"mp3","tld":tld,"attempt":attempt}
                finally:
                    try: os.remove(tmp_path)
                    except: pass
            except Exception as e:
                last_err = f"{type(e).__name__}: {e}"
                # tiny backoff
                time.sleep(0.4 * (attempt+1))
    raise RuntimeError(last_err or "Unknown gTTS error")

@app.get("/health")
def health():
    return jsonify({
        "service": "ODIADEV Nigerian TTS (gTTS)",
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "voices_available": list(VOICE_TO_TLD.keys())
    }), 200

@app.get("/voices")
def voices():
    return jsonify([
        {"id": vid, "description": f"gTTS English (TLD preference: {tld})"}
        for vid, tld in VOICE_TO_TLD.items()
    ]), 200

@app.get("/speak")
def speak():
    # Auth first
    if not _authorized():
        return jsonify({"error":"Unauthorized","hint":"send x-api-key header with a valid key"}), 401

    text = (request.args.get("text") or "").strip()
    voice = request.args.get("voice","nigerian-female")
    tld_override = (request.args.get("tld") or "").strip()

    if not text:
        return jsonify({"error":"Missing 'text'"}), 400
    if len(text) > 2000:
        return jsonify({"error":"Text too long (max 2000 chars)"}), 413

    try:
        audio, meta = _speak_gtts(text, _pick_tlds(voice, tld_override))
        resp = Response(audio, mimetype="audio/mpeg")
        resp.headers["Content-Disposition"] = 'inline; filename="speech.mp3"'
        # Lightweight debug metadata for clients
        resp.headers["X-ODIADEV-TTS"] = json.dumps(meta)
        return resp
    except RuntimeError as e:
        # gTTS/network issues  502 so clients can retry
        return jsonify({"error":"Upstream TTS failed","details":str(e),"engine":"gTTS"}), 502
    except Exception as e:
        return jsonify({"error":"TTS failed","details":str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT","10000"))
    app.run(host="0.0.0.0", port=port)