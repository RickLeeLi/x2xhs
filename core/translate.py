"""翻译模块。

【已禁用翻译】当前只抓取中文内容，无需翻译，translate() 直接透传原文。
如需恢复翻译，取消下方 annotated 代码块，并把 translate() 改回调用翻译逻辑即可。
"""
import re

# ===== 翻译功能暂注释（用户仅抓中文内容，避免联网卡死）=====
# import threading
# from config import TRANSLATE_BACKEND, TRANSLATE_API_KEY, TRANSLATE_API_BASE, TRANSLATE_API_MODEL, TARGET_LANG
#
# _HAS_CJK = re.compile(r"[\u4e00-\u9fff]")
#
# if TRANSLATE_BACKEND == "api" and TRANSLATE_API_KEY:
#     try:
#         from openai import OpenAI
#         _client = OpenAI(api_key=TRANSLATE_API_KEY, base_url=TRANSLATE_API_BASE)
#     except Exception:
#         _client = None
# else:
#     _client = None
#
#
# def _run_with_timeout(fn, timeout, default):
#     """在后台线程里跑 fn，超时则返回 default，避免网络调用卡死主流程。"""
#     box = {}
#     def _t():
#         try:
#             box["v"] = fn()
#         except Exception:
#             box["v"] = default
#     th = threading.Thread(target=_t, daemon=True)
#     th.start()
#     th.join(timeout)
#     return box.get("v", default)
#
#
# def _has_cjk(text):
#     return bool(_HAS_CJK.search(text or ""))
#
#
# def _api_translate(text):
#     def _do():
#         resp = _client.chat.completions.create(
#             model=TRANSLATE_API_MODEL,
#             messages=[
#                 {"role": "system", "content": "\u4f60\u662f\u7ffb\u8bd1\u4e13\u5bb6\u3002\u628a\u7528\u6237\u53d1\u6765\u7684\u793e\u4ea4\u5a92\u4f53\u5185\u5bb9\u51c6\u786e\u3001\u53e3\u8bed\u5316\u5730\u7ffb\u8bd1\u6210\u4e2d\u6587\uff08\u7b80\u4f53\uff09\uff0c\u4fdd\u7559\u539f\u610f\u3001\u8bed\u6c14\u548c emoji\uff0c\u4e0d\u8981\u52a0\u89e3\u91ca\uff0c\u53ea\u8fd4\u56de\u8bd8\u6587\u3002"},
#                 {"role": "user", "content": text},
#             ],
#             temperature=0.3,
#         )
#         return resp.choices[0].message.content.strip()
#     return _run_with_timeout(_do, 30, text)
#
#
# def _google_translate(text):
#     from deep_translator import GoogleTranslator
#     def _do():
#         if len(text) <= 4000:
#             return GoogleTranslator(source="auto", target=TARGET_LANG).translate(text)
#         parts, buf = [], ""
#         for ch in text:
#             buf += ch
#             if len(buf) >= 3500 and ch in "\u3002\n\uff01\uff1f!?":
#                 parts.append(buf)
#                 buf = ""
#         if buf:
#             parts.append(buf)
#         return "\n".join(GoogleTranslator(source="auto", target=TARGET_LANG).translate(p) for p in parts)
#     return _run_with_timeout(_do, 20, text)


def translate(text):
    """翻译已禁用：直接透传原文（中文内容无需翻译）。"""
    # 如需恢复翻译，把下面这行替换为原有逻辑：
    #   if not text or not text.strip(): return text or ""
    #   if _has_cjk(text) and len(re.sub(r"[^\x00-\xff]", "", text)) / max(len(text), 1) < 0.15: return text.strip()
    #   try:
    #       if _client is not None: return _api_translate(text).strip()
    #       return _google_translate(text).strip()
    #   except Exception: return text.strip()
    return text or ""
