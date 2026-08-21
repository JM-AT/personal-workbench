"""配置管理：模型供应商、嵌入方式、飞书模式。配置持久化到 data/config.json。"""
import json
import os
import sys

if getattr(sys, "frozen", False):
    # PyInstaller 打包后，__file__ 落在只读临时区；数据目录改放可执行文件旁边（可写、稳定）
    _BASE = os.path.dirname(sys.executable)
else:
    _BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(_BASE, "data")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "models": [
        {"id": "gpt", "name": "OpenAI GPT", "type": "openai",
         "base_url": "https://api.openai.com/v1", "api_key": "", "model": "gpt-4o-mini", "enabled": True},
        {"id": "deepseek", "name": "DeepSeek", "type": "openai",
         "base_url": "https://api.deepseek.com/v1", "api_key": "", "model": "deepseek-chat", "enabled": True},
        {"id": "qwen", "name": "通义千问", "type": "openai",
         "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "api_key": "", "model": "qwen-plus", "enabled": True},
        {"id": "ollama", "name": "Ollama 本地", "type": "ollama",
         "base_url": "http://localhost:11434/v1", "api_key": "ollama", "model": "qwen2.5:7b", "enabled": True},
    ],
    # 嵌入默认 hash（无需下载模型，纯本地离线可用）；追求质量可改为 fastembed / openai。
    "embedding": {"provider": "hash", "model": "hash", "base_url": "", "api_key": "", "dim": 256},
    "default_model": "gpt",
    "feishu": {"mode": "mock", "app_id": "", "app_secret": "", "user_id": ""},
}


def ensure_config():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
    return load_config()


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return ensure_config()
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(cfg: dict):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    return cfg
