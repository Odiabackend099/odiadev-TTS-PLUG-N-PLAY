#!/usr/bin/env python3
"""
ODIADEV Nigerian TTS Engine - Comprehensive Tester
Test your deployed TTS engine with various Nigerian voices and languages
"""

import requests
import json
import time
import sys
import os
from pathlib import Path

class NigerianTTSTester:
    def __init__(self, base_url="https://nigerian-tts-engine.onrender.com"):
        self.base_url = base_url.rstrip('/')
        self.test_phrases = {
            "english": "Hello Nigeria! Welcome to our multilingual TTS platform.",
            "yoruba_english": "Bawo ni? How are you doing? Welcome to Lagos!",
            "igbo_english": "Kedu ka i mere? How are you? Ndewo from Enugu!",
            "hausa_english": "Sannu! How are you today? Welcome to Kano!",
            "pidgin": "How far? I dey fine o! Make we enjoy this thing!",
            "professional": "Good morning. This is a professional announcement from ODIADEV Technologies.",
            "conversational": "Hey! What's up? I hope you're having a great day in Nigeria!"
        }
        
        self.nigerian_voices = [
            "en-NG-EzinneNeural",
            "en-NG-AbeolaNeural", 
            "yo-NG-AyotundeNeural",
            "ig-NG-ObinnaNeural",
            "ha-NG-MaryamNeural",
            "pcm-NG-ChiomaNeural"
        ]
    
    def test_health(self):
        """Test if the TTS engine is healthy"""
        print("🏥 Testing TTS Engine Health...")
        print("-" * 40)
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                print("✅ TTS Engine is healthy!")
                print(f"   Service: {health_data.get('service', 'Unknown')}")
                print(f"   Version: {health_data.get('version', 'Unknown')}")
                print(f"   Model Loaded: {health_data.get('model_loaded', False)}")
                print(f"   Available Voices: {health_data.get('voices', 0)}")
                return True
            else:
                print(f"❌ Health check failed: HTTP {response.status_code}")
                return False
                
        except requests.RequestException as e:
            print(f"❌ Cannot reach TTS engine: {e}")
            return False
    
    def test_voices_endpoint(self):
        """Test the voices listing endpoint"""
        print("\n🎤 Testing Available Voices...")
        print("-" * 40)
        
        try:
            response = requests.get(f"{self.base_url}/voices", timeout=10)
            
            if response.status_code == 200:
                voices_data = response.json()
                voices = voices_data.get('voices', [])
                
                print(f"✅ Found {len(voices)} Nigerian voices:")
                for voice in voices:
                    cloned_status = "🎭 Cloned" if voice.get('cloned') else "🔊 Default"
                    print(f"   • {voice['id']}: {voice['description']} {cloned_status}")
                
                return voices
            else:
                print(f"❌ Voices endpoint failed: HTTP {response.status_code}")
                return []
                
        except requests.RequestException as e:
            print(f"❌ Voices endpoint error: {e}")
            return []
    
    def test_tts_generation(self, text, voice, save_audio=True):
        """Test TTS generation with a specific voice"""
        print(f"\n🎵 Testing TTS: {voice}")
        print(f"   Text: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        print("-" * 40)
        
        try:
            # Test with GET method (simpler)
            params = {
                'text': text,
                'voice': voice,
                'format': 'wav',
                'language': 'en'
            }
            
            start_time = time.time()
            response = requests.get(f"{self.base_url}/speak", params=params, timeout=60)
            generation_time = time.time() - start_time
            
            if response.status_code == 200:
                audio_size = len(response.content)
                
                # Save audio file if requested
                if save_audio:
                    filename = f"test_{voice}_{int(time.time())}.wav"
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    
                    print(f"✅ TTS Success!")
                    print(f"   Audio Size: {audio_size:,} bytes")
                    print(f"   Generation Time: {generation_time:.2f}s")
                    print(f"   Saved as: {filename}")
                    
                    # Try to play on Windows
                    if os.name == 'nt':
                        try:
                            os.startfile(filename)
                        except:
                            pass
                else:
                    print(f"✅ TTS Success! ({audio_size:,} bytes in {generation_time:.2f}s)")
                
                return True
                
            else:
                print(f"❌ TTS failed: HTTP {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('error', 'Unknown error')}")
                except:
                    print(f"   Raw response: {response.text[:200]}")
                return False
                
        except requests.RequestException as e:
            print(f"❌ TTS request failed: {e}")
            return False
    
    def test_voice_cloning_endpoint(self):
        """Test voice cloning capabilities (without actually uploading)"""
        print("\n🎭 Testing Voice Cloning Endpoint...")
        print("-" * 40)
        
        try:
            # Test with empty request to see if endpoint exists
            response = requests.post(f"{self.base_url}/clone-voice", timeout=10)
            
            if response.status_code == 400:
                # Expected - we didn't send audio
                error_data = response.json()
                if "audio" in error_data.get("error", ""):
                    print("✅ Voice cloning endpoint is available!")
                    print("   You can upload audio samples to train custom voices")
                    return True
            
            print(f"⚠️  Voice cloning endpoint responded with: {response.status_code}")
            return False
            
        except requests.RequestException as e:
            print(f"❌ Voice cloning endpoint error: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run all tests"""
        print("🇳🇬 ODIADEV NIGERIAN TTS ENGINE - COMPREHENSIVE TEST")
        print("=" * 60)
        print(f"Testing: {self.base_url}")
        print("=" * 60)
        
        # Step 1: Health check
        if not self.test_health():
            print("\n❌ CRITICAL: TTS engine is not healthy!")
            print("   Check your deployment and try again.")
            return False
        
        # Step 2: Test voices endpoint
        available_voices = self.test_voices_endpoint()
        
        # Step 3: Test voice cloning endpoint
        self.test_voice_cloning_endpoint()
        
        # Step 4: Test TTS generation with different voices and texts
        test_results = []
        
        for i, (phrase_type, text) in enumerate(self.test_phrases.items()):
            # Test with first available voice or default
            voice = available_voices[0]['id'] if available_voices else "en-NG-EzinneNeural"
            
            success = self.test_tts_generation(
                text, 
                voice, 
                save_audio=(i < 3)  # Save only first 3 for testing
            )
            test_results.append(success)
        
        # Step 5: Test multiple voices with same text
        test_text = "Hello from Nigeria! This is a test of our TTS system."
        
        for voice in self.nigerian_voices[:3]:  # Test first 3 voices
            success = self.test_tts_generation(test_text, voice, save_audio=False)
            test_results.append(success)
        
        # Summary
        successful_tests = sum(test_results)
        total_tests = len(test_results)
        
        print("\n" + "=" * 60)
        print("🏁 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Successful: {successful_tests}/{total_tests}")
        print(f"❌ Failed: {total_tests - successful_tests}/{total_tests}")
        
        if successful_tests >= (total_tests * 0.8):  # 80% success rate
            print("🎉 EXCELLENT! Your Nigerian TTS engine is working well!")
            print("\n🎯 NEXT STEPS:")
            print("   1. Integrate with your AI agents and projects")
            print("   2. Upload voice samples for cloning")
            print("   3. Test with longer texts and conversations")
            print("   4. Monitor performance in production")
        else:
            print("⚠️  Some tests failed. Check the errors above.")
            print("\n🔧 TROUBLESHOOTING:")
            print("   1. Check Render logs for errors")
            print("   2. Verify all dependencies are installed")
            print("   3. Ensure enough memory/storage on Render")
        
        return successful_tests >= (total_tests * 0.8)

def main():
    """Main function"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        # Try both possible URLs
        possible_urls = [
            "https://nigerian-tts-engine.onrender.com",
            "https://odiadev-tts-plug-n-play.onrender.com"
        ]
        
        base_url = None
        for url in possible_urls:
            try:
                response = requests.get(f"{url}/health", timeout=5)
                if response.status_code == 200:
                    base_url = url
                    break
            except:
                continue
        
        if not base_url:
            print("❌ Could not find a working TTS engine at the expected URLs")
            print("   Please specify the URL manually:")
            print(f"   python {sys.argv[0]} https://your-tts-engine.onrender.com")
            return 1
    
    print(f"🎯 Testing Nigerian TTS Engine at: {base_url}")
    
    tester = NigerianTTSTester(base_url)
    success = tester.run_comprehensive_test()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
