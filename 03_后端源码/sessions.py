"""多会话管理：对话历史持久化到 data/sessions/<id>.json。

每条会话结构：
{
  "id": "20260101-abc123",
  "title": "新对话",
  "created_at": 1700000000.0,
  "updated_at": 1700000000.0,
  "model_id": "gpt",
  "role_id": null,            # 绑定的角色，None 表示默认
  "messages": [               # [{role, content}]
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
"""
import glob
import json
import os
import time
import uuid

from config import CONFIG_DIR

SESSIONS_DIR = os.path.join(CONFIG_DIR, "sessions")
os.makedirs(SESSIONS_DIR, exist_ok=True)


def _path(sid: str) -> str:
    return os.path.join(SESSIONS_DIR, f"{sid}.json")


def _now() -> float:
    return time.time()


def list_sessions() -> list:
    items = []
    for fp in glob.glob(os.path.join(SESSIONS_DIR, "*.json")):
        try:
            with open(fp, "r", encoding="utf-8") as f:
                d = json.load(f)
            items.append({
                "id": d.get("id"),
                "title": d.get("title", "未命名"),
                "model_id": d.get("model_id"),
                "role_id": d.get("role_id"),
                "updated_at": d.get("updated_at", 0),
                "count": len(d.get("messages", [])),
            })
        except Exception:
            continue
    items.sort(key=lambda x: x["updated_at"], reverse=True)
    return items


def get_session(sid: str) -> dict:
    if not os.path.exists(_path(sid)):
        return None
    with open(_path(sid), "r", encoding="utf-8") as f:
        return json.load(f)


def create_session(title: str = None, model_id: str = None,
                   role_id: str = None) -> dict:
    sid = time.strftime("%Y%m%d-") + uuid.uuid4().hex[:8]
    sess = {
        "id": sid,
        "title": title or "新对话",
        "created_at": _now(),
        "updated_at": _now(),
        "model_id": model_id,
        "role_id": role_id,
        "messages": [],
    }
    save_session(sess)
    return sess


def save_session(sess: dict) -> dict:
    sess["updated_at"] = _now()
    # 自动用首条用户消息当标题
    if (sess.get("title") in (None, "新对话", "")) and sess.get("messages"):
        for m in sess["messages"]:
            if m["role"] == "user":
                sess["title"] = m["content"][:30]
                break
    with open(_path(sess["id"]), "w", encoding="utf-8") as f:
        json.dump(sess, f, ensure_ascii=False, indent=2)
    return sess


def rename_session(sid: str, title: str) -> dict:
    sess = get_session(sid)
    if not sess:
        return None
    sess["title"] = title
    return save_session(sess)


def delete_session(sid: str) -> bool:
    if os.path.exists(_path(sid)):
        os.remove(_path(sid))
        return True
    return False


def export_markdown(sid: str) -> str:
    sess = get_session(sid)
    if not sess:
        return None
    lines = [f"# {sess.get('title', '对话记录')}", "",
             f"> 模型：{sess.get('model_id')}　导出时间：{time.strftime('%Y-%m-%d %H:%M')}", ""]
    for m in sess.get("messages", []):
        who = "🧑 用户" if m["role"] == "user" else "🤖 助手"
        lines.append(f"**{who}**\n")
        lines.append(m["content"])
        lines.append("")
    return "\n".join(lines)
