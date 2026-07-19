import uuid
from threading import Thread
import asyncio

from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRecorder
from fastapi import APIRouter, Request, Response

from controllers.audio import MicrophoneTrack
from controllers.camera import CameraVideoTrack
from helpers.utils import ts_filename
from helpers.logger import logger

def create_router(_):
    router = APIRouter()

    @router.get("/api/video/frame")
    async def frame(request: Request):
        data = request.app.state.appstate.camera.get_jpeg_frame()
        return Response(content=data, media_type="image/jpeg")

    @router.post("/streaming/offer")
    async def offer(request: Request):
        params = await request.json()
        offer = RTCSessionDescription(**params)
        pc = RTCPeerConnection()

        await pc.setRemoteDescription(offer)

        pc_id = str(uuid.uuid4())
        request.app.state.appstate.pcs[pc_id] = pc

        pc.addTrack(request.app.state.appstate.relay.subscribe(request.app.state.appstate.cam_track))
        pc.addTrack(request.app.state.appstate.relay.subscribe(request.app.state.appstate.aud_track))

        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        @pc.on("connectionstatechange")
        async def state_change():
            if pc.connectionState in ["failed", "closed"]:
                await pc.close()
                request.app.state.appstate.pcs.pop(pc_id, None)

        return { "id": pc_id, "sdp": pc.localDescription.sdp, "type": pc.localDescription.type }

    @router.post("/streaming/close")
    async def close_pc(request: Request):
        params = await request.json()

        pc_id = params.get("pc_id")
        pc = request.app.state.appstate.pcs.pop(pc_id, None)

        if pc:
            await pc.close()

        return { "status": "ok" }

    @router.post("/api/recording/start")
    async def start_record(request: Request):
        data = await request.json()

        pc = request.app.state.appstate.pcs.get(data["pc_id"])
        if not pc:
            return { "status": True, "message": "PeerConnection not found" }

        if request.app.state.appstate.recorder:
            return { "status": False, "message": "Recording already started" }

        request.app.state.appstate.recorder = MediaRecorder("media/recordings/" + ts_filename(ext='mp4'))
        request.app.state.appstate.recorder.addTrack(request.app.state.appstate.vtrack)
        request.app.state.appstate.recorder.addTrack(request.app.state.appstate.atrack)

        await request.app.state.appstate.recorder.start()
        request.app.state.appstate.is_recording = True

        return { "status": True, "message": "Recording has been started Successfully" }

    @router.post("/api/recording/stop")
    async def stop_record(request: Request):
        data = await request.json()

        if not request.app.state.appstate.recorder or not data["pc_id"]:
            return { "status": False, "message": "No active recording or PC Id provided" }

        await request.app.state.appstate.recorder.stop()

        request.app.state.appstate.recorder = None
        return { "status": True, "message": "Recording has been saved" }

    return router
