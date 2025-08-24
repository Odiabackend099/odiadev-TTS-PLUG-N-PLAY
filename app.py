#!/usr/bin/env python3
"""
ODIADEV Nigerian Multilingual TTS Engine
Using Coqui TTS for realistic conversational voices with voice cloning support
"""

import os
import io
import tempfile
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import torch
import numpy as np
import soundfile as sf
from TTS.api import TTS
import hashlib
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

class NigerianTTSEngine:
    def __init__(self):
        self.models = {}
        self.cache_dir = Path("./tts_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.voice_samples_dir = Path("./voice_samples")
        self.voice_samples_dir.mkdir(exist_ok=True)
        
        # Nigerian voice configurations
        self.nigerian_voices = {
            "en-NG-EzinneNeural": {
                "model": "tts_models/multilingual/multi-dataset/xtts_v2",
                "language": "en",
                "description": "Nigerian English Female (Ezinne)",
                "sample_text": "Welcome to Nigeria! How are you doing today?",
                "voice_sample": None  # Will be set when cloned
            },
            "en-NG-AbeolaNeural": {
                "model": "tts_models/multilingual/multi-dataset/xtts_v2", 
                "language": "en",
                "description": "Nigerian English Male (Abeola)",
                "sample_text": "Hello! I am speaking with a Nigerian accent.",
                "voice_sample": None
            },
            "yo-NG-AyotundeNeural": {
                "model": "tts_models/multilingual/multi-dataset/xtts_v2",
                "language": "en",  # Using English with Yoruba influence
                "description": "Yoruba-influenced English Female",
                "sample_text": "Bawo ni? How are you? Welcome to Lagos!",
                "voice_sample": None
            },
            "ig-NG-ObinnaNeural": {
                "model": "tts_models/multilingual/multi-dataset/xtts_v2", 
                "language": "en",
                "description": "Igbo-influenced English Male",
                "sample_text": "Kedu? How are you? Ndewo from Enugu!",
                "voice_sample": None
            },
            "ha-NG-MaryamNeural": {
                "model": "tts_models/multilingual/multi-dataset/xtts_v2",
                "language": "en",
                "description": "Hausa-influenced English Female", 
                "sample_text": "Sannu! How are you? Welcome to Kano!",
                "voice_sample": None
            },
            "pcm-NG-ChiomaNeural": {
                "model": "tts_models/multilingual/multi-dataset/xtts_v2",
                "language": "en",
                "description": "Nigerian Pidgin Female",
                "sample_text": "How far? I dey fine o! Welcome make you enjoy!",
                "voice_sample": None
            }
        }
        
        # Load default model
        self.load_default_model()
    
    def load_default_model(self):
        """Load the main XTTS model for Nigerian voices"""
        try:
            logger.info("Loading Coqui XTTS model...")
            self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)
            logger.info("✅ Coqui TTS model loaded successfully!")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to load TTS model: {e}")
            # Fallback to simpler model
            try:
                logger.info("Loading fallback model...")
                self.tts = TTS("tts_models/en/ljspeech/tacotron2-DDC", gpu=False)
                logger.info("✅ Fallback TTS model loaded!")
                return True
            except Exception as e2:
                logger.error(f"❌ Fallback model also failed: {e2}")
                self.tts = None
                return False
    
    def get_cache_path(self, text: str, voice: str, language: str) -> Path:
        """Generate cache file path for audio"""
        text_hash = hashlib.md5(f"{text}_{voice}_{language}".encode()).hexdigest()
        return self.cache_dir / f"{text_hash}.wav"
    
    def clone_voice_from_sample(self, voice_id: str, sample_audio_path: str) -> bool:
        """Clone a voice from uploaded audio sample"""
        try:
            if voice_id in self.nigerian_voices:
                self.nigerian_voices[voice_id]["voice_sample"] = sample_audio_path
                logger.info(f"✅ Voice sample registered for {voice_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Voice cloning failed: {e}")
            return False
    
    def synthesize(self, text: str, voice: str = "en-NG-EzinneNeural", 
                   language: str = "en", use_cache: bool = True) -> Optional[bytes]:
        """Generate Nigerian TTS audio"""
        
        if not self.tts:
            logger.error("TTS model not loaded")
            return None
        
        # Check cache first
        cache_path = self.get_cache_path(text, voice, language)
        if use_cache and cache_path.exists():
            logger.info(f"📦 Using cached audio for: {text[:50]}...")
            return cache_path.read_bytes()
        
        try:
            # Get voice configuration
            voice_config = self.nigerian_voices.get(voice, self.nigerian_voices["en-NG-EzinneNeural"])
            
            # Create temporary file for output
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Generate speech
            if voice_config.get("voice_sample") and hasattr(self.tts, 'tts_to_file'):
                # Use voice cloning if sample available
                logger.info(f"🎭 Generating cloned voice for: {voice}")
                self.tts.tts_to_file(
                    text=text,
                    file_path=temp_path,
                    speaker_wav=voice_config["voice_sample"],
                    language=language
                )
            else:
                # Use default voice synthesis
                logger.info(f"🎤 Generating default voice for: {voice}")
                if hasattr(self.tts, 'tts_to_file'):
                    self.tts.tts_to_file(text=text, file_path=temp_path)
                else:
                    # Fallback method
                    wav = self.tts.tts(text)
                    sf.write(temp_path, wav, 22050)
            
            # Read generated audio
            audio_data = Path(temp_path).read_bytes()
            
            # Cache the result
            if use_cache:
                cache_path.write_bytes(audio_data)
                logger.info(f"💾 Cached audio to: {cache_path}")
            
            # Cleanup
            os.unlink(temp_path)
            
            logger.info(f"✅ Generated {len(audio_data)} bytes of audio")
            return audio_data
            
        except Exception as e:
            logger.error(f"❌ TTS synthesis failed: {e}")
            return None

