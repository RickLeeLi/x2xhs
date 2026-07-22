"""内容改写：标题/正文/标签。"""
import re
import random
from config import ADD_PERSONA, ADD_HASHTAGS

TITLE_HOOKS = [
    "\u6551\u547d\uff01\u8fd9\u6761\u63a8\u7279\u592a\u7edd\u4e86\U0001F602",
    "\u5232\u5230\u5c31\u662f\u8d5a\u5230\U0001F525{kw}",
    "\u4e07\u4e07\u60f3\u4e0d\u5230\u2026\u2026{kw}",
    "\u8fd9\u6761\u76f4\u63a5\u5c01\u795e\u4e86\U0001F44F{kw}",
    "\u6211\u613f\u79f0\u4e4b\u4e3a\u5e74\u5ea6\u6700\u4f73{kw}",
    "\u770b\u5b8c\u7834\u9632\u4e86\U0001F62D{kw}",
    "\u4fe1\u606f\u91cf\u7206\u70b8\U0001F4A1{kw}",
    "\u59d0\u59b9\u4eec\u5feb\u770b\uff01{kw}",
    "\u8fd9\u64cd\u4f5c\u6211\u670d\u4e86\U0001F60F{kw}",
    "\u5efa\u8bae\u5168\u6587\u80cc\u8bf5{kw}",
]
BODY_OPENERS = [
    "\u5237 X \u7684\u65f6\u5019\u770b\u5230\u8fd9\u6761\uff0c\u76f4\u63a5\u7ed9\u6211\u770b\u7b11\u4e86\U0001F923",
    "\u4eca\u5929\u5728\u63a8\u7279\u51b2\u6d6a\u6361\u5230\u5b9d\u4e86\uff0c\u5fc5\u987b\u5206\u4eab\u7ed9\u4f60\u4eec\U0001F447",
    "\u8fd9\u6761\u63a8\u6587\u542b\u91d1\u91cf\u592a\u9ad8\uff0c\u8fde\u591c\u642c\u8fc7\u6765\uff01",
    "\u8c01\u61c2\u554a\uff0c\u8fd9\u6761\u63a8\u6587\u7b80\u76f4\u662f\u6211\u7684\u4e92\u8054\u7f51\u5634\u66ff\U0001F60E",
    "\u5232\u5230\u4e00\u6761\u795e\u5e16\uff0c\u7b2c\u4e00\u65f6\u95f4\u60f3\u5230\u4f60\u4eec\u2014\u2014",
]
BODY_CLOSERS = [
    "\u4f60\u4eec\u89c9\u5f97\u5462\uff1f\u8bc4\u8bba\u533a\u804a\u804a\ufeff\U0001F4AC",
    "\u5173\u6ce8\u6211\uff0c\u6bcf\u5929\u7ed9\u4f60\u642c\u5916\u7f51\u9ad8\u8d28\u91cf\u74dc\U0001F349",
    "\u89c9\u5f97\u6709\u7528\u8bb0\u5f70\u70b9\u8d5e\u6536\u85cf\uff0c\u4e0b\u6b21\u627e\u5f97\u5230\uff01\u2b50",
    "\u540c\u7c7b\u5185\u5bb9\u6211\u4f1a\u6301\u7eed\u66f4\u65b0\uff0c\u70b9\u4e2a\u5173\u6ce8\u4e0d\u8ff7\u8def\ufeff",
    "\u8fd9\u6761\u4f60\u6253\u51e0\u5206\uff1f\u8bf4\u51fa\u4f60\u7684\u770b\u6cd5\U0001F447",
]
TOPIC_TAGS = {
    "AI": ["#AI", "#\u4eba\u5de5\u667a\u80fd", "#ChatGPT"],
    "chatgpt": ["#ChatGPT", "#AI\u5de5\u5177"],
    "\u79d1\u6280": ["#\u9ed1\u79d1\u6280", "#\u6570\u7801"],
    "\u7a0b\u5e8f": ["#\u7a0b\u5e8f\u5458", "#\u7f16\u7a0b", "#\u4ee3\u7801"],
    "code": ["#\u7a0b\u5e8f\u5458", "#\u7f16\u7a0b"],
    "\u732b": ["#\u732b\u54aa", "#\u840c\u5ba0"],
    "\u72d7": ["#\u72d7\u72d7", "#\u840c\u5ba0"],
    "\u5ba0\u7269": ["#\u840c\u5ba0"],
    "\u7f8e\u98df": ["#\u7f8e\u98df", "#\u5403\u8d27"],
    "\u65c5\u6e38": ["#\u65c5\u884c", "#\u65c5\u6e38\u653b\u7565"],
    "travel": ["#\u65c5\u884c", "#\u65c5\u6e38\u653b\u7565"],
    "\u5065\u8eab": ["#\u5065\u8eab", "#\u81ea\u5f8b"],
    "\u51cf\u80a5": ["#\u51cf\u80a5", "#\u81ea\u5f8b"],
    "\u7406\u8d22": ["#\u7406\u8d22", "#\u641e\u94b1"],
    "money": ["#\u641e\u94b1", "#\u7406\u8d22"],
    "\u80a1": ["#\u70b2\u80a1", "#\u7406\u8d22"],
    "\u80b2\u513f": ["#\u80b2\u513f", "#\u5b9d\u5988"],
    "\u8003\u7814": ["#\u8003\u7814", "#\u5b66\u4e60"],
    "\u804c\u573a": ["#\u804c\u573a", "#\u6253\u5de5\u4eba"],
    "\u60c5\u611f": ["#\u60c5\u611f", "#\u604b\u7231"],
    "\u7a7f\u642d": ["#\u7a7f\u642d", "#ootd"],
    "\u7f8e\u5986": ["#\u7f8e\u5986", "#\u62a4\u80a4"],
    "\u7535\u5f71": ["#\u7535\u5f71", "#\u89c2\u5f71"],
    "\u97f3\u4e50": ["#\u97f3\u4e50", "#\u6b4c\u5355"],
    "\u6e38\u620f": ["#\u6e38\u620f", "#\u7535\u7ade"],
    "\u641e\u7b11": ["#\u641e\u7b11", "#\u6bb5\u5b50"],
    "meme": ["#\u641e\u7b11", "#\u6897\u56fe"],
    "\u65b0\u95fb": ["#\u70ed\u70b9", "#\u65b0\u95fb"],
    "\u5065\u5eb7": ["#\u5065\u5eb7", "#\u517b\u751f"],
}
GENERIC_TAGS = ["#\u5e99\u8d27\u5206\u4eab", "#\u6bcf\u65e5\u5206\u4eab", "#\u5916\u7f51\u51b2\u6d6a", "#\u6da8\u77e5\u8bc6", "#\u5c0f\u4f17\u5206\u4eab"]


