import asyncio
from fastapi import APIRouter, File, Form, HTTPException, Request
from fastapi.responses import FileResponse
from controllers.media import MediaController

media = MediaController()

def create_router(sio):
    router = APIRouter(prefix="/api/media")

    @router.get("/{index}/play")
    async def play_media(request: Request, index: int):
        loop = asyncio.get_event_loop()

        def event(payload):
            if len(request.app.state.appstate.connected_clients) > 0:
                loop.create_task(sio.emit("media_track_position", payload ))

        lullabies = media.getlist()
        if 0 <= index < len(lullabies):
            update = media.play(index, event)
            await sio.emit("media_track_playing", { "song": lullabies[index], "artist": f"song_{index}", "isPlaying": True, **update })

            return { "status": True, "message": f"Playing {lullabies[index]}" }

        raise HTTPException(status_code=404, detail="Media not found")

    @router.get("/{index}/download")
    async def download_media(index: int):
        path = media.read(index)

        if path is None:
            raise HTTPException(status_code=404, detail="Media not found")

        return FileResponse(path, media_type="audio/mpeg", filename=path.name)

    @router.get("/{index}/pause")
    async def pause_media(index: int):
        lullabies = media.getlist()

        if 0 <= index < len(lullabies):
            media.pause(index)
            await sio.emit("media_update", { "song": lullabies[index], "artist": f"song_{index}", "isPlaying": False })

            return { "status": True, "message": f"Paused {lullabies[index]}" }

        raise HTTPException(status_code=404, detail="Media not found")

    @router.get("/{index}/stop")
    async def stop_media(index: int):
        lullabies = media.getlist()

        if 0 <= index < len(lullabies):
            media.stop(index)
            await sio.emit("media_update", { "song": None, "artist": None, "isPlaying": False })
            
            return { "status": True, "message": f"Stopped {lullabies[index]}" }

        raise HTTPException(status_code=404, detail="Media not found")

    @router.post("/upload")
    async def upload_media(file: bytes = File(...), filename: str = Form(...)):
        if not filename.lower().endswith(('.mp3', '.wav', '.ogg')):
            raise HTTPException(status_code=400, detail="Unsupported file type")

        media.upload(file, filename)

        return { "status": True, "message": f"Uploaded {filename}" }

    @router.delete("/{index}")
    async def delete_media(index: int):
        lullabies = media.getlist()

        if 0 <= index < len(lullabies):
            media.delete(index)
            return { "status": True, "message": f"Deleted {lullabies[index]}" }

        raise HTTPException(status_code=404, detail="Media not found")

    @router.get("/volume/{value}")
    async def set_track_volume(value: int):
        if 0 <= value <= 100:
            media.volume(value)
            await sio.emit("media_track_volume", { "value": value })

            return { "status": True, "message": f"Current Track volume is now {value}" }

        raise HTTPException(status_code=404, detail="Invalid Volume value")

    @router.get("/seek/{value}")
    async def set_track_position(value: int):
        if 0 <= value <= 100:
            media.seek(value)

            return { "status": True, "message": f"Current Track Position is now {value}" }

        raise HTTPException(status_code=404, detail="Invalid Seek Position")

    @router.get("")
    async def get_media():
        return { "lullabies": media.getlist() }

    @router.get("/status")
    async def get_media_status():
        return media.get_current()

    @router.get("/mute/on")
    async def set_mute_on():
        media.mute(True)
        return { "status": True, "message": "Successfully Updated" }

    @router.get("/mute/off")
    async def set_mute_off():
        media.mute(False)
        return { "status": True, "message": "Successfully Updated" }

    @router.get("/loop/on")
    async def set_loop_on():
        media.loop(True)
        return { "status": True, "message": "Successfully Updated" }

    @router.get("/loop/off")
    async def set_loop_off():
        media.loop(False)
        return { "status": True, "message": "Successfully Updated" }

    return router
