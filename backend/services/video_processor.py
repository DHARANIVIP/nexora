import os
import json
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

# Import services (which now also handle missing deps)
from backend.services.face_detector import crop_face_advanced
from backend.services.ai_detector import get_ai_prediction, get_fft_score

async def process_video_pipeline(scan_id: str, video_path: str, original_filename: str):
    logger.info(f"[{scan_id}] Processing Started: {video_path} ({original_filename})")
    
    # 1. Setup - Get paths from storage manager
    frame_save_dir = storage_manager.get_processed_folder(scan_id)
    frame_save_dir.mkdir(exist_ok=True)
    
    # Get thumbnails directory for this scan
    thumbnail_dir = storage_manager.get_thumbnails_folder(scan_id)
    thumbnail_dir.mkdir(exist_ok=True)
    
    analyzed_frames = []
    fake_accumulated_score = 0
    fft_accumulated_score = 0
    count = 0
    thumbnails = []
    
    # --- MOCK MODE (If OpenCV is missing) ---
    if cv2 is None:
        logger.info(f"[{scan_id}] CV2 missing. Simulating analysis...")
        time.sleep(3) 
        
        # Generator fake frame data
        for i in range(5):
            ai_conf = random.uniform(0.1, 0.95)
            fft_val = random.uniform(10, 80)
            analyzed_frames.append({
                "timestamp": i * 1.0,
                "ai_probability": ai_conf,
                "fft_anomaly": fft_val
            })
            fake_accumulated_score += ai_conf
            fft_accumulated_score += fft_val
            count += 1
            
    # --- REAL MODE ---
    else:
        try:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                logger.error(f"Could not open video: {video_path}")
                return

            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            skip_rate = int(fps) 
            current_frame = 0
            faces_detected = 0
            
            logger.info(f"[{scan_id}] Video: {total_frames} frames, {fps} fps, analyzing every {skip_rate} frames")
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret: break
                
                if current_frame % skip_rate == 0:
                    # A. Detect Face
                    face_img, found = crop_face_advanced(frame)
                    
                    # If face detected, use it; otherwise use full frame as fallback
                    analysis_img = None
                    analysis_path = None
                    
                    if found and face_img is not None and face_img.size > 0:
                        # Face detected - use cropped face
                        faces_detected += 1
                        face_filename = f"face_{current_frame}.jpg"
                        analysis_path = frame_save_dir / face_filename
                        cv2.imwrite(str(analysis_path), face_img)
                        analysis_img = face_img
                    else:
                        # No face detected - use full frame as fallback
                        logger.info(f"[{scan_id}] Frame {current_frame}: No face, using full frame")
                        frame_filename = f"frame_{current_frame}.jpg"
                        analysis_path = frame_save_dir / frame_filename
                        # Resize frame to reasonable size for analysis
                        resized_frame = cv2.resize(frame, (640, 480))
                        cv2.imwrite(str(analysis_path), resized_frame)
                        analysis_img = resized_frame
                    
                    # B. Run Intelligence (on either face or full frame)
                    if analysis_path is not None:
                        ai_conf = get_ai_prediction(str(analysis_path))
                        fft_val = get_fft_score(str(analysis_path))
                        
                        # C. Save thumbnail for report
                        thumbnail_filename = f"thumb_{count}.jpg"
                        thumbnail_path = thumbnail_dir / thumbnail_filename
                        # Create smaller thumbnail (max 400px width)
                        if analysis_img is not None:
                            h, w = analysis_img.shape[:2]
                            if w > 400:
                                scale = 400 / w
                                new_w, new_h = 400, int(h * scale)
                                thumbnail_img = cv2.resize(analysis_img, (new_w, new_h))
                            else:
                                thumbnail_img = analysis_img
                            cv2.imwrite(str(thumbnail_path), thumbnail_img)
                            thumbnails.append(thumbnail_filename)
                        
                        analyzed_frames.append({
                            "timestamp": round(current_frame / fps, 2),
                            "ai_probability": ai_conf,
                            "fft_anomaly": fft_val,
                            "thumbnail": thumbnail_filename
                        })
                        
                        fake_accumulated_score += ai_conf
                        fft_accumulated_score += fft_val
                        count += 1
                        
                current_frame += 1

            cap.release()
            logger.info(f"[{scan_id}] Processed {current_frame} frames, detected {faces_detected} faces, analyzed {count} frames")
        except Exception as e:
            logger.error(f"Error in video processing loop: {e}")

    # 2. Final Verdict Logic
    logger.info(f"[{scan_id}] Verdict Calculation: {count} faces analyzed")
    
    if count == 0:
        final_verdict = "UNCERTAIN"
        confidence = 0
        logger.warning(f"[{scan_id}] No faces analyzed, verdict: UNCERTAIN")
    else:
        avg_ai = fake_accumulated_score / count
        avg_fft = fft_accumulated_score / count
        
        logger.info(f"[{scan_id}] Accumulated AI Score: {fake_accumulated_score:.2f}, Avg: {avg_ai:.4f}")
        logger.info(f"[{scan_id}] Accumulated FFT Score: {fft_accumulated_score:.2f}, Avg: {avg_fft:.2f}")
        
        # Weighted Logic: AI is 70% important, Math is 30%
        final_score = (avg_ai * 100 * 0.7) + (avg_fft * 0.01 * 100 * 0.3)
        confidence = min(final_score, 99.9)
        final_verdict = "DEEPFAKE" if confidence > 50 else "REAL"
        
        logger.success(f"[{scan_id}] Final Score: {final_score:.2f}, Confidence: {confidence:.2f}%, Verdict: {final_verdict}")

    # 3. Save Report
    report = {
        "scan_id": scan_id,
        "verdict": final_verdict,
        "confidence_score": round(confidence, 2),
        "total_frames_analyzed": count,
        "frame_data": analyzed_frames,
        "file_name": original_filename,
        "created_at": time.time(),
        "has_thumbnails": len(thumbnails) > 0,
        "media_type": "video"
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

    # 4. Cleanup Temporary Files using storage manager
    try:
        # Delete extracted frames folder (but keep thumbnails and video)
        storage_manager.cleanup_scan(scan_id, keep_video=True, keep_thumbnails=True)
        logger.info(f"[{scan_id}] Cleanup successful (Frames cleared, {len(thumbnails)} thumbnails saved, Video kept)")
    except Exception as e:
        logger.error(f"Cleanup Failed: {e}")

    logger.success(f"[{scan_id}] Analysis Complete. Verdict: {final_verdict}")