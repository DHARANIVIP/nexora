import cv2
import numpy as np

def analyze_fft(face_path: str):
    img = cv2.imread(face_path, 0) # Grayscale
    if img is None: return 0.0

    # Perform Fast Fourier Transform
    dft = np.fft.fft2(img)
    dft_shift = np.fft.fftshift(dft)
    
    # Calculate magnitude spectrum
    magnitude_spectrum = 20 * np.log(np.abs(dft_shift) + 1)
    
    # High-pass filter logic: Real images are smooth; AIs have high-freq noise
    rows, cols = img.shape
    crow, ccol = rows//2 , cols//2
    # Mask out the low frequencies (center)
    magnitude_spectrum[crow-30:crow+30, ccol-30:ccol+30] = 0
    
    # Calculate anomaly score based on high-frequency energy
    score = np.mean(magnitude_spectrum)
    return round(float(score), 2)