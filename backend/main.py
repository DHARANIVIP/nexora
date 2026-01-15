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

from backend.services.image_processor import process_image_pipeline

@app.post("/api/analyze")
async def analyze_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # 1. Validation
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file format")
    
    # 2. Create scan folder and save file
    scan_id = uuid.uuid4().hex
    paths = storage_manager.create_scan_folder(scan_id)
    
    # Save file to temporary location first
    temp_path = paths["scan_folder"] / f"temp{ext}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Move to final location using storage manager
    # Note: save_video in storage_manager just renames/moves, so it works for images too
    # We might want to rename the method later for clarity, but it is safe.
    final_path = storage_manager.save_video(scan_id, str(temp_path), ext)
        
    # 3. Trigger Background Processing based on type
    image_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    
    if ext in image_extensions:
        logger.info(f"Triggering Image Pipeline for {scan_id}")
        background_tasks.add_task(process_image_pipeline, scan_id, str(final_path), file.filename)
    else:
        logger.info(f"Triggering Video Pipeline for {scan_id}")
        background_tasks.add_task(process_video_pipeline, scan_id, str(final_path), file.filename)
    
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
async def get_media(scan_id: str):
    """Serve media file (video or image) for a scan"""
    logger.info(f"Media Request for scan_id: {scan_id}")
    file_path = storage_manager.get_video_path(scan_id)
    
    if file_path and file_path.exists():
        logger.info(f"Serving media from: {file_path}")
        # Determine media type based on extension
        media_type = "application/octet-stream" # Default
        ext = file_path.suffix.lower()
        
        # Videos
        if ext == ".mp4": media_type = "video/mp4"
        elif ext == ".avi": media_type = "video/x-msvideo"
        elif ext == ".mov": media_type = "video/quicktime"
        elif ext == ".mkv": media_type = "video/x-matroska"
        
        # Images
        elif ext == ".jpg" or ext == ".jpeg": media_type = "image/jpeg"
        elif ext == ".png": media_type = "image/png"
        elif ext == ".webp": media_type = "image/webp"
            
        return FileResponse(str(file_path), media_type=media_type)
        
    logger.error(f"Media not found for scan_id: {scan_id}")
    raise HTTPException(status_code=404, detail="Media not found")

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