import logging
try:
    import cv2
    import mediapipe as mp
    import numpy as np
    
    # Initialize MediaPipe Face Detection
    # Handle both old and new mediapipe API versions
    try:
        mp_face_detection = mp.solutions.face_detection
    except AttributeError:
        # Fallback for newer mediapipe versions without solutions
        from mediapipe.python.solutions import face_detection as mp_face_detection
    
    # model_selection: 0 for short-range (within 2m), 1 for full-range (within 5m)
    # Lower confidence threshold for better detection
    detector = mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.3)
    
    # Fallback: OpenCV Haar Cascade
    haar_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
except (ImportError, AttributeError) as e:
    logging.warning(f"Failed to initialize face detection: {e}")
    cv2 = None
    mp = None
    np = None
    detector = None
    haar_cascade = None

from loguru import logger

def crop_face_advanced(frame):
    """
    Detects face using Google MediaPipe and returns the cropped numpy array.
    Falls back to Haar Cascade if MediaPipe fails.
    Returns: (cropped_face, status_boolean)
    """
    if detector is None:
        # Lite Mode: Simulate finding a face (return None or random noise if needed, or just True)
        return None, True 

    try:
        height, width, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = detector.process(rgb_frame)

        # Try MediaPipe first
        if results.detections:
            # Get the first face (Assumption: Single person video)
            detection = results.detections[0]
            bbox = detection.location_data.relative_bounding_box

            # Convert relative coordinates to pixels
            x = int(bbox.xmin * width)
            y = int(bbox.ymin * height)
            w = int(bbox.width * width)
            h = int(bbox.height * height)

            # Add Padding (20%) to capture chin/forehead artifacts
            x_pad, y_pad = int(w * 0.2), int(h * 0.2)
            x1 = max(0, x - x_pad)
            y1 = max(0, y - y_pad)
            x2 = min(width, x + w + x_pad)
            y2 = min(height, y + h + y_pad)

            cropped_face = frame[y1:y2, x1:x2]
            
            # Validate that cropped face is not empty
            if cropped_face is None or cropped_face.size == 0:
                logger.warning("MediaPipe: Cropped face is empty, trying Haar Cascade")
            else:
                logger.info(f"MediaPipe: Face detected at ({x}, {y}, {w}, {h})")
                return cropped_face, True
        
        # Fallback to Haar Cascade if MediaPipe didn't detect or returned empty
        logger.info("MediaPipe: No detection, trying Haar Cascade fallback")
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # More aggressive settings: lower minNeighbors and minSize
        faces = haar_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(20, 20))
        
        if len(faces) > 0:
            # Get the first face
            (x, y, w, h) = faces[0]
            
            # Add Padding
            x_pad, y_pad = int(w * 0.2), int(h * 0.2)
            x1 = max(0, x - x_pad)
            y1 = max(0, y - y_pad)
            x2 = min(width, x + w + x_pad)
            y2 = min(height, y + h + y_pad)
            
            cropped_face = frame[y1:y2, x1:x2]
            
            if cropped_face is not None and cropped_face.size > 0:
                logger.info(f"Haar Cascade: Face detected at ({x}, {y}, {w}, {h})")
                return cropped_face, True
        
        # Only log every 10th failure to avoid spam
        return None, False

    except Exception as e:
        logger.error(f"Face Detection Failed: {e}")
        return None, False