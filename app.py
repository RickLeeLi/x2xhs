"""WEBUI 后端（FastAPI）。"""
import os, shutil, uvicorn
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from config import HOST, PORT, MEDIA_DIR, WEBUI_TITLE
from core import pipeline, store

app = FastAPI(title=WEBUI_TITLE)
app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")

class ProcessReq(BaseModel):
    url: str = ""; demo: bool = False; demo_type: str = "image"

class UpdateReq(BaseModel):
    title: str = ""
    body: str = ""
    hashtags: list = []
    media: list = []

class NewJobReq(BaseModel):
    media_type: str = "image"

@app.get("/api/health")
def health(): return {"ok": True, "title": WEBUI_TITLE}

@app.post("/api/process")
def api_process(req: ProcessReq):
    try:
        if req.demo: job = pipeline.process_link("", demo=True, demo_type=req.demo_type)
        else:
            if not req.url.strip(): return {"ok": False, "error": "\u8bf7\u7c98\u8d34 X \u63a8\u6587\u94fe\u63a5"}
            job = pipeline.process_link(req.url.strip())
        return {"ok": True, "job": _public_job(job)}
    except Exception as e: return {"ok": False, "error": str(e)}

@app.get("/api/job/{job_id}")
def api_get_job(job_id):
    job = store.get_job(job_id)
    if not job: return {"ok": False, "error": "\u4efb\u52a1\u4e0d\u5b58\u5728"}
    return {"ok": True, "job": _public_job(job)}

@app.post("/api/job/new")
def api_new_job(req: NewJobReq):
    try:
        job = pipeline.create_blank_job(req.media_type)
        return {"ok": True, "job": _public_job(job)}
    except Exception as e: return {"ok": False, "error": str(e)}

@app.post("/api/publish/{job_id}")
def api_publish(job_id):
    try: res = pipeline.confirm_publish(job_id); return {"ok": True, "result": res}
    except Exception as e: return {"ok": False, "error": str(e)}

@app.post("/api/login")
def api_login():
    try:
        from core import publisher
        res = publisher.interactive_login()
        return {"ok": True, "result": res}
    except Exception as e: return {"ok": False, "error": str(e)}

@app.get("/api/login/status")
def api_login_status():
    import json as _json
    from config import XHS_COOKIES_PATH
    from core import publisher
    try:
        cookies = _json.loads(XHS_COOKIES_PATH.read_text(encoding="utf-8"))
        return {"logged_in": publisher._has_login_cookie(cookies)}
    except Exception:
        return {"logged_in": False}

@app.post("/api/job/{job_id}/update")
def api_update_job(job_id: str, req: UpdateReq):
    job = store.get_job(job_id)
    if not job: return {"ok": False, "error": "\u4efb\u52a1\u4e0d\u5b58\u5728"}
    media = [m for m in req.media if isinstance(m, str)]
    local_media = [_rel_to_local(m) for m in media]
    store.update_job(job_id, title=req.title, body=req.body,
                     hashtags=req.hashtags, media=media, local_media=local_media)
    return {"ok": True, "job": _public_job(store.get_job(job_id))}

@app.post("/api/job/{job_id}/upload")
async def api_upload_media(job_id: str, file: UploadFile = File(...)):
    job = store.get_job(job_id)
    if not job: return {"ok": False, "error": "\u4efb\u52a1\u4e0d\u5b58\u5728"}
    ctype = file.content_type or ""
    is_video = ctype.startswith("video/")
    is_image = ctype.startswith("image/")
    if not (is_image or is_video):
        return {"ok": False, "error": "\u4ec5\u652f\u6301\u56fe\u7247\u6216\u89c6\u9891\u6587\u4ef6"}
    folder = MEDIA_DIR / job_id
    folder.mkdir(parents=True, exist_ok=True)
    if is_video:
        ext = (file.filename or "").rsplit(".", 1)[-1].lower()
        ext = ext if ext in ("mp4", "webm", "mov", "m4v", "avi") else "mp4"
        # 视频只保留一份：先删除已有 user_*.mp4
        for old in folder.glob("user_*.mp4"):
            try: old.unlink()
            except Exception: pass
        fn = f"user_1.{ext}"
    else:
        ext = (file.filename or "").rsplit(".", 1)[-1].lower()
        ext = ext if ext in ("jpg", "jpeg", "png", "webp", "gif", "bmp") else "jpg"
        n = len(list(folder.glob("user_*"))) + 1
        fn = f"user_{n}.{ext}"
    path = folder / fn
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    rel = f"media/{job_id}/{fn}"
    return {"ok": True, "rel": rel, "local": str(path), "kind": "video" if is_video else "image"}

def _rel_to_local(rel):
    rel = rel.replace("\\", "/")
    p = rel[len("media/"):] if rel.startswith("media/") else rel
    return str(MEDIA_DIR / p)

def _public_job(job):
    return {k: job[k] for k in ["id","url","author_name","author_handle","original_text",
        "translated_text","title","body","hashtags","media_type","media","status"]}

@app.get("/", response_class=HTMLResponse)
def index(): return FileResponse(os.path.join(os.path.dirname(__file__), "templates", "index.html"))

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT)
