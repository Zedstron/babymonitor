import uuid
from threading import Thread
import asyncio

from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRecorder
from fastapi import APIRouter, Request, Response

from controllers.audio import MicrophoneTrack
from controllers.camera import CameraVideoTrack
from utils import ts_filename


def create_router(camera, audio, state):
    router = APIRouter()

    @router.get("/api/video/frame")
    async def frame():
        data = camera.get_jpeg_frame()
        return Response(content=data, media_type="image/jpeg")

    @router.post("/streaming/offer")
    async def offer(request: Request):
        params = await request.json()
        offer = RTCSessionDescription(**params)
        pc = RTCPeerConnection()
        await pc.setRemoteDescription(offer)
        pc_id = str(uuid.uuid4())
        state.pcs[pc_id] = pc
        pc.addTrack(CameraVideoTrack(camera))
        pc.addTrack(MicrophoneTrack(audio))
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        @pc.on("connectionstatechange")
        async def state_change():
            if pc.connectionState in ["failed", "closed"]:
                await pc.close()
                state.pcs.pop(pc_id, None)

        return {"id": pc_id, "sdp": pc.localDescription.sdp, "type": pc.localDescription.type}

    @router.post("/streaming/close")
    async def close_pc(request: Request):
        params = await request.json()
        pc_id = params.get("pc_id")
        pc = state.pcs.pop(pc_id, None)
        if pc:
            await pc.close()
        return { "status": "ok" }

    @router.post("/api/recording/start")
    async def start_record(request: Request):
        def start_recorder(recorder: MediaRecorder):
            asyncio.run(recorder.start())
        data = await request.json()
        pc = state.pcs.get(data["pc_id"])
        if not pc:
            return { "status": True, "message": "PeerConnection not found" }
        if state.recorder:
            return { "status": False, "message": "Recording already started" }
        state.recorder = MediaRecorder("media/recordings/" + ts_filename(ext='mp4'))
        state.recorder.addTrack(CameraVideoTrack(camera))
        state.recorder.addTrack(MicrophoneTrack(audio))
        state.recorder_task = Thread(target=start_recorder, args=(state.recorder,))
        state.recorder_task.start()
        state.is_recording = True
        return { "status": True, "message": "Recording has been started Successfully" }

    @router.post("/api/recording/stop")
    async def stop_record(request: Request):
        data = await request.json()
        if not state.recorder or not data["pc_id"]:
            return { "status": False, "message": "No active recording or PC Id provided" }
        await state.recorder.stop()
        state.recorder = None
        state.recorder_task = None
        return { "status": True, "message": "Recording has been saved" }

    return router
