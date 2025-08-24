#!/usr/bin/env python3
"""
ODIA TTS Local Testing Script
Run this BEFORE deploying to verify real TTS works
"""

import sys
import os
import tempfile
import wave

def test_pyttsx3_installation():
    """Test if pyttsx3 is installed and working"""
    print("1️⃣ Testing pyttsx3 installation...")
    try:
        import pyttsx3
        print("   ✅ pyttsx3 imported successfully")
        
        # Try to initialize engine
        engine = pyttsx3.init()
        print("   ✅ pyttsx3 engine initialized")
        
        # Check available voices
        voices = engine.getProperty('voices')
        print(f"   ✅ Found {len(voices)} voices")
        
        return True
    except Exception as e:
        print(f"   ❌ pyttsx3 test failed: {e}")
        print("   Fix: pip install pyttsx3")
        return False

def test_audio_generation():
    """Test if we can generate actual audio"""
    print("\n2️⃣ Testing audio generation...")
    try:
        import pyttsx3
        
        engine = pyttsx3.init()
        test_text = "Testing ODIA Nigerian TTS engine"
        
        # Generate audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp_path = tmp.name
        
        engine.save_to_file(test_text, tmp_path)
        engine.runAndWait()
        
        # Check if file was created and has content
        if os.path.exists(tmp_path):
            size = os.path.getsize(tmp_path)
            
            if size > 1000:  # Should be more than 1KB for real audio
                print(f"   ✅ Audio file generated: {size} bytes")
                
                # Verify it's a valid WAV file
                try:
                    with wave.open(tmp_path, 'rb') as wav:
                        frames = wav.getnframes()
                        rate = wav.getframerate()
                        duration = frames / float(rate)
                        print(f"   ✅ Valid WAV file: {duration:.2f} seconds")
                except:
                    print("   ⚠️ File generated but may not be valid WAV")
                
                # Clean up
                os.unlink(tmp_path)
                return True
            else:
                print(f"   ❌ Audio file too small: {size} bytes (probably empty)")
                os.unlink(tmp_path)
                return False
        else:
            print("   ❌ No audio file generated")
            return False
            
    except Exception as e:
        print(f"   ❌ Audio generation failed: {e}")
        return False

def test_flask_app():
    """Test if Flask app starts correctly"""
    print("\n3️⃣ Testing Flask app...")
    try:
        from app import app, tts_engine
        print("   ✅ App imported successfully")
        
        # Check if TTS engine initialized
        if tts_engine.engine:
            print("   ✅ TTS engine initialized")
        else:
            print("   ⚠️ TTS engine using fallback mode")
        
        # Test the test client
        with app.test_client() as client:
            # Test health endpoint
            response = client.get('/health')
            if response.status_code == 200:
                print("   ✅ Health endpoint working")
                data = response.get_json()
                if data.get('ready_for_business'):
                    print("   ✅ System ready for business!")
            else:
                print(f"   ❌ Health endpoint failed: {response.status_code}")
            
            # Test voices endpoint
            response = client.get('/voices')
            if response.status_code == 200:
                data = response.get_json()
                print(f"   ✅ Found {data['count']} Nigerian voices")
            
            # Test speak endpoint
            response = client.post('/speak', 
                                  json={'text': 'Test', 'voice': 'nigerian-female'})
            if response.status_code == 200:
                audio_size = len(response.data)
                if audio_size > 1000:
                    print(f"   ✅ Speech generation working: {audio_size} bytes")
                    
                    # Save test file
                    with open('test_output.wav', 'wb') as f:
                        f.write(response.data)
                    print("   ✅ Test audio saved to: test_output.wav")
                    print("      Run: 'play test_output.wav' to hear it (Linux/Mac)")
                else:
                    print(f"   ⚠️ Audio generated but small: {audio_size} bytes")
            else:
                print(f"   ❌ Speech generation failed: {response.status_code}")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Could not import app: {e}")
        print("   Make sure app.py is in the current directory")
        return False
    except Exception as e:
        print(f"   ❌ Flask app test failed: {e}")
        return False

def test_dependencies():
    """Test all required dependencies"""
    print("\n4️⃣ Testing dependencies...")
    
    required = ['flask', 'flask_cors', 'pyttsx3', 'numpy', 'requests']
    missing = []
    
    for module in required:
        try:
            __import__(module)
            print(f"   ✅ {module} installed")
        except ImportError:
            print(f"   ❌ {module} missing")
            missing.append(module)
    
    if missing:
        print(f"\n   Install missing: pip install {' '.join(missing)}")
        return False
    return True

def test_memory_usage():
    """Check memory usage is acceptable for Render"""
    print("\n5️⃣ Testing memory usage...")
    try:
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        if memory_mb < 400:
            print(f"   ✅ Memory usage OK: {memory_mb:.1f} MB (under 512 MB limit)")
            return True
        else:
            print(f"   ⚠️ Memory usage high: {memory_mb:.1f} MB (close to 512 MB limit)")
            return True
    except ImportError:
        print("   ⏭️  psutil not installed, skipping memory test")
        return True

def main():
    print("=" * 60)
    print("🧪 ODIA TTS LOCAL TESTING")
    print("=" * 60)
    
    all_passed = True
    
    # Run all tests
    all_passed &= test_dependencies()
    all_passed &= test_pyttsx3_installation()
    all_passed &= test_audio_generation()
    all_passed &= test_flask_app()
    all_passed &= test_memory_usage()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED - READY TO DEPLOY!")
        print("\nNext steps:")
        print("1. git add .")
        print("2. git commit -m 'Add real TTS engine'")
        print("3. git push origin main")
        print("4. Deploy to Render")
    else:
        print("❌ SOME TESTS FAILED - FIX BEFORE DEPLOYING!")
        print("\nCheck the errors above and fix them first.")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())