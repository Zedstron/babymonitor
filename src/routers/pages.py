from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from helpers.tokenizer import create_token
from controllers.wireguard import WireGuard
from fastapi.templating import Jinja2Templates
from helpers.utils import get_hostname, get_storage
from controllers.weather import get_current_weather
from controllers.resources import get_system_health

from helpers.database import check_new_install, get_db, User, get_current_user, get_ir_devices

def create_router(_):
    router = APIRouter()
    templates = Jinja2Templates(directory="templates")

    @router.get("/", response_class=HTMLResponse)
    async def login_page(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
        if user == None:
            return templates.TemplateResponse("login.html", {
                "request": request,
                "is_new_install": check_new_install(db)
            })
        
        return RedirectResponse(url="/dashboard", status_code=303)

    @router.get("/logout")
    async def logout(user: User = Depends(get_current_user)):
        response = RedirectResponse(url="/", status_code=303)
        response.delete_cookie("nursery")

        return response

    @router.get("/dashboard", response_class=HTMLResponse)
    async def get_dashboard(request: Request, user: User = Depends(get_current_user)):
        if user:
            return templates.TemplateResponse("index.html", {
                "request": request,
                "user": user,
                **get_template_context(request.app.state.appstate)
            })
        
        return RedirectResponse("/?error=expired")

    @router.post("/api/auth")
    async def handle_auth(request: Request, username: str = Form(...), password: str = Form(...), confirm_password: str = Form(None), db: Session = Depends(get_db)):
        pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
        if check_new_install(db):
            if password != confirm_password:
                return RedirectResponse(url="/?error=match", status_code=status.HTTP_303_SEE_OTHER)

            hashed = pwd_context.hash(password)
            db.add(User(username=username, password=hashed))
            db.commit()

            request.app.state.appstate.user_profile.update({ "user_name": username, "email": None })

            res = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
            res.set_cookie(key="nursery", value=create_token({ "id": user.id, "username": user.username }), httponly=True, max_age=60*60*24*7, secure=True, samesite="lax")

            return res

        user = db.query(User).filter(User.username == username).first()

        if user and pwd_context.verify(password, user.password):
            res = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
            res.set_cookie(key="nursery", value=create_token({ "id": user.id, "username": user.username }), httponly=True, max_age=60*60*24*7, secure=True, samesite="lax")
            return res

        return RedirectResponse(url="/?error=auth", status_code=status.HTTP_303_SEE_OTHER)

    return router

def get_template_context(state) -> dict:
    recordings_data = state.camera.get_recordings()
    snapshots_data = state.camera.get_snapshots(limit=20)

    wireguard = WireGuard()

    return {
        "profile": state.user_profile,
        "sensors": state.sensor_data,
        "settings": state.settings,
        "latency": "N/A",
        "notifications": state.notifications[-10:],
        "lullabies": state.media.getlist(),
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