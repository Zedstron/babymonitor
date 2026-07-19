from dotenv import load_dotenv
load_dotenv()

import asyncio
import socketio
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from typing import AsyncGenerator

from helpers.logger import logger
from fastapi import FastAPI

from helpers.appstate import AppState

from routers import audio as audio_routes
from routers import gallery as gallery_routes
from routers import integrations as integration_routes
from routers import media as media_routes
from routers import pages as page_routes
from routers import streaming as streaming_routes
from routers import system as system_routes
from routers import socketio as socket_routes

routers = ( 
    socket_routes, audio_routes, gallery_routes,
    integration_routes, media_routes, page_routes,
    streaming_routes, system_routes 
)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("🚀 Initializing Services & Endpoints")

    #state.sensor_task = asyncio.create_task(update_sensor_data())
    
    Path("media/recordings").mkdir(exist_ok=True)
    Path("media/snapshots").mkdir(exist_ok=True)

    app.state.appstate = AppState()
    sio.appstate = app.state.appstate
    
    logger.info("✅ Background tasks started")
    yield

    logger.info("🛑 Shutting down...")

    # state.sensor_task.cancel()
    # try:
    #     await state.sensor_task
    # except asyncio.CancelledError:
    #     pass

    for pc in app.state.appstate.pcs.copy():
        await app.state.appstate.pcs[pc].close()

    app.state.appstate.pcs.clear()
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

app.mount("/assets", StaticFiles(directory="assets"), name="assets")

for router in routers:
    r = router.create_router(sio)
    if r:
        app.include_router(r)

async def update_sensor_data(state):
    while True:
        try:
            sensors = state.gpio.read_sensors()

            if sensors["temperature"] is not None:
                state.sensor_data["temperature"] = sensors["temperature"]

            if sensors["humidity"] is not None:
                state.sensor_data["humidity"] = sensors["humidity"]
            
            if state.audio_listen_enabled:
                state.sensor_data["noise"] = state.audio.get_mic_level()
                state.sensor_data.update(state.audio.guess_occupancy())

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
