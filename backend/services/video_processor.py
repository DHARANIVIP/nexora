import cv2
import os
import json
from services.face_detector import crop_face
from services.ai_detector import analyze_deepfake
from services.math_detector import analyze_fft
from services.report_generator import create_pdf_report

def process_video_pipeline(scan_id: str, video_path: str):
    # Setup Output
    output_dir = f"storage/processed/{scan_id}"
    os.makedirs(output_dir, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
    frame_interval = fps # Analyze 1 frame per second
    
    all_ai_scores = []
    all_fft_scores = []
    frame_count = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        
        if frame_count % frame_interval == 0:
            temp_frame = os.path.join(output_dir, f"raw_{frame_count}.jpg")
            cv2.imwrite(temp_frame, frame)
            
            # PIPELINE: Frame -> Face -> AI -> Math
            face_path = crop_face(temp_frame, output_dir)
            if face_path:
                ai_res = analyze_deepfake(face_path)
                fft_res = analyze_fft(face_path)
                
                all_ai_scores.append(ai_res['score'])
                all_fft_scores.append(fft_res)
            
            os.remove(temp_frame) # Clean up raw frame to save space
        frame_count += 1
    
    cap.release()
    
    # Calculate Final Stats
    if not all_ai_scores: return {"error": "No faces detected"}
    
    avg_ai = sum(all_ai_scores) / len(all_ai_scores)
    avg_fft = sum(all_fft_scores) / len(all_fft_scores)
    
    final_result = {
        "verdict": "DEEPFAKE" if avg_ai > 0.5 else "AUTHENTIC",
        "confidence": round(avg_ai * 100, 2),
        "fft_score": round(avg_fft, 2)
    }
    
    # Save results for Frontend to find
    with open(f"storage/results/{scan_id}.json", 'w') as f:
        json.dump(final_result, f)
        
    # Generate PDF
    create_pdf_report(scan_id, final_result)
    print(f"--- Scan {scan_id} Completed ---")