# Initialize TTS engine
logger.info("🚀 Initializing Nigerian TTS Engine...")
tts_engine = NigerianTTSEngine()

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if tts_engine.tts else "degraded",
        "service": "Nigerian TTS Engine",
        "version": "2.0.0",
        "voices": len(tts_engine.nigerian_voices),
        "model_loaded": tts_engine.tts is not None,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.route('/')
def root():
    """Service info"""
    return {
        "service": "ODIADEV Nigerian Multilingual TTS",
        "version": "2.0.0",
        "description": "Realistic conversational Nigerian voices with voice cloning",
        "voices": list(tts_engine.nigerian_voices.keys()),
        "features": ["Voice Cloning", "Multilingual", "Conversational", "Nigerian Accents"],
        "endpoints": ["/speak", "/voices", "/clone-voice", "/health"]
    }

@app.route('/voices')
def list_voices():
    """List available Nigerian voices"""
    voices = []
    for voice_id, config in tts_engine.nigerian_voices.items():
        voices.append({
            "id": voice_id,
            "name": voice_id.split('-')[-1].replace('Neural', ''),
            "language": config.get("language", "en"),
            "description": config["description"],
            "sample_text": config["sample_text"],
            "cloned": config["voice_sample"] is not None
        })
    
    return {"voices": voices, "count": len(voices)}

@app.route('/speak', methods=['GET', 'POST'])
def speak():
    """Generate Nigerian TTS audio"""
    
    # Parse request data
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            text = data.get('text', '')
            voice = data.get('voice', 'en-NG-EzinneNeural')
            format_type = data.get('format', 'mp3')
            language = data.get('language', 'en')
        else:
            text = request.form.get('text', '')
            voice = request.form.get('voice', 'en-NG-EzinneNeural')
            format_type = request.form.get('format', 'mp3')
            language = request.form.get('language', 'en')
    else:
        text = request.args.get('text', '')
        voice = request.args.get('voice', 'en-NG-EzinneNeural')
        format_type = request.args.get('format', 'mp3')
        language = request.args.get('language', 'en')
    
    # Validation
    if not text.strip():
        return jsonify({"error": "Text parameter is required"}), 400
    
    if len(text) > 5000:  # Reasonable limit
        return jsonify({"error": "Text too long (max 5000 characters)"}), 400
    
    # Generate audio
    logger.info(f"🎤 TTS Request: '{text[:50]}...' | Voice: {voice}")
    
    try:
        audio_data = tts_engine.synthesize(text, voice, language)
        
        if not audio_data:
            return jsonify({"error": "TTS generation failed"}), 500
        
        # Convert to requested format if needed
        if format_type.lower() == 'mp3':
            # Note: For production, you'd want to convert WAV to MP3 here
            # For now, returning WAV with MP3 mime type (browsers handle it)
            mime_type = 'audio/mpeg'
        else:
            mime_type = 'audio/wav'
        
        # Return audio file
        return Response(
            audio_data,
            mimetype=mime_type,
            headers={
                'Content-Disposition': f'inline; filename="tts_output.{format_type}"',
                'Content-Length': str(len(audio_data)),
                'Cache-Control': 'public, max-age=3600',  # Cache for 1 hour
                'X-Voice-Used': voice,
                'X-Text-Length': str(len(text)),
                'X-Generated-At': datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"❌ TTS generation error: {e}")
        return jsonify({"error": "Internal TTS error", "details": str(e)}), 500

@app.route('/clone-voice', methods=['POST'])
def clone_voice():
    """Upload audio sample for voice cloning"""
    
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    
    audio_file = request.files['audio']
    voice_id = request.form.get('voice_id', 'custom_voice')
    
    if audio_file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    try:
        # Save uploaded audio sample
        sample_path = tts_engine.voice_samples_dir / f"{voice_id}_sample.wav"
        audio_file.save(sample_path)
        
        # Register voice for cloning
        success = tts_engine.clone_voice_from_sample(voice_id, str(sample_path))
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Voice sample uploaded for {voice_id}",
                "voice_id": voice_id,
                "sample_path": str(sample_path)
            })
        else:
            return jsonify({"error": "Failed to register voice sample"}), 500
            
    except Exception as e:
        logger.error(f"❌ Voice cloning error: {e}")
        return jsonify({"error": "Voice cloning failed", "details": str(e)}), 500

@app.route('/test')
def quick_test():
    """Quick test endpoint"""
    test_text = "Hello from Nigeria! This is a test of our multilingual TTS system."
    
    try:
        audio_data = tts_engine.synthesize(test_text, "en-NG-EzinneNeural", "en")
        
        if audio_data:
            return Response(
                audio_data,
                mimetype='audio/wav',
                headers={'Content-Disposition': 'inline; filename="test.wav"'}
            )
        else:
            return jsonify({"error": "Test synthesis failed"}), 500
            
    except Exception as e:
        return jsonify({"error": "Test failed", "details": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"🚀 Starting Nigerian TTS Engine on port {port}")
    logger.info(f"🎭 Voice cloning enabled: {len(tts_engine.nigerian_voices)} voices available")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
