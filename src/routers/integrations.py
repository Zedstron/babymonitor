from fastapi import APIRouter, Request

from controllers.infrared import IRController
from controllers.wireguard import WireGuard
from helpers.logger import logger
from utils import get_ir_device, get_ir_devices, remove_ir_device


def create_router(whitenoise):
    router = APIRouter(prefix="/api")

    @router.post("/ir/")
    async def add_new_ir(request: Request):
        data = await request.json()
        if "tag" not in data:
            return { "status": False, "message": "Tag is required for recording signals" }
        tag = data.get("tag")
        frequency = data.get("frequency", 38888)
        ir = IRController(freq=frequency)
        if ir.record(tag):
            return { "status": True, "message": "Signal has been recorded & saved" }
        return { "status": False, "message": "Error occured either hardware issue or TAG not unique" }

    @router.get("/ir/")
    async def get_all_ir(request: Request):
        return get_ir_devices()

    @router.get("/ir/{id}")
    async def get_ir(id: int):
        return get_ir_device(id) or {"status": False, "message": "Device not found or Invalid ID"}

    @router.delete("/ir/{id}")
    async def delete_ir(id: int):
        response = { "status": False, "message": "Device not found or invalid ID" }
        if remove_ir_device(id):
            response.update({ "status": True, "message": "Successfully Removed" })
        return response

    @router.post("/ir/{id}/send")
    async def send_ir_signal(id: int):
        try:
            ir = IRController()
            result = ir.send(id)
            if not result:
                return { "status": False, "message": "Failed to send IR signal" }
            return { "status": True, "message": "IR signal sent" }
        except Exception as e:
            logger.error(f"IR send error: {e}")
            return { "status": False, "message": "Error sending IR signal" }

    @router.get("/whitenoise/start")
    async def start_whitenosie():
        whitenoise.start()
        return { "status": True, "message": "Whitenoise is now Active" }

    @router.get("/whitenoise/stop")
    async def stop_whitenoise():
        whitenoise.stop()
        return { "status": True, "message": "Whitenoise is now Stopped" }

    @router.get("/wireguard/start")
    async def start_wg():
        wire = WireGuard()
        status = wire.start()
        message = "Wireguard Service is now Running" if status else "Error occured while starting the service"
        return { "status": status, "message": message }

    @router.get("/wireguard/stop")
    async def stop_wg():
        wire = WireGuard()
        status = wire.stop()
        message = "Wireguard Service is now Stoped" if status else "Error occured while stoping the service"
        return { "status": status, "message": message }

    @router.post("/wireguard")
    async def update_wireguard(request: Request):
        data = await request.json()
        if len(data) > 0:
            wire = WireGuard()
            status = wire.save_config(data)
            message = "Wireguard Settings updated Successfully" if status else "Error occured while udpating wireguard settings"
            return { "status": status, "message": message }
        return { "status": False, "message": "No config provided nothing updated" }

    return router
