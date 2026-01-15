import os
import time
import random
from loguru import logger
from backend.core.config import settings
from backend.core.database import db
from backend.services.storage_manager import storage_manager

# Optional Imports with Graceful Fallback
try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None
    logger.warning("OpenCV/Numpy not found. Running in LITE MODE (Mock Processing).")

# Import specialized detectors
from backend.services.face_detector import crop_face_advanced
from backend.services.ai_detector import get_ai_prediction, get_fft_score

async def process_image_pipeline(scan_id: str, image_path: str, original_filename: str):
    logger.info(f"[{scan_id}] Image Processing Started: {image_path} ({original_filename})")
    
    # 1. Setup - Get paths
    # For images, we don't strictly need a "processed" folder for frames, 
    # but we might save the cropped face there or in thumbnails.
    thumbnail_dir = storage_manager.get_thumbnails_folder(scan_id)
    thumbnail_dir.mkdir(exist_ok=True)
    
    # We will treat the single image as one "frame" for the report structure consistency
    analyzed_frames = []
    
    # --- REAL MODE vs MOCK MODE ---
    if cv2 is None:
        logger.info(f"[{scan_id}] CV2 missing. Simulating analysis...")
        time.sleep(1)
        
        ai_conf = random.uniform(0.1, 0.95)
        fft_val = random.uniform(10, 80)
        final_verdict = "DEEPFAKE" if ai_conf > 0.5 else "REAL"
        confidence = ai_conf * 100
        
        analyzed_frames.append({
            "timestamp": 0,
            "ai_probability": ai_conf,
            "fft_anomaly": fft_val
        })
        
    else:
        try:
            # Read Image
            img = cv2.imread(str(image_path))
            if img is None:
                logger.error(f"Could not read image: {image_path}")
                return

            # A. Detect Face
            face_img, found = crop_face_advanced(img)
            
            # Determine what to analyze (Face or Full Image)
            analysis_img = None
            analysis_path = str(image_path) # Default to original if no face
            
            if found and face_img is not None and face_img.size > 0:
                # Save cropped face as a "thumbnail" or temp file to analyze
                faces_detected = 1
                face_filename = f"face_detected.jpg"
                face_path = thumbnail_dir / face_filename
                cv2.imwrite(str(face_path), face_img)
                analysis_path = str(face_path)
                analysis_img = face_img
                logger.info(f"[{scan_id}] Face detected, analyzing crop.")
            else:
                faces_detected = 0
                logger.info(f"[{scan_id}] No face detected, analyzing full image.")
                analysis_img = img

            # B. Run Intelligence
            ai_conf = get_ai_prediction(analysis_path)
            fft_val = get_fft_score(analysis_path)
            
            # C. Create Thumbnail for UI (if not already the face)
            # If we analyzed the face, we already saved it as face_detected.jpg in thumbnail_dir
            # If we analyzed full image, maybe resize for thumbnail?
            thumbnail_filename = "thumbnail.jpg"
            if found:
                # Use the face we already saved
                thumbnail_filename = f"face_detected.jpg"
            else:
                # Create a resized thumbnail of original
                thumb_path = thumbnail_dir / thumbnail_filename
                h, w = img.shape[:2]
                if w > 400:
                    scale = 400 / w
                    new_w, new_h = 400, int(h * scale)
                    thumb_img = cv2.resize(img, (new_w, new_h))
                else:
                    thumb_img = img
                cv2.imwrite(str(thumb_path), thumb_img)
            
            analyzed_frames.append({
                "timestamp": 0,
                "ai_probability": ai_conf,
                "fft_anomaly": fft_val,
                "thumbnail": thumbnail_filename
            })
            
            logger.info(f"[{scan_id}] AI Score: {ai_conf:.4f}, FFT Score: {fft_val:.2f}")

            # Weighted Logic
            final_score = (ai_conf * 100 * 0.7) + (fft_val * 0.01 * 100 * 0.3)
            confidence = min(final_score, 99.9)
            final_verdict = "DEEPFAKE" if confidence > 50 else "REAL"

        except Exception as e:
            logger.error(f"Error in image processing: {e}")
            final_verdict = "UNCERTAIN"
            confidence = 0

    # 3. Save Report
    report = {
        "scan_id": scan_id,
        "verdict": final_verdict,
        "confidence_score": round(confidence, 2),
        "total_frames_analyzed": 1, 
        "frame_data": analyzed_frames,
        "file_name": original_filename,
        "created_at": time.time(),
        "has_thumbnails": True,
        "media_type": "image" # Explicitly mark as image
    }
    
    # Save to MongoDB (Async)
    try:
        if db.db is not None:
            await db.db.scans.insert_one(report)
            logger.success(f"[{scan_id}] Saved to MongoDB Atlas")
        else:
            logger.warning("MongoDB not connected. Data NOT saved.")
    except Exception as e:
        logger.error(f"DB Save Failed: {e}")

    logger.success(f"[{scan_id}] Image Analysis Complete. Verdict: {final_verdict}")
