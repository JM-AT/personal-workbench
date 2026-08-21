"""角色库：预设 + 自定义系统提示词模板。

每个角色：
{
  "id": "translator",
  "name": "翻译专家",
  "icon": "🌐",
  "prompt": "你是一名专业的翻译专家……",
  "temperature": 0.3,
  "builtin": true            # builtin 角色不可删除
}
"""
import copy

from config import load_config, save_config

PRESET_ROLES = [
    {
        "id": "general", "name": "通用助手", "icon": "💬",
        "prompt": "你是一个乐于助人的通用 AI 助手，回答准确、简洁、友好。",
        "temperature": 0.7, "builtin": True,
    },
    {
        "id": "translator", "name": "翻译专家", "icon": "🌐",
        "prompt": "你是一名专业的翻译专家。请准确翻译用户的内容，保持原意与语气；"
                  "若用户未指明目标语言，默认翻译成中文。只输出译文，无需解释。",
        "temperature": 0.3, "builtin": True,
    },
    {
        "id": "coder", "name": "编程助手", "icon": "🧑‍💻",
        "prompt": "你是一名资深软件工程师。回答时给出可运行的代码，"
                  "并简要说明关键点；涉及多条方案时给出推荐。优先使用用户当前技术栈。",
        "temperature": 0.2, "builtin": True,
    },
    {
        "id": "writer", "name": "写作助手", "icon": "✍️",
        "prompt": "你是一名写作助手，擅长润色、扩写与结构优化。"
                  "保持用户原有意图与风格，提升表达清晰度与感染力。",
        "temperature": 0.8, "builtin": True,
    },
    {
        "id": "analyst", "name": "分析顾问", "icon": "📊",
        "prompt": "你是一名严谨的商业/技术分析顾问。先拆解问题，再给结构化结论，"
                  "用数据或逻辑支撑观点，避免空泛。",
        "temperature": 0.5, "builtin": True,
    },
]


def _ensure_roles(cfg: dict) -> list:
    """返回角色列表：内置角色 + 用户自定义角色（合并去重）。"""
    custom = cfg.get("roles", []) or []
    custom_ids = {r["id"] for r in custom if isinstance(r, dict)}
    merged = [copy.deepcopy(r) for r in PRESET_ROLES if r["id"] not in custom_ids]
    merged.extend(custom)
    return merged


def list_roles() -> list:
    cfg = load_config()
    return _ensure_roles(cfg)


def get_role(role_id: str) -> dict:
    return next((r for r in list_roles() if r["id"] == role_id), None)


def add_role(role: dict) -> dict:
    cfg = load_config()
    roles = _ensure_roles(cfg)
    # 不允许覆盖内置 id
    if role["id"] in {r["id"] for r in roles}:
        return {"error": f"角色 id {role['id']} 已存在"}
    role = dict(role)
    role["builtin"] = False
    custom = [r for r in roles if not r.get("builtin")]
    custom.append(role)
    cfg["roles"] = custom
    save_config(cfg)
    return role


def delete_role(role_id: str) -> bool:
    cfg = load_config()
    roles = _ensure_roles(cfg)
    target = next((r for r in roles if r["id"] == role_id), None)
    if not target:
        return False
    if target.get("builtin"):
        return {"error": "内置角色不可删除"}
    custom = cfg.get("roles", []) or []
    cfg["roles"] = [r for r in custom if r.get("id") != role_id]
    save_config(cfg)
    return True
