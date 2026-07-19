from fastapi import APIRouter, Request
from controllers.audio import AudioController

def create_router(state, sio):
    audio = AudioController()
    router = APIRouter(prefix="/api/audio")

    @router.post("/play")
    async def play_audio(request: Request):
        data = await request.body()
        mime_len = data[0]
        mime_type = data[1 : 1 + mime_len].decode("utf-8")
        audio_bytes = data[1 + mime_len:]
        status = audio.play_audio_bytes(audio_bytes, mime_type)
        return { "status": status, "message": "Playing audio in speaker" if status else "Hardware initialization issue for playback" }

    @router.post("/volume")
    async def set_volume(request: Request):
        data = await request.json()
        if "volume" in data:
            audio.update_volume(data["volume"])
            return { "status": True, "message": "Volume updated" }
        return { "status": False, "message": "Invalid request" }

    @router.post("/listen")
    async def set_listen_status(request: Request):
        data = await request.json()
        if "status" in data:
            state.audio_listen_enabled = data["status"]
            if not data["status"]:
                state.sensor_data["noise"] = "NA"
                state.sensor_data["occupancy"] = "NA"
                state.sensor_data["confidence"] = "0%"
                await sio.emit('sensor_update', state.sensor_data)
                audio.close_mic()
            else:
                audio.open_mic()
            return { "status": True, "message": "Baby Microphone status updated" }
        return { "status": False, "message": "Invalid request" }

    return router
