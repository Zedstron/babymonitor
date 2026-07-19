from dotenv import load_dotenv
load_dotenv()

import time
import asyncio
import socketio
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional, AsyncGenerator
from aiortc.contrib.media import MediaRecorder

from helpers.database import *
from helpers.models import *
from helpers.tokenizer import decode_token
from helpers.logger import logger
from fastapi.responses import RedirectResponse
from fastapi import FastAPI, Request, Depends
from aiortc import RTCPeerConnection

from utils import *

from controllers.media import MediaController
from controllers.audio import AudioController
from controllers.camera import CameraController
from controllers.gpio import GPIOController
from controllers.weather import get_current_weather
from controllers.resources import get_system_health
from controllers.wireguard import WireGuard
from controllers.whitenoise import WhiteNoisePlayer

from routers import audio as audio_routes
from routers import gallery as gallery_routes
from routers import integrations as integration_routes
from routers import media as media_routes
from routers import pages as page_routes
from routers import streaming as streaming_routes
from routers import system as system_routes

gpio = GPIOController()
camera = CameraController()

try:
    camera.enable()
    logger.info("Camera enabled successfully")
except Exception as e:
    logger.warning(f"Camera enable failed: {e}")

audio = AudioController()
media = MediaController()
whitenoise = WhiteNoisePlayer()

EXCLUDED_PATHS = {
    "/",
    "/api/auth",
    "/docs",
    "/openapi.json",
}

EXCLUDED_PREFIXES = (
    "/assets",
)

def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("nursery")
    if not token:
        return None

    payload = decode_token(token)
    if not payload:
        return None

    return db.query(User).filter(User.id == payload.get("id")).first()

def is_excluded(path: str) -> bool:
    if path in EXCLUDED_PATHS:
        return True

    return any(path.startswith(prefix) for prefix in EXCLUDED_PREFIXES)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("🚀 Initializing Services & Endpoints")

    #state.sensor_task = asyncio.create_task(update_sensor_data())
    
    Path("media/recordings").mkdir(exist_ok=True)
    Path("media/snapshots").mkdir(exist_ok=True)
    
    logger.info("✅ Background tasks started")
    yield

    logger.info("🛑 Shutting down...")

    # state.sensor_task.cancel()
    # try:
    #     await state.sensor_task
    # except asyncio.CancelledError:
    #     pass

    for pc in state.pcs.copy():
        await state.pcs[pc].close()

    state.pcs.clear()
    logger.info("✅ Shutdown complete")

