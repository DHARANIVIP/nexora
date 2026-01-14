from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger
import shutil
import uuid
import os
import json

from backend.core.config import settings
from backend.services.video_processor import process_video_pipeline
from backend.services.storage_manager import storage_manager

app = FastAPI(title="Nexora Deepfake Defense API", version="2.0")

# CORS (Allow Frontend to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.core.database import db

@app.on_event("startup")
async def startup_event():
    logger.info("Nexora API Starting up...")
    db.connect()

@app.on_event("shutdown")
async def shutdown_event():
    db.close()

# --- serve static files ---
# Mount the assets folder (JS/CSS)
app.mount("/assets", StaticFiles(directory="dist/assets"), name="assets")
# Mount scans folder to serve all scan-related files
app.mount("/scans", StaticFiles(directory=settings.SCANS_FOLDER), name="scans")

# API Routes

@app.post("/api/analyze")
async def analyze_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # 1. Validation
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid video format")
    
    # 2. Create scan folder and save file
    scan_id = uuid.uuid4().hex
    paths = storage_manager.create_scan_folder(scan_id)
    
    # Save video to temporary location first
    temp_path = paths["scan_folder"] / f"temp{ext}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Move to final location using storage manager
    video_path = storage_manager.save_video(scan_id, str(temp_path), ext)
        
    # 3. Trigger Background Processing
    background_tasks.add_task(process_video_pipeline, scan_id, str(video_path), file.filename)
    
    return {
        "scan_id": scan_id,
        "message": "Upload successful. Analysis running in background.",
        "status_url": f"/api/results/{scan_id}"
    }

@app.get("/api/scans")
async def get_scans():
    if db.db is not None:
        try:
            # Fetch all scans, sort by newest first
            cursor = db.db.scans.find({}, {"_id": 0}).sort("created_at", -1)
            scans = await cursor.to_list(length=100) # Limit to 100 recent
            return scans
        except Exception as e:
            logger.error(f"DB Read Error: {e}")
            raise HTTPException(status_code=500, detail="Database Error")
    return []

@app.get("/api/results/{scan_id}")
async def get_results(scan_id: str):
    # 1. Try DB (Sole Source of Truth)
    if db.db is not None:
        try:
            report = await db.db.scans.find_one({"scan_id": scan_id}, {"_id": 0})
            if report:
                return report
        except Exception as e:
            logger.error(f"DB Read Error: {e}")
            raise HTTPException(status_code=500, detail="Database Error")

    # If we are here, it's either not connected or not found
    return {"status": "PROCESSING", "message": "Analysis in progress or ID not found..."}

@app.get("/api/video/{scan_id}")
async def get_video(scan_id: str):
    """Serve video file for a scan, automatically detecting the extension"""
    logger.info(f"Video Request for scan_id: {scan_id}")
    video_path = storage_manager.get_video_path(scan_id)
    
    if video_path and video_path.exists():
        logger.info(f"Serving video from: {video_path}")
        # Determine media type based on extension
        media_type = "video/mp4"  # Default
        if video_path.suffix.lower() == ".avi":
            media_type = "video/x-msvideo"
        elif video_path.suffix.lower() == ".mov":
            media_type = "video/quicktime"
        elif video_path.suffix.lower() == ".mkv":
            media_type = "video/x-matroska"
            
        return FileResponse(str(video_path), media_type=media_type)
        
    logger.error(f"Video not found for scan_id: {scan_id}")
    raise HTTPException(status_code=404, detail="Video not found")

# --- SPA Catch-All ---

@app.get("/")
async def serve_index():
    return FileResponse("dist/index.html")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # Security: prevent traversing up
    if ".." in full_path:
        raise HTTPException(status_code=404)
        
    file_path = f"dist/{full_path}"
    
    # If it is a file, serve it directly
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # Otherwise, for client-side routing, serve index.html
    return FileResponse("dist/index.html")