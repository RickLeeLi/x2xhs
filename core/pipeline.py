"""编排层。"""
import time, shutil
from pathlib import Path
from config import MEDIA_DIR, SAMPLES_DIR
from core import scraper, translate, transform, cover, video, store, publisher


def _rel(abs_path):
    p = Path(abs_path)
    try: rel = p.relative_to(MEDIA_DIR); return "media/" + rel.as_posix()
    except Exception: return str(p).replace("\\", "/")


def _make_placeholder_images(out_dir, n=3):
    from PIL import Image, ImageDraw
    out_dir.mkdir(parents=True, exist_ok=True); paths = []
    for i in range(n):
        img = Image.new("RGB", (1080, 1080), (i * 40 % 255, 120, 200))
        d = ImageDraw.Draw(img); d.text((80, 500), f"\u793a\u4f8b\u56fe {i+1}", fill=(255, 255, 255))
        p = out_dir / f"orig_{i}.jpg"; img.save(p); paths.append(str(p))
    return paths


def process_link(url, demo=False, demo_type="image"):
    if demo:
        tweet = _build_demo(demo_type); tweet_id = tweet["id"]
    else:
        tweet_id = scraper.parse_tweet_id(url)
        if store.is_processed(tweet_id): raise ValueError("\u8be5\u63a8\u6587\u5df2\u53d1\u5e03\u8fc7")
        tweet = scraper.scrape_tweet(url)
    work = MEDIA_DIR / tweet_id; work.mkdir(parents=True, exist_ok=True)
    media = tweet.get("media", [])
    if demo:
        pass
    else:
        media = scraper.download_media(tweet, str(work))
    has_video = any(m.get("type") == "video" for m in media)
    has_image = any(m.get("type") == "image" for m in media)
    media_type = "video" if has_video else ("image" if has_image else "text")
    original = tweet.get("text", "").strip()
    translated = translate.translate(original) if original else ""
    content = transform.full_transform(original, translated, media_type)
    local_media, rel_media = [], []
    if media_type == "video":
        vid = next(m for m in media if m.get("type") == "video")
        caption = translated[:140] if translated else content["title"]
        vout = work / "video_vertical.mp4"
        video.process_video(vid["local"], caption, str(vout))
        local_media = [str(vout)]; rel_media = [_rel(str(vout))]
    else:
        cover_path = work / "cover.png"
        subtitle = (translated[:20] if translated else "") or (original[:20] if original else "")
        cover.generate_cover(content["title"], str(cover_path), subtitle=subtitle)
        local_media = [str(cover_path)]; rel_media = [_rel(str(cover_path))]
        imgs = [m for m in media if m.get("type") == "image" and m.get("local")]
        for m in imgs[:8]:
            local_media.append(m["local"]); rel_media.append(_rel(m["local"]))
    job = {
        "id": tweet_id, "url": tweet.get("url", url),
        "author_name": tweet.get("author_name", ""), "author_handle": tweet.get("author_handle", ""),
        "original_text": original, "translated_text": translated,
        "title": content["title"], "body": content["body"], "hashtags": content["hashtags"],
        "media_type": media_type, "media": rel_media, "local_media": local_media,
        "status": "preview", "created_at": time.time(), "updated_at": time.time(),
    }
    store.save_job(job); return job


def process_text(text, author_name="", author_handle="", tweet_url=""):
    text = (text or "").strip()
    if not text: raise ValueError("\u6587\u5b57\u4e3a\u7a7a")
    translated = translate.translate(text)
    content = transform.full_transform(text, translated, "text")
    job_id = f"text_{int(time.time())}"
    work = MEDIA_DIR / job_id; work.mkdir(parents=True, exist_ok=True)
    cover_path = work / "cover.png"
    subtitle = (translated[:20] if translated else text[:20])
    cover.generate_cover(content["title"], str(cover_path), subtitle=subtitle)
    job = {
        "id": job_id, "url": tweet_url, "author_name": author_name, "author_handle": author_handle,
        "original_text": text, "translated_text": translated,
        "title": content["title"], "body": content["body"], "hashtags": content["hashtags"],
        "media_type": "image", "media": [_rel(str(cover_path))], "local_media": [str(cover_path)],
        "status": "preview", "created_at": time.time(), "updated_at": time.time(),
    }
    store.save_job(job); return job


def create_blank_job(media_type="image"):
    """新建一个空白笔记（图文/视频），供用户从零开始编辑。"""
    media_type = "video" if media_type == "video" else "image"
    job_id = f"blank_{int(time.time() * 1000)}"
    work = MEDIA_DIR / job_id; work.mkdir(parents=True, exist_ok=True)
    job = {
        "id": job_id, "url": "", "author_name": "", "author_handle": "",
        "original_text": "", "translated_text": "",
        "title": "", "body": "", "hashtags": [],
        "media_type": media_type, "media": [], "local_media": [],
        "status": "preview", "created_at": time.time(), "updated_at": time.time(),
    }
    store.save_job(job); return job


def confirm_publish(job_id):
    job = store.get_job(job_id)
    if not job: raise ValueError("\u4efb\u52a1\u4e0d\u5b58\u5728")
    if job["status"] == "published": return {"ok": True, "already": True, "url": job.get("url")}
    res = publisher.publish_note(
        title=job["title"], body=job["body"], hashtags=job["hashtags"],
        media_paths=job["local_media"], media_type=job["media_type"])
    if res.get("ok"):
        store.update_job(job_id, status="published", publish_result=res)
    else:
        store.update_job(job_id, status="failed", publish_result=res)
    return res


def _build_demo(demo_type):
    work = MEDIA_DIR / f"demo_{demo_type}"; work.mkdir(parents=True, exist_ok=True)
    if demo_type == "video":
        ph = work / "placeholder.mp4"
        if not ph.exists():
            subprocess = __import__("subprocess")
            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i",
                "color=c=orange:s=1280x720:d=3", "-pix_fmt", "yuv420p", str(ph)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"id": f"demo_{demo_type}", "url": "https://x.com/i/web/status/demo",
            "author_name": "Demo", "author_handle": "demo",
            "text": "This AI tool just changed how I work forever. Mind blowing demo!",
            "media": [{"type": "video", "local": str(ph)}]}
    imgs = _make_placeholder_images(work, 3)
    return {"id": f"demo_{demo_type}", "url": "https://x.com/i/web/status/demo",
        "author_name": "Demo", "author_handle": "demo",
        "text": "I tried the new AI cat feeder and my cat now orders food by itself. The future is unhinged \U0001F602 #AI #cats",
        "media": [{"type": "image", "local": p} for p in imgs]}
