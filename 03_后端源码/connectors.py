"""外部数据接入：把其他软件的数据灌进本地知识库（LanceDB）。

支持三种来源：
1. local_folder  —— 扫描本机某个目录下的 .txt/.md/.pdf，批量入库（无需联网）
2. rest_api      —— 调用用户提供的 REST 接口，把返回 JSON 扁平化为文本入库
3. feishu        —— 复用 schedule 的飞书模式，拉取文档/多维表格（当前 mock）

每条接入配置存 config.json 的 connectors 列表：
{"id","name","type":"local_folder|rest_api|feishu","config":{...},"last_sync":0}
"""
import json
import os
import time
import urllib.parse

import requests

from config import load_config, save_config
from embeddings import Embedder
from kb import ingest_text


def list_connectors() -> list:
    cfg = load_config()
    return cfg.get("connectors", [])


def add_connector(c: dict) -> dict:
    cfg = load_config()
    conns = cfg.get("connectors", [])
    c = dict(c)
    c["id"] = c.get("id") or f"conn_{int(time.time())}"
    c["last_sync"] = c.get("last_sync", 0)
    conns.append(c)
    cfg["connectors"] = conns
    save_config(cfg)
    return c


def delete_connector(cid: str) -> bool:
    cfg = load_config()
    conns = cfg.get("connectors", [])
    new = [x for x in conns if x.get("id") != cid]
    if len(new) == len(conns):
        return False
    cfg["connectors"] = new
    save_config(cfg)
    return True


def _flatten_json(obj, prefix="") -> str:
    """把嵌套 JSON 拍平成可读文本（用于 REST 接入）。"""
    lines = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{prefix}{k}:")
                lines.append(_flatten_json(v, prefix + "  "))
            else:
                lines.append(f"{prefix}{k}: {v}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            lines.append(f"{prefix}- [{i}]")
            lines.append(_flatten_json(v, prefix + "  "))
    else:
        lines.append(f"{prefix}{obj}")
    return "\n".join(lines)


def sync_local_folder(path: str, emb: Embedder, label: str = None) -> int:
    """扫描目录内文本/PDF，入库。返回入库文档数。"""
    if not os.path.isdir(path):
        raise ValueError(f"目录不存在: {path}")
    count = 0
    exts = (".txt", ".md", ".markdown", ".pdf")
    for root, _, files in os.walk(path):
        for fn in files:
            if fn.lower().endswith(exts):
                fp = os.path.join(root, fn)
                try:
                    if fn.lower().endswith(".pdf"):
                        from pypdf import PdfReader
                        import io
                        with open(fp, "rb") as f:
                            text = "\n".join(
                                (p.extract_text() or "") for p in PdfReader(io.BytesIO(f.read())).pages)
                    else:
                        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                            text = f.read()
                except Exception:
                    continue
                name = label or f"folder:{os.path.relpath(fp, path)}"
                ingest_text(f"{name}::{fn}", text, emb)
                count += 1
    return count


def sync_rest_api(url: str, emb: Embedder, headers: dict = None,
                  label: str = None, method: str = "GET") -> int:
    resp = requests.request(method, url, headers=headers or {}, timeout=20)
    resp.raise_for_status()
    text = _flatten_json(resp.json())
    name = label or f"rest:{urllib.parse.urlparse(url).netloc}"
    ingest_text(f"{name}::{int(time.time())}", text, emb)
    return 1


def sync_connector(cid: str, emb: Embedder) -> dict:
    """执行单个连接器同步。"""
    conn = next((c for c in list_connectors() if c["id"] == cid), None)
    if not conn:
        return {"error": f"找不到连接器 {cid}"}
    t = conn["type"]
    cfg = conn.get("config", {})
    if t == "local_folder":
        n = sync_local_folder(cfg["path"], emb, label=cfg.get("label"))
    elif t == "rest_api":
        n = sync_rest_api(cfg["url"], emb,
                          headers=cfg.get("headers"),
                          label=cfg.get("label"),
                          method=cfg.get("method", "GET"))
    elif t == "feishu":
        # 复用飞书 mock 逻辑（后续可接真实飞书文档接口）
        from schedule import get_schedule
        sched = get_schedule()
        text = json.dumps(sched, ensure_ascii=False, indent=2)
        ingest_text(f"feishu:{conn.get('name','schedule')}", text, emb)
        n = 1
    else:
        return {"error": f"未知类型 {t}"}
    # 更新 last_sync
    allc = load_config().get("connectors", [])
    for c in allc:
        if c["id"] == cid:
            c["last_sync"] = int(time.time())
    save_config(load_config())
    return {"synced": n}
