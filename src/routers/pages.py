from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from helpers.database import check_new_install, get_db
from helpers.models import User
from helpers.tokenizer import create_token


def create_router(templates, state, get_current_user, get_template_context):
    router = APIRouter()

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
    async def get_dashboard(request: Request):
        return templates.TemplateResponse("index.html", {
            "request": request,
            **get_template_context()
        })

    @router.post("/api/auth")
    async def handle_auth(request: Request, username: str = Form(...), password: str = Form(...), confirm_password: str = Form(None), db: Session = Depends(get_db)):
        pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
        if check_new_install(db):
            if password != confirm_password:
                return RedirectResponse(url="/?error=match", status_code=status.HTTP_303_SEE_OTHER)
            hashed = pwd_context.hash(password)
            db.add(User(username=username, password=hashed))
            db.commit()
            state.user_profile.update({ "user_name": username, "email": None })
            return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
        user = db.query(User).filter(User.username == username).first()
        if user and pwd_context.verify(password, user.password):
            res = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
            res.set_cookie(key="nursery", value=create_token({ "id": user.id, "username": user.username }), httponly=True, max_age=60*60*24*7, secure=True, samesite="lax")
            return res
        return RedirectResponse(url="/?error=auth", status_code=status.HTTP_303_SEE_OTHER)

    return router
