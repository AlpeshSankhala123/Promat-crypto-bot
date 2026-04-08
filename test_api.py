from config import validate_config, display_config

print("Testing configuration...")
display_config()

if validate_config():
    print("✅ All configurations are correct!")
else:
    print("❌ Please fix the errors above")