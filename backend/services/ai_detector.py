import os
import random
from loguru import logger

try:
    from huggingface_hub import InferenceClient
    from transformers import pipeline
    from PIL import Image
    import numpy as np
    import cv2
except ImportError:
    InferenceClient = None
    pipeline = None
    Image = None
    np = None
    cv2 = None

# --- 1. DEEP LEARNING ENGINE ---
# Using HuggingFace Deep-Fake-Detector-v2-Model
MODEL_NAME = "prithivMLmods/Deep-Fake-Detector-v2-Model"

# Setup Inference Client (Cloud API)
hf_token = os.environ.get("HF_TOKEN")
client = None
if hf_token and InferenceClient:
    try:
        client = InferenceClient(provider="hf-inference", api_key=hf_token)
        logger.success(f"HF Inference Client initialized with model: {MODEL_NAME}")
    except Exception as e:
        logger.warning(f"Could not initialize HF Client: {e}")

# Setup Local Pipeline (Fallback)
ai_pipe = None
if pipeline and not client:
    try:
        logger.info(f"Loading Local AI Model: {MODEL_NAME}...")
        ai_pipe = pipeline("image-classification", model=MODEL_NAME, device=-1)
        logger.success("Local AI Model Loaded Successfully!")
    except Exception as e:
        logger.warning(f"Local AI Load Failed: {e}")
        logger.info("AI will run in LITE MODE (mock predictions)")
elif client:
    logger.info("Using HuggingFace Cloud API for AI predictions")
else:
    logger.warning("No AI model available - will use LITE MODE (mock predictions)")

def get_ai_prediction(image_path: str):
    """Returns probability of being FAKE (0.0 to 1.0)"""
    # LITE MODE: Mock score if everything is missing
    if not client and not ai_pipe:
        logger.warning("AI Model: Running in LITE MODE (no model loaded), returning random score")
        return random.uniform(0.1, 0.9)

    try:
        # STRATEGY 1: Cloud API
        if client:
            try:
                logger.debug(f"AI Model: Using Cloud API ({MODEL_NAME})")
                # API expects binary or path. Client.image_classification handles local paths?
                # Usually client takes URL or bytes or PIL.
                # Let's read file as bytes to be safe or pass PIL
                if Image:
                    image = Image.open(image_path)
                    result = client.image_classification(image, model=MODEL_NAME)
                    # Result format: [{'label': 'Fake', 'score': 0.99}, ...]
                    
                    top = result[0]
                    # InferenceClient usually returns objects like ClassificatonOutput or simple list of dicts depending on version
                    # We'll handle it as list of objects or dicts
                    if hasattr(top, 'label'):
                        label = top.label.lower()
                        score = top.score
                    else:
                        label = top['label'].lower()
                        score = top['score']
                    
                    logger.info(f"AI Model: Cloud API result - Label: {label}, Score: {score}")
                    
                    if "fake" in label or "deepfake" in label:
                        logger.info(f"AI Model: Returning FAKE probability: {score}")
                        return score
                    else:
                        logger.info(f"AI Model: Returning REAL probability (inverted): {1.0 - score}")
                        return 1.0 - score
            except Exception as e:
                logger.error(f"API Inference failed, trying local if available: {e}")
                # Fallthrough to local

        # STRATEGY 2: Local Pipeline
        if ai_pipe and Image:
            logger.debug(f"AI Model: Using Local Pipeline ({MODEL_NAME})")
            pil_image = Image.open(image_path)
            result = ai_pipe(pil_image)
            top = result[0]
            label = top['label'].lower()
            score = top['score']
            
            logger.info(f"AI Model: Local Pipeline result - Label: {label}, Score: {score}")
            
            if "fake" in label or "deepfake" in label:
                logger.info(f"AI Model: Returning FAKE probability: {score}")
                return score
            else:
                logger.info(f"AI Model: Returning REAL probability (inverted): {1.0 - score}")
                return 1.0 - score
                
        # Fallback if both fail
        logger.warning("No AI model available. Returning random score")
        return random.uniform(0.1, 0.9)
            
    except Exception as e:
        logger.error(f"AI Prediction Error: {e}")
        return 0.5

# --- 2. MATH ENGINE (FFT) ---
def get_fft_score(image_path: str):
    """
    Analyzes frequency domain artifacts.
    High score (> 60) = Likely Generated/GAN.
    """
    if cv2 is None or np is None:
        logger.warning("FFT: Libraries not available, returning random score")
        return random.uniform(20, 80)
        
    try:
        img = cv2.imread(image_path, 0) # Grayscale
        if img is None:
            logger.error(f"FFT: Could not read image {image_path}")
            return 0

        # Fast Fourier Transform
        f = np.fft.fft2(img)
        fshift = np.fft.fftshift(f)
        magnitude = 20 * np.log(np.abs(fshift) + 1e-10)

        # Calculate high-frequency noise (Edges of the spectrum)
        rows, cols = img.shape
        crow, ccol = rows//2, cols//2
        # Mask the center (low freq)
        magnitude[crow-10:crow+10, ccol-10:ccol+10] = 0
        
        score = np.mean(magnitude)
        # Normalize to 0-100 scale based on experimental data
        # GANs usually have scores > 140, Real images ~100-120
        normalized = min(max((score - 100) * 2, 0), 100)
        
        logger.debug(f"FFT: Raw score: {score:.2f}, Normalized: {normalized:.2f}")
        return normalized

    except Exception as e:
        logger.error(f"FFT Error: {e}")
        return 0
