"""视频转制（ffmpeg 竖屏 9:16 + 字幕）。"""
import subprocess
import tempfile
from pathlib import Path
from config import VIDEO_SIZE, FONT_BOLD, FONT_REGULAR

W, H = (int(x) for x in VIDEO_SIZE.split("x"))
_ENCODER = None


def _detect_encoder():
    global _ENCODER
    if _ENCODER:
        return _ENCODER
    out = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout
    for name in ("libx264", "libopenh264", "mpeg4"):
        if name in out:
            _ENCODER = name; return _ENCODER
    _ENCODER = "mpeg4"; return _ENCODER


def _esc(text):
    text = text.replace("\\", ""); text = text.replace("'", "\u2019"); text = text.replace("%", "\uff05"); return text


def _wrap_lines(text, max_chars=14):
    text = _esc(text)[:160]
    lines, cur = [], ""
    for ch in text:
        cur += ch
        if len(cur) >= max_chars and ch in " \uff0c\u3002\uff01\uff1f!?\u3001\uff1b;":
            lines.append(cur); cur = ""
    if cur:
        lines.append(cur)
    lines = lines[:4]
    return "\\n".join(lines)


def process_video(src, caption, output):
    src, output = str(src), str(output)
    font = FONT_BOLD if Path(FONT_BOLD).exists() else (FONT_REGULAR if Path(FONT_REGULAR).exists() else "verdana")
    enc = _detect_encoder()
    cap = _wrap_lines(caption or "\u5b57\u5e55")
    y = H - 200
    graph = (
        f"[0:v]scale={W}:-2[top];"
        f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma=20[bg];"
        f"[bg][top]overlay=(W-w)/2:(H-h)/2[ovl];"
        f"[ovl]drawbox=y={H-220}:w=iw:h=220:color=black@0.55:t=fill[bx];"
        f"[bx]drawtext=fontfile='{font}':text='{cap}':"
        f"fontcolor=white:fontsize=32:x=(w-tw)/2:y={y}:line_spacing=8[out]"
    )
    fd, script = tempfile.mkstemp(suffix=".txt")
    with open(script, "w", encoding="utf-8") as f:
        f.write(graph)
    cmd = ["ffmpeg", "-y", "-i", src, "-filter_complex_script", script,
           "-map", "[out]", "-map", "0:a?", "-c:v", enc]
    if enc == "libx264":
        cmd += ["-preset", "veryfast", "-crf", "23"]
    else:
        cmd += ["-b:v", "2M"]
    cmd += ["-c:a", "aac", "-b:a", "128k", "-shortest", output]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    finally:
        Path(script).unlink(missing_ok=True)
    if not Path(output).exists() or Path(output).stat().st_size == 0:
        raise RuntimeError("\u89c6\u9891\u8f6c\u5236\u5931\u8d25")
    return output
