from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from orchestrator.auth import get_all_keys, add_key, remove_key, require_role

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/admin/ui", response_class=HTMLResponse)
def admin_ui(request: Request, authorized: bool = Depends(require_role('admin'))):
    keys = get_all_keys()
    return templates.TemplateResponse("admin_keys.html", {"request": request, "keys": keys})


@router.post("/admin/ui/add")
def admin_ui_add(request: Request, key: str = Form(None), role: str = Form("user"), authorized: bool = Depends(require_role('admin'))):
    if not key:
        # generate key if empty
        import uuid
        key = uuid.uuid4().hex
    add_key(key, role)
    return RedirectResponse(url="/admin/ui", status_code=303)


@router.post("/admin/ui/remove")
def admin_ui_remove(request: Request, key: str = Form(...), authorized: bool = Depends(require_role('admin'))):
    remove_key(key)
    return RedirectResponse(url="/admin/ui", status_code=303)
