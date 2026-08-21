"""每日工作安排：当前为模拟飞书数据；接入真实飞书时改 mode=real 并补全 API。"""
import datetime

from config import load_config


def get_schedule():
    cfg = load_config()
    fs = cfg.get("feishu", {})
    if fs.get("mode") == "real":
        # TODO: 用 app_id/app_secret 换取 tenant_access_token，
        # 调用 https://open.feishu.cn/open-apis/calendar/v4/calendars/... 拉取日程。
        return {
            "mode": "real",
            "date": datetime.date.today().isoformat(),
            "items": [],
            "note": "真实飞书对接尚未实现：请在 schedule.py 中填入凭证并调用飞书开放平台日历/任务 API。",
        }

    today = datetime.date.today().isoformat()
    items = [
        {"time": "09:30", "title": "团队晨会 sync", "status": "todo", "source": "飞书日历"},
        {"time": "11:00", "title": "评审 AI 工作台原型", "status": "todo", "source": "飞书任务"},
        {"time": "14:00", "title": "与客户对齐需求", "status": "doing", "source": "飞书日历"},
        {"time": "16:30", "title": "整理本周周报", "status": "todo", "source": "飞书文档"},
        {"time": "18:00", "title": "健身", "status": "todo", "source": "飞书日程"},
    ]
    return {
        "mode": "mock",
        "date": today,
        "items": items,
        "note": "当前为模拟数据。在「设置」中将飞书模式切到真实并填入 app_id/app_secret 即可对接。",
    }
