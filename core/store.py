"""任务状态存储。"""
import json, re, time
from pathlib import Path
from config import DATA_DIR

JOBS_FILE = DATA_DIR / "jobs.json"

def _load():
    if JOBS_FILE.exists():
        try: return json.loads(JOBS_FILE.read_text(encoding="utf-8"))
        except Exception: return {}
    return {}

def _clean_surrogates(obj):
    """递归清除孤立代理对（surrogate），避免写入 UTF-8 时崩溃。"""
    if isinstance(obj, str):
        try:
            s = obj.encode("utf-16", "surrogatepass").decode("utf-16")
        except Exception:
            s = obj
        return re.sub(r"[\ud800-\udfff]", "", s)
    if isinstance(obj, list):
        return [_clean_surrogates(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _clean_surrogates(v) for k, v in obj.items()}
    return obj

def _save(db):
    db = _clean_surrogates(db)
    JOBS_FILE.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")

def is_processed(tweet_id):
    db = _load(); job = db.get(tweet_id)
    return bool(job and job.get("status") == "published")

def save_job(job):
    db = _load(); db[job["id"]] = job; _save(db)

def get_job(job_id):
    return _load().get(job_id)

def update_job(job_id, **fields):
    db = _load(); job = db.get(job_id)
    if not job: return None
    job.update(fields); job["updated_at"] = time.time(); _save(db); return job
