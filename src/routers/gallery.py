from datetime import datetime
from pathlib import Path

import cv2
from controllers.camera import CameraController
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse

from helpers.logger import logger

camera = CameraController()

def create_router(_, sio):
    router = APIRouter()

    @router.get("/api/recordings")
    async def list_recordings():
        recordings_dir = Path("media/recordings")
        files = []
        
        if recordings_dir.exists():
            for f in recordings_dir.glob("*.avi"):
                stat = f.stat()
                files.append({"filename": f.name, "size_mb": round(stat.st_size / 1024 / 1024, 2), "created": datetime.fromtimestamp(stat.st_mtime).isoformat(), "url": f"/recordings/{f.name}"})
        
        return { "recordings": sorted(files, key=lambda x: x['created'], reverse=True) }

    @router.get("/recordings/{filename}")
    async def get_recording(filename: str):
        filepath = Path("recordings") / filename
        
        if filepath.exists() and filepath.suffix == '.avi':
            return FileResponse(filepath, media_type='video/x-msvideo')
        
        raise HTTPException(status_code=404, detail="Recording not found")

    @router.get("/api/snapshots")
    async def list_snapshots(page: int = 1, limit: int = 20, sort: str = "newest"):
        snapshots_dir = Path("media/snapshots")
        
        if not snapshots_dir.exists():
            snapshots_dir.mkdir(parents=True, exist_ok=True)
            return {"snapshots": [], "total": 0, "page": page, "has_more": False, "total_pages": 0}
        
        files = list(snapshots_dir.glob("*.jpg")) + list(snapshots_dir.glob("*.jpeg")) + list(snapshots_dir.glob("*.png"))
        files.sort(key=lambda f: f.stat().st_mtime, reverse=sort == "newest")
        
        total = len(files)
        
        total_pages = max(1, (total + limit - 1) // limit) if total > 0 else 1
        start_idx = (page - 1) * limit
        
        snapshots = []
        for filepath in files[start_idx:min(start_idx + limit, total)]:
            try:
                stat = filepath.stat()
                filename = filepath.name
                date_str = filename.replace("snapshot_", "").replace(".jpg", "").replace(".jpeg", "").replace(".png", "")
        
                try:
                    dt = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                except Exception:
                    dt = datetime.fromtimestamp(stat.st_mtime)
        
                snapshots.append({"id": filename, "filename": filename, "url": f"/api/snapshots/{filename}", "thumbnail_url": f"/api/snapshots/thumb/{filename}", "size_bytes": stat.st_size, "size_kb": round(stat.st_size / 1024, 1), "created": dt.isoformat(), "created_formatted": dt.strftime("%b %d, %Y %I:%M %p"), "date": date_str[:8] if len(date_str) >= 8 else "", "time": date_str[9:15] if len(date_str) >= 15 else ""})
            except Exception as e:
                logger.warning(f"Error processing snapshot {filepath}: {e}")
        
        return {"snapshots": snapshots, "total": total, "page": page, "limit": limit, "has_more": page < total_pages, "total_pages": total_pages, "sort": sort}

    @router.get("/api/snapshots/thumb/{filename}")
    async def get_snapshot_thumbnail(filename: str):
        snapshots_dir = Path("media/snapshots")
        thumb_dir = Path("media/thumbnails")
        
        thumb_dir.mkdir(parents=True, exist_ok=True)
        filepath = snapshots_dir / filename
        thumb_path = thumb_dir / f"thumb_{filename}"
        
        if thumb_path.exists():
            return FileResponse(thumb_path, media_type='image/jpeg')
        
        if filepath.exists():
            try:
                img = cv2.imread(str(filepath))
                if img is not None:
                    thumb = cv2.resize(img, (400, 225), interpolation=cv2.INTER_AREA)
                    cv2.imwrite(str(thumb_path), thumb)
                    logger.debug(f"Generated thumbnail: {thumb_path}")
                    return FileResponse(thumb_path, media_type='image/jpeg')
            except Exception as e:
                logger.warning(f"Thumbnail generation failed for {filename}: {e}")
        
        placeholder = Path("assets/img/placeholder-thumb.jpg")
        if placeholder.exists():
            return FileResponse(placeholder, media_type='image/jpeg')
        
        return Response(content=b'', media_type='image/jpeg')

    @router.get("/api/snapshots/{filename}")
    async def get_snapshot(filename: str):
        filepath = Path("media/snapshots") / filename
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="Snapshot not found")
        
        if filepath.suffix.lower() not in ['.jpg', '.jpeg', '.png']:
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        return FileResponse(filepath, media_type='image/jpeg', filename=filename, headers={'Cache-Control': 'public, max-age=31536000', 'Content-Disposition': f'inline; filename="{filename}"'})

    @router.delete("/api/snapshots/{filename}")
    async def delete_snapshot(filename: str):
        filepath = Path("media/snapshots") / filename
        thumb_path = Path("media/thumbnails") / f"thumb_{filename}"
        
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="Snapshot not found")
        
        try:
            filepath.unlink()
            if thumb_path.exists():
                thumb_path.unlink()
        
            logger.info(f"🗑️ Deleted snapshot: {filename}")
            return {"status": "success", "message": f"Deleted {filename}", "filename": filename}
        except Exception as e:
            logger.error(f"Delete error for {filename}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/api/snapshots/capture")
    async def capture_snapshot():
        try:
            frame = camera.get_frame()
            if frame is None:
                raise { "status": False, "message": "Failed to capture frame as no Camera Available or camera not running" }
        
            snapshots_dir = Path("media/snapshots")
            snapshots_dir.mkdir(parents=True, exist_ok=True)
            
            now = datetime.now()
            
            filename = f"snapshot_{now.strftime('%Y%m%d_%H%M%S')}.jpg"
            filepath = snapshots_dir / filename
            
            cv2.imwrite(str(filepath), cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            logger.info(f"📸 Snapshot captured: {filename}")
            
            await sio.emit('snapshot_new', {"filename": filename, "url": f"/api/snapshots/{filename}", "thumbnail_url": f"/api/snapshots/thumb/{filename}", "created": now.isoformat(), "created_formatted": now.strftime("%b %d, %Y %I:%M %p")})
            
            return {"status": True, "filename": filename, "url": f"/api/snapshots/{filename}", "message": "Snapshot captured successfully"}
        except Exception as e:
            logger.error(f"Capture error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/api/snapshots/stats")
    async def get_snapshot_stats():
        snapshots_dir = Path("media/snapshots")
        thumb_dir = Path("media/thumbnails")
        
        if not snapshots_dir.exists():
            return {"total": 0, "storage_used_mb": 0, "storage_thumbnails_mb": 0, "oldest": None, "newest": None}
        
        files = list(snapshots_dir.glob("*.jpg")) + list(snapshots_dir.glob("*.jpeg")) + list(snapshots_dir.glob("*.png"))
        total_size = sum(f.stat().st_size for f in files)
        thumb_size = sum(f.stat().st_size for f in thumb_dir.glob("*.jpg")) if thumb_dir.exists() else 0
        files_sorted = sorted(files, key=lambda f: f.stat().st_mtime) if files else []
        
        return {"total": len(files), "storage_used_mb": round(total_size / 1024 / 1024, 2), "storage_thumbnails_mb": round(thumb_size / 1024 / 1024, 2), "oldest": datetime.fromtimestamp(files_sorted[0].stat().st_mtime).isoformat() if files_sorted else None, "newest": datetime.fromtimestamp(files_sorted[-1].stat().st_mtime).isoformat() if files_sorted else None}

    return router
