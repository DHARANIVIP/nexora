import requests
import os
import time

# Use the uploaded image path
IMAGE_PATH = r"C:/Users/DHARANI/.gemini/antigravity/brain/1edb280d-c264-496d-a427-4286dac7a26d/uploaded_image_1768455605168.png"
API_URL = "http://localhost:8000/api/analyze"

def test_image_upload():
    if not os.path.exists(IMAGE_PATH):
        print(f"Error: Image not found at {IMAGE_PATH}")
        return

    print(f"Uploading {IMAGE_PATH}...")
    
    with open(IMAGE_PATH, "rb") as f:
        files = {"file": ("test_image.png", f, "image/png")}
        try:
            response = requests.post(API_URL, files=files)
            if response.status_code == 200:
                data = response.json()
                scan_id = data.get("scan_id")
                print(f"Upload Success! Scan ID: {scan_id}")
                return scan_id
            else:
                print(f"Upload Failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Request Error: {e}")

def check_results(scan_id):
    print(f"Checking results for {scan_id}...")
    url = f"http://localhost:8000/api/results/{scan_id}"
    
    for i in range(10):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "PROCESSING":
                    print("Processing...")
                else:
                    print("\n--- ANALYSIS COMPLETE ---")
                    print(f"Verdict: {data.get('verdict')}")
                    print(f"Confidence: {data.get('confidence_score')}")
                    print(f"Media Type: {data.get('media_type')}")
                    print(f"Has Thumbnails: {data.get('has_thumbnails')}")
                    return
            else:
                print(f"Error checking results: {response.status_code}")
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(2)

if __name__ == "__main__":
    scan_id = test_image_upload()
    if scan_id:
        check_results(scan_id)
