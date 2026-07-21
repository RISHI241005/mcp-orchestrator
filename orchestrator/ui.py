from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from orchestrator.auth import get_all_keys, add_key, remove_key, require_role
import os

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def ui_network_guard(request: Request):
    """Restrict UI access to localhost unless ORCH_UI_ALLOW_EXTERNAL is set to 'true'."""
    allow_external = os.environ.get("ORCH_UI_ALLOW_EXTERNAL", "false").lower() == "true"
    if allow_external:
        return True
    client = request.client
    if not client:
        return True
    host = client.host
    if host in ("127.0.0.1", "::1", "localhost"):
        return True
    raise HTTPException(status_code=403, detail="UI access restricted to localhost")


@router.get("/admin/ui", response_class=HTMLResponse)
def admin_ui(request: Request, network_ok: bool = Depends(ui_network_guard), authorized: bool = Depends(require_role('admin'))):
    keys = get_all_keys()
    return templates.TemplateResponse("admin_keys.html", {"request": request, "keys": keys})


# JSON endpoints for AJAX (inline JS client)
@router.post('/admin/ui/keys')
def admin_ui_keys_add(payload: dict, network_ok: bool = Depends(ui_network_guard), authorized: bool = Depends(require_role('admin'))):
    key = payload.get('key')
    role = payload.get('role', 'user')
    if not key:
        import uuid
        key = uuid.uuid4().hex
    add_key(key, role)
    return JSONResponse({"key": key, "role": role})


@router.delete('/admin/ui/keys/{key}')
def admin_ui_keys_remove(key: str, network_ok: bool = Depends(ui_network_guard), authorized: bool = Depends(require_role('admin'))):
    remove_key(key)
    return JSONResponse({"removed": key})


@router.post("/admin/ui/add")
def admin_ui_add(request: Request, key: str = Form(None), role: str = Form("user"), authorized: bool = Depends(require_role('admin')), network_ok: bool = Depends(ui_network_guard)):
    if not key:
        # generate key if empty
        import uuid
        key = uuid.uuid4().hex
    add_key(key, role)
    return RedirectResponse(url="/admin/ui", status_code=303)


@router.post("/admin/ui/remove")
def admin_ui_remove(request: Request, key: str = Form(...), authorized: bool = Depends(require_role('admin')), network_ok: bool = Depends(ui_network_guard)):
    remove_key(key)
    return RedirectResponse(url="/admin/ui", status_code=303)
