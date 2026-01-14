import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 1. Load Env
env_path = Path(__file__).parent / 'backend' / '.env'
print(f"Loading .env from: {env_path}")
load_dotenv(env_path)

token = os.getenv("HF_TOKEN")
print(f"HF_TOKEN found: {'YES' if token else 'NO'}")
if token:
    print(f"Token length: {len(token)}")
    print(f"Token prefix: {token[:4]}...")

# 2. Try Import
try:
    from huggingface_hub import InferenceClient
    print("InferenceClient imported successfully")
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)

# 3. Try Init
if token:
    try:
        client = InferenceClient(provider="hf-inference", api_key=token)
        print("InferenceClient initialized successfully")
        
    except Exception as e:
        print(f"InferenceClient init failed: {e}")
else:
    print("Skipping client init (no token)")
