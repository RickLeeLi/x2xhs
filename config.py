"""X2XHS 全局配置。"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
MEDIA_DIR = DATA_DIR / "media"
COOKIES_DIR = Path(os.getenv("COOKIES_DIR", BASE_DIR / "cookies"))
SAMPLES_DIR = BASE_DIR / "samples"
TEMPLATES_DIR = BASE_DIR / "templates"

for d in (DATA_DIR, MEDIA_DIR, COOKIES_DIR, SAMPLES_DIR):
    d.mkdir(parents=True, exist_ok=True)

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))
WEBUI_TITLE = os.getenv("WEBUI_TITLE", "X \u2192 \u5c0f\u7ea2\u4e66 \u81ea\u52a8\u53d1\u5e03\u53f0")
TARGET_LANG = os.getenv("TARGET_LANG", "zh-CN")

TRANSLATE_BACKEND = os.getenv("TRANSLATE_BACKEND", "google")
TRANSLATE_API_KEY = os.getenv("TRANSLATE_API_KEY", "")
TRANSLATE_API_BASE = os.getenv("TRANSLATE_API_BASE", "https://api.openai.com/v1")
TRANSLATE_API_MODEL = os.getenv("TRANSLATE_API_MODEL", "gpt-4o-mini")

XHS_COOKIES_PATH = Path(os.getenv("XHS_COOKIES_PATH", COOKIES_DIR / "xhs_cookies.json"))
XHS_CHROME_PROFILE = os.getenv("XHS_CHROME_PROFILE", "")
XHS_PUBLISH_TIMEOUT = int(os.getenv("XHS_PUBLISH_TIMEOUT", "180"))

X_AUTH_COOKIES_PATH = Path(os.getenv("X_AUTH_COOKIES_PATH", COOKIES_DIR / "x_auth_cookies.json"))
X_USE_BROWSER = os.getenv("X_USE_BROWSER", "true").lower() in ("1", "true", "yes")

ADD_PERSONA = os.getenv("ADD_PERSONA", "true").lower() in ("1", "true", "yes")
ADD_HASHTAGS = os.getenv("ADD_HASHTAGS", "true").lower() in ("1", "true", "yes")
SUBTITLE_MODE = os.getenv("SUBTITLE_MODE", "caption")
VIDEO_SIZE = os.getenv("VIDEO_SIZE", "720x1280")


def detect_cjk_font(bold=False):
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc" if bold else "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyhbd.ttc",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]


FONT_REGULAR = detect_cjk_font(False)
FONT_BOLD = detect_cjk_font(True)
