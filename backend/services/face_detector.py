import cv2
import os
import uuid

# Load the built-in OpenCV face model
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def crop_face(frame_path: str, output_folder: str):
    img = cv2.imread(frame_path)
    if img is None: return None

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(100, 100))

    if len(faces) == 0:
        return None 

    # Pick the largest face in the frame
    x, y, w, h = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)[0]
    
    # Add 15% padding for better AI context
    padding = int(w * 0.15)
    y1, y2 = max(0, y-padding), min(img.shape[0], y+h+padding)
    x1, x2 = max(0, x-padding), min(img.shape[1], x+w+padding)
    
    face_img = img[y1:y2, x1:x2]
    face_path = os.path.join(output_folder, f"face_{uuid.uuid4().hex[:6]}.jpg")
    cv2.imwrite(face_path, face_img)
    return face_path