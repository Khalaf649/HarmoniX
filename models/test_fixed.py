# models/test_fixed.py
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

print("🔍 Checking files after rename...")
print("Files in directory:", [f for f in os.listdir('.') if f.endswith('.py')])

try:
    # Test individual imports
    import model_manager
    print("✅ model_manager imported successfully")
    
    import ai_models
    print("✅ ai_models imported successfully")
    
    import audio_utils
    print("✅ audio_utils imported successfully")
    
    import performance
    print("✅ performance imported successfully")
    
    # Now try the main API
    from integration_api import ai_models_api
    print("✅ integration_api imported successfully")
    
    print("\n🎯 Running full test...")
    
    # Test the API
    modes = ai_models_api.get_available_modes()
    print(f"Available modes: {modes}")
    
    for mode in modes:
        sliders = ai_models_api.switch_mode(mode)
        print(f"✅ {mode}: {sliders}")
    
    test_audio = ai_models_api.create_test_audio(duration=1)
    processed = ai_models_api.process_audio(test_audio, [1.0, 0.5, 0.3, 0.8])
    print(f"✅ Audio processing: Input {len(test_audio)} → Output {len(processed)}")
    
    print("\n🎉 SUCCESS! All systems working!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()