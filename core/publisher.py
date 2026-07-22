"""小红书自动发布（Playwright）。

发布流程的选择器与操作顺序借鉴成熟的 GitHub 项目
wszrw123/xiaohongshu-automation（v2.0），比自行猜测的单一选择器稳健：
- tab 切换用 JS 精确文本匹配（class 常变，按文本点最稳）
- file input 用 `.upload-input, input[type='file']`（输入框常隐藏，用 state='attached'）
- 标题 / 正文 / 发布按钮均用「多备选兜底链」
"""
import json, time, os
from pathlib import Path
from config import XHS_COOKIES_PATH, XHS_CHROME_PROFILE, XHS_PUBLISH_TIMEOUT, DATA_DIR

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
CREATOR_URL = "https://creator.xiaohongshu.com/publish/publish?source=official"

# 真正的登录态 cookie 名（片段匹配）。小红书给匿名访客也会种 a1/webId/acw_tc 等设备
# 指纹 cookie，只有登录后才会出现下面这些会话/令牌 cookie，用它来判定是否真的登录成功。
_LOGIN_COOKIE_HINTS = (
    "web_session",
    "galaxy_creator_session_id",
    "access-token-creator.xiaohongshu.com",
    "customer-sso-sign",
    "customerClientId",
)


def _has_login_cookie(cookies):
    """cookies 里是否包含真正的登录态 cookie（而非匿名设备 cookie）。"""
    for c in cookies or []:
        name = c.get("name", "")
        if any(h in name for h in _LOGIN_COOKIE_HINTS):
            return True
    return False


