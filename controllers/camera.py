import asyncio
import cv2
import numpy as np
from typing import Optional, Tuple
from aiortc import VideoStreamTrack
from av import VideoFrame
from pathlib import Path
import subprocess
from datetime import datetime

try:
    from picamera2 import Picamera2
    PI_AVAILABLE = True
except:
    PI_AVAILABLE = False


class CameraController:
    def __init__(self):
        self._camera = None
        self._enabled = False
        self._recording = False
        self._resolution = (1280, 720)
        self._framerate = 30
        self._quality = 90
        self.black_frame = False

        if PI_AVAILABLE:
            try:
                self._camera = Picamera2()
            except:
                self._camera = None
    
    def noise_frame(self, width=640, height=480):
        return np.random.randint(
            0, 256,
            (height, width, 3),
            dtype=np.uint8
        )
    
    def get_snapshots(self, limit: int = 20) -> dict:
        snapshots_dir = Path("assets/snapshots")
        items = []

        if not snapshots_dir.exists():
            return {"items": [], "count": 0, "total_pages": 1}

        files = list(snapshots_dir.glob("*.jpg")) + list(snapshots_dir.glob("*.png"))
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        for filepath in files[:limit]:
            try:
                stat = filepath.stat()
                filename = filepath.name
                date_str = filename.replace("snapshot_", "").replace(".jpg", "").replace(".png", "")

                try:
                    dt = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
                except:
                    dt = datetime.fromtimestamp(stat.st_mtime)

                items.append({
                    "filename": filename,
                    "url": f"/assets/snapshots/{filename}",
                    "thumbnail_url": f"/api/snapshots/thumb/{filename}",
                    "size_kb": round(stat.st_size / 1024, 1),
                    "created_formatted": dt.strftime("%b %d, %Y %I:%M %p"),
                })
            except:
                continue
            
        return {
            "items": items,
            "count": len(items),
            "total_pages": max(1, (len(files) + limit - 1) // limit)
        }

    def get_recordings(self, limit: int = 50) -> dict:
        recordings_dir = Path("recordings")
        items = []

        if not recordings_dir.exists():
            return {
                "items": [],
                "count": 0,
                "available_dates": {"years": [], "months": [], "days": []}
            }

        years, months, days = set(), set(), set()

        for filepath in sorted(recordings_dir.glob("*.avi"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
            try:
                stat = filepath.stat()
                filename = filepath.name

                date_part = filename.replace("baby_", "").replace(".avi", "").split("_")[0]

                if len(date_part) == 8:
                    years.add(date_part[:4])
                    months.add({"value": date_part[4:6], "label": datetime(2000, int(date_part[4:6]), 1).strftime("%B")})
                    days.add(date_part[6:8])

                duration = self.__get_video_duration(filepath)

                items.append({
                    "id": filename,
                    "filename": filename,
                    "url": f"/api/recordings/file/{filename}",
                    "thumbnail": f"/api/recordings/thumbnail/{filename}",
                    "size_mb": round(stat.st_size / 1024 / 1024, 2),
                    "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "created_formatted": datetime.fromtimestamp(stat.st_mtime).strftime("%b %d, %Y %I:%M %p"),
                    "date": date_part,
                    "year": date_part[:4] if len(date_part) >= 4 else "",
                    "month": date_part[4:6] if len(date_part) >= 6 else "",
                    "day": date_part[6:8] if len(date_part) >= 8 else "",
                    "duration": duration,
                    "duration_formatted": self.__format_duration(duration)
                })
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                continue
            
        return {
            "items": items,
            "count": len(items),
            "available_dates": {
                "years": sorted(years, reverse=True),
                "months": sorted(months, key=lambda m: m["value"], reverse=True),
                "days": sorted(days, reverse=True)
            }
        }


    def __get_video_duration(self, filepath: Path) -> float:
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'default=noprint_wrappers=1:nokey=1', str(filepath)],
                capture_output=True, text=True, check=True, timeout=5
            )
            return float(result.stdout.strip())
        except:
            return filepath.stat().st_size / 1024 / 1024 * 10


    def __format_duration(self, seconds: float) -> str:
        if not seconds or seconds < 0:
            return "00:00"

        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hrs}:{mins:02d}:{secs:02d}" if hrs > 0 else f"{mins}:{secs:02d}"

    def enable(self):
        if not self._camera or self._enabled:
            return
        config = self._camera.create_video_configuration(
            main={"size": self._resolution, "format": "RGB888"},
            controls={"FrameRate": self._framerate}
        )
        self._camera.configure(config)
        self._camera.start()
        self._enabled = True

    def disable(self):
        if not self._camera or not self._enabled:
            return
        try:
            self._camera.stop()
        except:
            pass
        self._enabled = False

    def is_enabled(self):
        return self._enabled

    def get_frame(self) -> Optional[np.ndarray]:
        if not self._enabled or not self._camera:
            frame = np.zeros((480, 640, 3), dtype=np.uint8) if self.black_frame else self.noise_frame()
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        try:
            frame = self._camera.capture_array()
            if frame is None:
                frame = np.zeros((480, 640, 3), dtype=np.uint8)

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        except:
            frame = np.zeros((480, 640, 3), dtype=np.uint8) if self.black_frame else self.noise_frame()
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def get_jpeg_frame(self) -> Optional[bytes]:
        frame = self.get_frame()

        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self._quality]
        ok, buf = cv2.imencode(".jpg", frame, encode_param)
        if not ok:
            return None

        return buf.tobytes()

    def get_resolution(self) -> Tuple[int, int]:
        return self._resolution

    def set_resolution(self, width: int, height: int):
        self._resolution = (width, height)
        if self._enabled:
            self.disable()
            self.enable()

    def set_framerate(self, fps: int):
        self._framerate = fps
        if self._enabled and self._camera:
            try:
                self._camera.set_controls({ "FrameRate": fps })
            except:
                pass

    def get_framerate(self):
        return self._framerate

    def set_frame_quality(self, quality: int):
        self._quality = max(10, min(100, quality))

    def get_frame_quality(self):
        return self._quality

    def start_recording(self, filepath: str):
        if not self._camera or not self._enabled:
            return False
        try:
            self._camera.start_recording(filepath, format="mjpeg")
            self._recording = True
            return True
        except:
            self._recording = False
            return False

    def stop_recording(self):
        if self._camera and self._recording:
            try:
                self._camera.stop_recording()
                self._recording = False
            except:
                pass

    def is_recording(self):
        return self._recording


class CameraVideoTrack(VideoStreamTrack):
    kind = "video"

    def __init__(self, controller: CameraController):
        super().__init__()
        self.controller = controller

    async def recv(self):
        pts, time_base = await self.next_timestamp()
        frame = self.controller.get_frame()
        if frame is not None:
            video = VideoFrame.from_ndarray(frame, format="rgb24")
            video.pts = pts
            video.time_base = time_base
            return video