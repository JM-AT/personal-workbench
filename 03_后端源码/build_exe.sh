#!/usr/bin/env bash
# 把 AI 工作台打包成 Windows 桌面可执行文件（onedir 模式，更稳定）。
# 依赖：pywebview + pyinstaller（已装到 ./lib），以及 frontend/dist 已构建。
# 注意：一律使用相对路径，避免含中文的绝对路径导致 PyInstaller 找不到模块。
set -e

cd "$(dirname "$0")"

PY="$HOME/.workbuddy/binaries/python/versions/3.13.12/python.exe"
export PYTHONPATH="lib"

# 前置检查
if [ ! -d "../frontend/dist" ]; then
  echo "[错误] 未找到 frontend/dist，请先在 frontend/ 执行 npm run build"
  exit 1
fi

echo "=== 开始 PyInstaller 打包 ==="
"$PY" -m PyInstaller -y --noconsole --name "ai-workbench" \
  --paths lib \
  --add-data "../frontend/dist;frontend/dist" \
  --collect-all lancedb \
  --collect-all pyarrow \
  --hidden-import multiprocessing \
  --hidden-import uvicorn.logging \
  --hidden-import uvicorn.loops.auto \
  --hidden-import uvicorn.protocols.auto \
  --hidden-import h11 \
  desktop_app.py

echo "=== 完成 ==="
echo "产物目录： $PWD/dist/ai-workbench/"
echo "可执行文件： $PWD/dist/ai-workbench/ai-workbench.exe"