def _extract_keywords(text):
    lowered = text.lower()
    hits = []
    for kw in TOPIC_TAGS:
        if kw.lower() in lowered:
            hits.append(kw)
    return hits


def _first_meaningful_line(text, max_len=12):
    line = re.split(r"[。\.\!\?\uff01\uff1f\n]", text.strip())[0].strip()
    line = re.sub(r"[#@]\w+", "", line).strip()
    if len(line) > max_len:
        line = line[:max_len]
    return line


def build_title(text_zh, original_text=""):
    kw = _first_meaningful_line(text_zh or original_text)
    hook = random.choice(TITLE_HOOKS)
    title = hook.replace("{kw}", f"\uff5c{kw}" if kw else "")
    if len(title) > 20:
        title = title[:19] + "\u2026"
    return title


def build_body(text_zh, original_zh="", media_type="image"):
    parts = []
    if ADD_PERSONA:
        parts.append(random.choice(BODY_OPENERS))
        parts.append("")
    body_main = text_zh.strip() if text_zh.strip() else original_zh.strip()
    for chunk in re.split(r"(?<=[\u3002\uff01\uff1f])\s*", body_main):
        if chunk.strip():
            parts.append(chunk.strip())
    if ADD_PERSONA:
        parts.append("")
        parts.append(random.choice(BODY_CLOSERS))
    return "\n".join(parts).strip()


def build_hashtags(text_zh, original_text=""):
    if not ADD_HASHTAGS:
        return []
    tags = []
    for kw in _extract_keywords(text_zh + " " + original_text):
        for t in TOPIC_TAGS.get(kw, []):
            if t not in tags:
                tags.append(t)
    for m in re.findall(r"#(\w[\w\u4e00-\u9fff]+)", original_text + " " + text_zh):
        t = "#" + m
        if t not in tags:
            tags.append(t)
    for g in GENERIC_TAGS:
        if g not in tags:
            tags.append(g)
        if len(tags) >= 10:
            break
    return tags[:10]


def full_transform(original_text, translated_text, media_type="image"):
    return {
        "title": build_title(translated_text, original_text),
        "body": build_body(translated_text, original_text, media_type),
        "hashtags": build_hashtags(translated_text, original_text),
    }
