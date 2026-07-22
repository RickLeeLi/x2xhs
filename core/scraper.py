"""X 推文抓取。"""
import json, re, time
from pathlib import Path
import requests
from config import MEDIA_DIR, X_USE_BROWSER, X_AUTH_COOKIES_PATH

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
_SYND = "https://cdn.syndication.twimg.com/tweet-result"


def parse_tweet_id(url):
    m = re.search(r"(?:twitter\.com|x\.com)/\w+/status/(\d+)", url)
    return m.group(1) if m else None


def _fetch_syndication(tweet_id):
    try:
        r = requests.get(_SYND, params={"id": tweet_id}, headers={"User-Agent": UA}, timeout=15)
        if not r.ok: return None
        d = r.json()
    except Exception:
        return None
    media = []
    for m in d.get("mediaDetails", []) or []:
        t = m.get("type")
        if t == "photo":
            url = (m.get("media_url") or "").split("?")[0] + "?name=large"
            media.append({"type": "image", "url": url})
        elif t in ("video", "animated_gif"):
            variants = m.get("video_info", {}).get("variants", [])
            mp4 = [v for v in variants if v.get("content_type") == "video/mp4"]
            mp4.sort(key=lambda v: v.get("bitrate", 0) or 0, reverse=True)
            if mp4:
                media.append({"type": "video", "url": mp4[0]["url"],
                              "thumb": (m.get("media_url") or "").split("?")[0]})
    if not media and not d.get("text"): return None
    return {
        "id": tweet_id, "url": f"https://x.com/i/web/status/{tweet_id}",
        "author_name": (d.get("author") or {}).get("name", ""),
        "author_handle": (d.get("author") or {}).get("username", ""),
        "text": d.get("text", ""), "created_at": d.get("created_at", ""), "media": media,
    }


def _load_auth_cookies():
    if X_AUTH_COOKIES_PATH.exists():
        try: return json.loads(X_AUTH_COOKIES_PATH.read_text(encoding="utf-8"))
        except Exception: return []
    return []


def _fetch_via_browser(url, tweet_id):
    from playwright.sync_api import sync_playwright
    auth = _load_auth_cookies()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(user_agent=UA, locale="zh-CN")
        if auth: ctx.add_cookies(auth)
        page = ctx.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_selector("article", timeout=12000)
        except Exception: pass
        text = ""
        for a in page.query_selector_all("article"):
            t = a.inner_text()
            if t and len(t) > len(text): text = t
        media = []
        for img in page.query_selector_all("article img"):
            src = img.get_attribute("src") or ""
            if "twimg" in src and "profile_images" not in src:
                media.append({"type": "image", "url": src.split("?")[0] + "?name=large"})
        if not any(m["type"] == "video" for m in media):
            try: page.evaluate("() => document.querySelector('article video')?.play()"); time.sleep(2)
            except Exception: pass
            for v in page.query_selector_all("article video"):
                src = v.get_attribute("src") or (v.evaluate("e => e.currentSrc") or "")
                if src and src.endswith(".mp4"):
                    media.append({"type": "video", "url": src}); break
        browser.close()
        if not text and not media: return None
        return {"id": tweet_id, "url": url, "author_name": "", "author_handle": "",
                "text": text, "created_at": "", "media": media}


def scrape_tweet(url):
    tweet_id = parse_tweet_id(url)
    if not tweet_id:
        raise ValueError("\u65e0\u6cd5\u4ece\u94fe\u63a5\u4e2d\u89e3\u6790\u63a8\u6587 ID")
    if X_USE_BROWSER:
        data = _fetch_syndication(tweet_id) or _fetch_via_browser(url, tweet_id)
    else:
        data = _fetch_syndication(tweet_id)
    if not data:
        raise RuntimeError("\u6293\u53d6\u5931\u8d25\uff1aX \u4e0d\u53ef\u8fbe\u6216\u88ab\u767b\u5f55\u5899\u62e6\u622a")
    return data


def download_media(data, out_dir):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    result = []
    for i, m in enumerate(data.get("media", [])):
        ext = "mp4" if m["type"] == "video" else "jpg"
        dest = out / f"{i}.{ext}"
        try:
            r = requests.get(m["url"], headers={"User-Agent": UA}, timeout=60, stream=True)
            r.raise_for_status(); dest.write_bytes(r.content)
            item = dict(m); item["local"] = str(dest); result.append(item)
        except Exception as e:
            result.append({**m, "local": None, "error": str(e)})
    return result