app = FastAPI(
    title="Baby Monitor Pro", 
    version="2.0.5", 
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

sio = socketio.AsyncServer(
    async_mode='asgi', 
    cors_allowed_origins='*', 
    async_handlers=True,
    logger=False,
    engineio_logger=False
)

app_socket = socketio.ASGIApp(sio, app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def auth_middleware(request: Request, call_next, user: User = Depends(get_current_user)):
    path = request.url.path

    if is_excluded(path):
        return await call_next(request)

    if not user:
        return RedirectResponse("/", status_code=303)

    response = await call_next(request)
    return response

app.mount("/assets", StaticFiles(directory="assets"), name="assets")
templates = Jinja2Templates(directory="templates")

class AppState:
    def __init__(self):
        self.pcs: dict[str, RTCPeerConnection] = dict()
        self.recorder: MediaRecorder = None
        self.recorder_task = None

        self.connected_clients: Dict[str, dict] = {}

        self.sensor_data = {
            "temperature": 24.5,
            "humidity": 58,
            "noise": 32,
            "occupancy": 1,
            "confidence": "98%"
        }

        self.settings = get_settings({
            "baby_name": "Cookie",
            "cry_detection": False,
            "led_indicator": True,
            "buzzer_enabled": False,
            "video_quality": "high",
            "video_resolution": "1080",
            "video_fps": "30",
            "latitude": 33.69186440015098, 
            "longitude": 72.82942605084591
        })

        self.notifications: List[dict] = []
        self.max_notifications = 50

        self.is_recording = False
        self.recording_start_time: Optional[float] = None
        self.current_recording_path: Optional[str] = None

        self.audio_listen_enabled = True
        self.current_volume = audio.get_volume()
        
        self.start_time = time.time()

        try:
            logger.info("Please wait current bandwidth is being calculated")
            self.bandwidth = quick_speed_test()
        except Exception as e:
            logger.warning("Bandwidth calculation failed, skipping " + str(e))
            self.bandwidth = {
                "upload": { "speed": 0, "label": "No Connection" },
                "download": { "speed": 0, "label": "No Connection" }
            }

        self.user_profile = {
            "profile_pic": "/assets/img/zain.jpeg",
            **get_profile()
        }
    
    def save_settings(self):
        try:
            save_settings(self.settings)
        except Exception as e:
            logger.error(f"Settings save error: {e}")

state = AppState()

@sio.event
async def connect(sid, environ):
    logger.info(f"🟢 Client connected: {sid}")
    state.connected_clients[sid] = {
        "connected_at": datetime.now().isoformat(),
        "ip": environ.get('REMOTE_ADDR', 'unknown')
    }

    await sio.emit('initial_state', {
        "sensor_data": state.sensor_data,
        "settings": state.settings,
        "is_connected": True,
        "notifications": state.notifications[-10:],
        "is_recording": state.is_recording,
    }, room=sid)
    
    await sio.emit('client_count', { "count": len(state.connected_clients) })

@sio.event
async def disconnect(sid):
    logger.info(f"🔴 Client disconnected: {sid}")
    if sid in state.connected_clients:
        del state.connected_clients[sid]

    await sio.emit('client_count', { "count": len(state.connected_clients) })

@sio.event
async def ping(sid, data):
    await sio.emit("pong", data, to=sid)

def get_template_context() -> dict:
    recordings_data = camera.get_recordings()
    snapshots_data = camera.get_snapshots(limit=20)

    wireguard = WireGuard()

    return {
        "profile": state.user_profile,
        "sensors": state.sensor_data,
        "settings": state.settings,
        "latency": "N/A",
        "notifications": state.notifications[-10:],
        "lullabies": media.getlist(),
        "recordings": recordings_data["items"],
        "recording_count": recordings_data["count"],
        "available_dates": recordings_data["available_dates"],
        "total_pages_recordings": recordings_data.get("total_pages", 1),
        "current_page": recordings_data.get("current_page", 1),
        "snapshots": snapshots_data["items"],
        "snapshot_count": snapshots_data["count"],
        "total_pages_snapshots": snapshots_data.get("total_pages", 1),
        "storage_media": get_storage("audio"),
        "volume": state.current_volume,
        "baby_audio": state.audio_listen_enabled,
        "health": get_system_health(),
        "weather": get_current_weather(state.settings["longitude"], state.settings["latitude"]),
        "wireguard": wireguard.get_config(),
        "ir": get_ir_devices(),
        "hostname": get_hostname(),
        **state.bandwidth
    }

app.include_router(page_routes.create_router(templates, state, get_current_user, get_template_context))
app.include_router(audio_routes.create_router(audio, state, sio))
app.include_router(streaming_routes.create_router(camera, audio, state))
app.include_router(media_routes.create_router(media, state, sio))
app.include_router(gallery_routes.create_router(camera, sio))
app.include_router(system_routes.create_router(state, sio))
app.include_router(integration_routes.create_router(whitenoise))

async def add_notification(message: str):
    note = {
        "message": message,
        "time": datetime.now().strftime("%H:%M"),
        "id": f"{int(time.time())}"
    }
    state.notifications.append(note)

    if len(state.notifications) > state.max_notifications:
        state.notifications = state.notifications[-state.max_notifications:]
    
    await sio.emit('notification_new', note)

async def update_sensor_data():
    while True:
        try:
            sensors = gpio.read_sensors()

            if sensors["temperature"] is not None:
                state.sensor_data["temperature"] = sensors["temperature"]

            if sensors["humidity"] is not None:
                state.sensor_data["humidity"] = sensors["humidity"]
            
            if state.audio_listen_enabled:
                state.sensor_data["noise"] = audio.get_mic_level()
                state.sensor_data.update(audio.guess_occupancy())

            await sio.emit('sensor_update', state.sensor_data)
            
            await asyncio.sleep(30)
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Sensor update error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    import os
    import uvicorn
    import traceback

    CERT_DIR = "cert"
    CERT_FILE = os.path.join(CERT_DIR, "cert.pem")
    KEY_FILE = os.path.join(CERT_DIR, "key.pem")

    MEDIA_DIR = "media"
    AUDIO_DIR = os.path.join(MEDIA_DIR, "audio")

    try:
        os.makedirs(CERT_DIR, exist_ok=True)

        cert_exists = os.path.isfile(CERT_FILE)
        key_exists = os.path.isfile(KEY_FILE)

        if not cert_exists or not key_exists:
            logger.error(f"SSL certificate files missing. cert exists: {cert_exists}, key exists: {key_exists}")
            raise FileNotFoundError("Required SSL certificate files not found in cert/")

        os.makedirs(MEDIA_DIR, exist_ok=True)
        os.makedirs(AUDIO_DIR, exist_ok=True)

        uvicorn.run(
            app_socket,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            ssl_certfile=CERT_FILE,
            ssl_keyfile=KEY_FILE
        )

    except Exception:
        logger.error(traceback.format_exc())
