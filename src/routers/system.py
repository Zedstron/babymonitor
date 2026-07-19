import time
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from helpers.database import get_db, User
from helpers.models import SettingsUpdate
from controllers.resources import get_system_health
from helpers.utils import format_uptime, get_latency, get_wifi_signal


def create_router(sio):
    router = APIRouter(prefix="/api")

    @router.post("/settings")
    async def update_settings_api(request: Request, data: SettingsUpdate):
        update_data = data.model_dump(exclude_unset=True)
        request.app.state.appstate.settings.update(update_data)
        request.app.state.appstate.save_settings()
        
        await sio.emit('settings_updated', request.app.state.appstate.settings)
        
        return { "status": True, "settings": request.app.state.appstate.settings }

    @router.post("/notifications/clear")
    async def clear_notifications(request: Request):
        request.app.state.appstate.notifications = []
        await sio.emit('notifications_cleared', {})
        
        return { "status": True }

    @router.get("/connection")
    async def get_connection_stats(request: Request):
        latency = get_latency()
        return JSONResponse({
            "is_connected": latency is not None,
            **get_wifi_signal(),
            **latency,
            "uptime": format_uptime(time.time() - request.app.state.appstate.start_time)
        })

    @router.get("/health")
    async def get_health_data():
        return { "status": "success", "timestamp": datetime.now().isoformat(), "data": get_system_health() }

    @router.post("/profile")
    async def update_profile(request: Request, db: Session = Depends(get_db)):
        data = await request.json()
        user = db.query(User).first()
        
        if "email" in data and data["email"]:
            user.email = data["email"]
            db.commit()
        
        if "new_password" in data:
            context = CryptContext(schemes=["argon2"], deprecated="auto")
            hashed_new = context.hash(data["new_password"])
            hashed_old = context.hash(data["current_password"])
        
            if user.password == hashed_old:
                user.password = hashed_new
                db.commit()
            else:
                return { "status": False, "message": "Current Password is invalid" }
        
        return { "status": True, "message": "Successfully Updated" }

    return router