def _browser():
    from playwright.sync_api import sync_playwright
    p = sync_playwright().start()
    headless = os.getenv("XHS_HEADLESS", "true").lower() in ("1", "true", "yes")
    if XHS_CHROME_PROFILE:
        browser = p.chromium.launch(headless=headless, user_data_dir=XHS_CHROME_PROFILE,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
        ctx = browser.new_context(user_agent=UA)
    else:
        browser = p.chromium.launch(headless=headless,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
        ctx = browser.new_context(user_agent=UA)
        if XHS_COOKIES_PATH.exists():
            try: ctx.add_cookies(json.loads(XHS_COOKIES_PATH.read_text(encoding="utf-8")))
            except Exception as e: print(f"[WARN] cookies 加载失败：{e}")
    return p, browser, ctx


def _ensure_logged_in(page):
    page.goto(CREATOR_URL, wait_until="domcontentloaded", timeout=XHS_PUBLISH_TIMEOUT * 1000)
    time.sleep(3)
    # 精确检测是否处于登录页面
    is_login_page = (
        "login" in page.url
        or page.locator(".beer-login-btn").count() > 0
        or page.locator("input[placeholder*='手机号']").count() > 0
    )
    if is_login_page:
        raise RuntimeError("小红书未登录或登录已失效：请先点击网页顶部的「[KEY] 登录小红书」按钮进行扫码登录。")


def _click_tab_by_text(page, text):
    """用 JS 匹配可见元素的文本并点击（切换「上传图文/上传视频」tab）。
    多策略：先宽松文本匹配所有可点击元素，再精确匹配，最后 Playwright 兜底。"""
    # 策略 1：JS 宽松匹配——搜所有可见元素，文本包含目标词即可
    found = page.evaluate("""(txt) => {
        const allEls = document.querySelectorAll('span, div, a, li, button, [role="tab"], [class*="tab"], p');
        const isSidebar = (el) => {
            let parent = el;
            while (parent) {
                const cls = (parent.className || '').toString().toLowerCase();
                const id = (parent.id || '').toString().toLowerCase();
                if (cls.includes('side') || cls.includes('menu') || cls.includes('nav') ||
                    id.includes('side') || id.includes('menu') || id.includes('nav')) {
                    return true;
                }
                parent = parent.parentElement;
            }
            return false;
        };

        // 1. 精确匹配（非侧栏）
        for (const el of allEls) {
            if (el.textContent.trim() === txt && el.offsetParent !== null && !isSidebar(el)) {
                el.click();
                return 'exact_non_sidebar';
            }
        }
        // 2. 包含匹配（非侧栏）
        for (const el of allEls) {
            const t = el.textContent.trim();
            if ((t === txt || (t.includes(txt) && t.length < txt.length + 5)) && el.offsetParent !== null && !isSidebar(el)) {
                el.click();
                return 'contains_non_sidebar:' + t;
            }
        }
        // 3. 兜底匹配（侧栏）
        for (const el of allEls) {
            if (el.textContent.trim() === txt && el.offsetParent !== null) {
                el.click();
                return 'exact_sidebar';
            }
        }
        return null;
    }""", text)
    if found:
        print(f"[OK] 已通过 JS {found} 切换到「{text}」tab")
        return True

    # 策略 2：Playwright get_by_text 精确匹配
    try:
        loc = page.get_by_text(text, exact=True)
        if loc.count() > 0:
            # 找到多个时逐个试点击可见的
            for i in range(loc.count()):
                try:
                    el = loc.nth(i)
                    if el.is_visible(timeout=2000):
                        el.click()
                        print(f"[OK] 已通过 Playwright get_by_text 切换到「{text}」tab")
                        return True
                except Exception:
                    continue
    except Exception as e:
        print(f"[WARN] Playwright get_by_text 失败：{e}")

    # 策略 3：Playwright 非精确匹配（最后兜底）
    try:
        loc = page.get_by_text(text)
        if loc.count() > 0:
            for i in range(min(loc.count(), 10)):  # 最多试前 10 个
                try:
                    el = loc.nth(i)
                    if el.is_visible(timeout=1000):
                        el.click()
                        print(f"[OK] 已通过 Playwright 非精确匹配切换到「{text}」tab")
                        return True
                except Exception:
                    continue
    except Exception:
        pass

    print(f"[ERROR] 所有策略均未找到「{text}」tab")
    return False


def _start_upload(page, media_paths, media_type):
    """在创作后台启动上传。
    流程：先切到正确的 tab → 找对应类型的 file input → 设文件。
    关键安全守则：如果 tab 切换失败且当前 input 类型不匹配 → 直接报错，
    绝不用视频的单文件 input 塞多张图（会爆 Non-multiple）。
    """
    is_video = media_type == "video"
    target = "上传视频" if is_video else "上传图文"
    tab_ok = _click_tab_by_text(page, target)
    time.sleep(2)

    # 按类型精确定位 file input。
    # 关键：小红书图文/视频的 file input 常同时在 DOM 里（只是各自面板显隐），
    # 所以不能用 state='attached' 取第一个（会取到 DOM 顺序在前的隐藏 panel 的 input）。
    # 改用 locator.all() 找全部匹配项，再逐个检查是否在可见容器内。
    if is_video:
        selectors = ["input[type='file'][accept*='video']",
                     "input[type='file'][accept*='mp4']",
                     "input[type='file']"]
    else:
        selectors = ["input[type='file'][accept*='image']",
                     "input[type='file'][multiple]",
                     "input[type='file']"]

    inp = None
    matched_sel = None
    for sel in selectors:
        try:
            candidates = page.locator(sel).all()
            for c in candidates:
                # 检查这个 input 是否在可见容器内（其 offsetParent 非 null，
                # 或最近的非 body 祖先元素是可见的）
                is_usable = page.evaluate("""(el) => {
                    // file input 本身常 display:none，所以检查它所在的最近面板/容器
                    let parent = el.parentElement;
                    while (parent && parent.tagName !== 'BODY') {
                        const style = window.getComputedStyle(parent);
                        if (style.display === 'none' || style.visibility === 'hidden') {
                            return false;
                        }
                        parent = parent.parentElement;
                    }
                    return true;
                }""", c.element_handle())
                if is_usable:
                    inp = c
                    matched_sel = sel
                    break
            if inp is not None:
                break
        except Exception:
            continue

    if inp is None:
        print("[WARN] 未找到任何 file input")
        return False

    # 安全检查：图文模式绝不能用单文件 input 塞多张图
    if not is_video and len(media_paths) > 1:
        multiple_attr = inp.get_attribute("multiple")
        accept_val = (inp.get_attribute("accept") or "").lower()
        # 判断是否为图片类 input：有 multiple 属性，或 accept 含图片扩展名/关键词
        is_image_input = bool(multiple_attr) or any(
            kw in accept_val for kw in ("image", "jpg", "jpeg", "png", "webp", "gif", "bmp")
        )
        if not is_image_input:
            raise RuntimeError(
                f"Tab 切换{'失败' if not tab_ok else '可能未生效'}："
                f"当前 file input 是单文件(accept={accept_val})，无法塞入 "
                f"{len(media_paths)} 张图片。请检查页面是否真的在「上传图文」tab。"
                f"（已保存调试截图 publish_debug_fail.png）")

    file_paths = media_paths[0] if is_video else media_paths
    try:
        inp.set_input_files(file_paths)
        kind = "视频" if is_video else f"{len(media_paths)}张图片"
        print(f"[ATTACH] 已设置上传文件：{kind}（选择器: {matched_sel}）")
        return True
    except Exception as e:
        print(f"[WARN] 设文件失败：{e}")
        return False


def _fill_title(page, title):
    """填写标题。多个备选选择器，首个成功即用。借鉴成熟项目。"""
    for sel in ["div.d-input input", "div.title-container input",
                "input[placeholder*='标题']", "#title-input"]:
        try:
            el = page.locator(sel).first
            el.wait_for(state="visible", timeout=5000)
            el.click()
            el.fill(title[:20])
            return True
        except Exception:
            continue
    raise RuntimeError("找不到标题输入框")


def _fill_content(page, body):
    """填写正文。contenteditable 容器不能用 fill，需键盘输入。
    借鉴成熟项目：先尝试 div.ql-editor，再降级 [role=textbox] / contenteditable。"""
    for sel in ["div.ql-editor", "[role='textbox']", "div[contenteditable='true']"]:
        try:
            el = page.locator(sel).first
            el.wait_for(state="visible", timeout=5000)
            el.click()
            try:
                el.fill(body)
            except Exception:
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                for line in body.split("\n"):
                    page.keyboard.type(line, delay=15)
                    page.keyboard.press("Enter")
            return True
        except Exception:
            continue
    raise RuntimeError("找不到正文输入框")


def _click_publish(page):
    """点击发布按钮。用多策略兜底：
    1) 精确 CSS 选择器链（成熟项目验证过）
    2) JS 按可见文本精确匹配「发布」（最稳，class 常变但文案不变）
    3) Playwright get_by_text 兜底
    """
    clicked = False

    # 策略 1：CSS 选择器链（以及针对新版 div 按钮的优化选择器）
    css_selectors = [
        ".publish-video .btn-inner:has-text('发布')",
        ".publish-video .btn-wrapper:has-text('发布')",
        ".btn-inner:has-text('发布')",
        ".btn-wrapper:has-text('发布')",
        ".publish-page-publish-btn button.bg-red",
        ".submit-container button.primary",
        "button.publishBtn",
        "button[class*='publish']:not([disabled])",
        ".footer-bar button[class*='primary']",
        ".action-bar button:last-of-type",
    ]
    for sel in css_selectors:
        try:
            btn = page.locator(sel).first
            btn.wait_for(state="visible", timeout=3000)
            if not btn.get_attribute("disabled"):
                btn.scroll_into_view_if_needed()
                time.sleep(0.5)
                btn.click()
                clicked = True
                print(f"[OK] 已通过 CSS 选择器点击发布按钮：{sel}")
                break
        except Exception:
            continue

    # 策略 2：JS 精确文本匹配可见的「发布」按钮（跳过侧栏「发布笔记」等干扰项）
    if not clicked:
        try:
            found = page.evaluate("""() => {
                // 找所有可见的 button / [role=button] 或是带 publish/btn 类的 div 元素
                const candidates = document.querySelectorAll('button, [role="button"], div[class*="btn"], div[class*="publish"], .publish-video');
                for (const el of candidates) {
                    const text = (el.textContent || '').trim();
                    // 精确匹配「发布」，排除「发布笔记」「发布图文」等含「发布」的更长文本
                    if (text === '发布' && el.offsetParent !== null) {
                        // 再确认不是 disabled
                        if (!el.disabled && !el.getAttribute('disabled') &&
                            !el.classList.contains('disabled') &&
                            !el.getAttribute('aria-disabled')) {
                            el.scrollIntoView({ block: 'center' });
                            el.click();
                            return true;
                        }
                    }
                }
                return false;
            }""")
            if found:
                clicked = True
                print("[OK] 已通过 JS 文本匹配点击「发布」按钮")
        except Exception as e:
            print(f"[WARN] JS 文本匹配失败：{e}")

    # 策略 3：Playwright get_by_role/text 兜底
    if not clicked:
        try:
            btn = page.get_by_role("button", name="发布", exact=True)
            if btn.count() and btn.first.is_visible(timeout=3000):
                btn.first.scroll_into_view_if_needed()
                time.sleep(0.5)
                btn.first.click()
                clicked = True
                print("[OK] 已通过 get_by_role 点击「发布」按钮")
        except Exception:
            pass

    if not clicked:
        raise RuntimeError("找不到发布按钮（或发布按钮处于禁用状态）")

    time.sleep(3)
    # 二次确认弹窗（如果有）
    try:
        cf = page.get_by_role("button", name="确认发布", exact=False)
        if cf.count() and cf.first.is_visible(timeout=3000):
            cf.first.click()
            print("[OK] 已点击二次确认「确认发布」")
    except Exception:
        pass


def _debug_dump(page, tag=""):
    """发布失败时保存截图并打印页面按钮文本，便于定位选择器问题。"""
    try:
        path = DATA_DIR / f"publish_debug_{tag}.png"
        page.screenshot(path=str(path))
        print(f"[SNAP] 调试截图已保存：{path}")
        btns = [b.inner_text() for b in page.locator("button").all()
                if b.is_visible(timeout=500)]
        texts = [t.strip() for t in btns if t and t.strip()]
        print("当前页面按钮文本：", texts[:40])
    except Exception as e:
        print(f"[WARN] 调试信息收集失败：{e}")


def publish_note(title, body, hashtags, media_paths, media_type="image"):
    full_body = body + ("\n\n" + " ".join(hashtags) if hashtags else "")
    p, browser, ctx = _browser()
    page = ctx.new_page()
    try:
        _ensure_logged_in(page)
        if not media_paths:
            raise RuntimeError("没有可发布的媒体文件（图片/视频为空），无法发布")
        time.sleep(2)
        ok = _start_upload(page, media_paths, media_type)
        if not ok:
            _debug_dump(page, "upload")
            raise RuntimeError("无法在创作后台启动上传：未找到文件入口或类型选择按钮"
                               "（已保存调试截图 publish_debug_upload.png，请把截图发我）")
        time.sleep(6)
        _fill_title(page, title)
        _fill_content(page, full_body)
        _click_publish(page)
        time.sleep(5)
        return {"ok": True, "url": page.url}
    except Exception as e:
        try: _debug_dump(page, "fail")
        except Exception: pass
        return {"ok": False, "error": str(e)}
    finally:
        browser.close(); p.stop()


def interactive_login():
    from playwright.sync_api import sync_playwright
    p = sync_playwright().start()
    # 强制开启有头模式以供用户扫码登录
    browser = p.chromium.launch(headless=False,
        args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
    ctx = browser.new_context(user_agent=UA)
    page = ctx.new_page()
    page.goto(CREATOR_URL, wait_until="domcontentloaded", timeout=60000)

    print("等待用户在弹出的浏览器中扫码登录小红书...")
    logged_in = False
    start_time = time.time()
    # 关键：只有当浏览器上下文里出现真正的登录态 cookie（web_session 等）才算登录成功。
    # 不能只看 URL/页面元素——匿名访问创作平台时 URL 也含 creator.xiaohongshu.com，
    # 会导致扫码未完成就误判成功，最终只存下一堆无效的设备 cookie。
    while time.time() - start_time < 180:
        time.sleep(2)
        try:
            if _has_login_cookie(ctx.cookies()):
                logged_in = True
                break
        except Exception:
            pass

    if not logged_in:
        browser.close()
        p.stop()
        raise RuntimeError("登录超时或未完成扫码（180秒内未检测到登录态）。请重新点击「[KEY] 登录小红书」并完成扫码。")

    try:
        cookies = ctx.cookies()
        XHS_COOKIES_PATH.parent.mkdir(parents=True, exist_ok=True)
        XHS_COOKIES_PATH.write_text(json.dumps(cookies, ensure_ascii=False, indent=2), encoding="utf-8")
        res = {"ok": True, "msg": "登录成功，已保存 cookies"}
    except Exception as e:
        res = {"ok": False, "error": f"保存 cookies 失败: {str(e)}"}
    finally:
        browser.close()
        p.stop()
    return res
