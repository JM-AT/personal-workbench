"""桌面入口：pywebview 打开本地窗口，内嵌 FastAPI（前端 + /api）。

- 开发：先 `npm run build` 生成 frontend/dist，再 `python desktop_app.py`。
- 打包：由 build_exe.sh 用 PyInstaller 打成桌面可执行文件。
- 校验：设置环境变量 AIWB_HEADLESS=1 仅起服务（不弹窗），便于自动化测试。
"""
import os
import sys
import time
import threading

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import webview

import app as backend_app

FROZEN = getattr(sys, "frozen", False)
if FROZEN:
    _MEI = sys._MEIPASS
    DIST = os.path.join(_MEI, "frontend", "dist")
else:
    _HERE = os.path.dirname(os.path.abspath(__file__))
    DIST = os.path.abspath(os.path.join(_HERE, "..", "frontend", "dist"))


def run_server():
    uvicorn.run(backend_app.app, host="127.0.0.1", port=8000, log_level="warning")


def wait_ready(timeout=10):
    import urllib.request

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen("http://127.0.0.1:8000/api/health", timeout=1)
            return True
        except Exception:
            time.sleep(0.2)
    return False


def main():
    # 挂载前端静态资源（单页应用）
    if os.path.isdir(DIST):
        backend_app.app.mount("/", StaticFiles(directory=DIST, html=True), name="static")
    else:
        print(f"[警告] 未找到前端构建产物：{DIST}，请先 `npm run build`。")

    if os.environ.get("AIWB_HEADLESS") == "1":
        # 无界面模式：仅起服务，用于校验/调试
        print("AIWB headless server on http://127.0.0.1:8000")
        run_server()
        return

    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    wait_ready()

    webview.create_window(
        "AI 工作台",
        "http://127.0.0.1:8000",
        width=1180,
        height=780,
        min_size=(920, 620),
    )
    webview.start()


if __name__ == "__main__":
    main()
