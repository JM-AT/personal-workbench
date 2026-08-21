"""联网检索：无 Key 用 DuckDuckGo Lite（HTML 解析），有 Key 用 SerpAPI / Bing。

返回结构：[{title, url, snippet}, ...]
依赖：requests（已装）；DDG 解析不需额外包。SerpAPI/Bing 取配置里的 key。
"""
import os
import re
import urllib.parse

import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}
TIMEOUT = 10


def _ddg_lite(query: str, top_n: int = 5) -> list:
    """DuckDuckGo Lite 轻量检索（无需 API Key，但可能受频率限制）。"""
    url = "https://lite.duckduckgo.com/lite/"
    try:
        resp = requests.post(url, data={"q": query, "kl": "cn-zh"},
                             headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        return [{"title": f"(检索失败: {e})", "url": "", "snippet": ""}]

    # 解析结果块：每条结果标题在 <a class="result-link">，摘要在 <td class="result-snippet">
    results = []
    # 标题链接
    titles = re.findall(r'<a[^>]+class="result-link"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                        html, re.S)
    snippets = re.findall(r'<td[^>]+class="result-snippet"[^>]*>(.*?)</td>', html, re.S)
    for i, (href, title) in enumerate(titles[:top_n]):
        snippet = ""
        if i < len(snippets):
            snippet = re.sub(r"<[^>]+>", "", snippets[i])
            snippet = re.sub(r"\s+", " ", snippet).strip()
        title = re.sub(r"<[^>]+>", "", title)
        title = re.sub(r"\s+", " ", title).strip()
        results.append({"title": title or "(无标题)", "url": href, "snippet": snippet})
    return results


def _serpapi(query: str, api_key: str, top_n: int = 5) -> list:
    url = "https://serpapi.com/search.json"
    try:
        resp = requests.get(url, params={"q": query, "api_key": api_key, "hl": "zh-cn"},
                            headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return [{"title": f"(SerpAPI 失败: {e})", "url": "", "snippet": ""}]
    out = []
    for r in data.get("organic_results", [])[:top_n]:
        out.append({
            "title": r.get("title", ""),
            "url": r.get("link", ""),
            "snippet": re.sub(r"\s+", " ", r.get("snippet", "")).strip(),
        })
    return out


def _bing(query: str, api_key: str, top_n: int = 5) -> list:
    url = "https://api.bing.microsoft.com/v7.0/search"
    try:
        resp = requests.get(url, params={"q": query, "count": top_n, "mkt": "zh-CN"},
                            headers={"Ocp-Apim-Subscription-Key": api_key,
                                      "User-Agent": HEADERS["User-Agent"]},
                            timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return [{"title": f"(Bing 失败: {e})", "url": "", "snippet": ""}]
    out = []
    for r in data.get("webPages", {}).get("value", [])[:top_n]:
        out.append({"title": r.get("name", ""), "url": r.get("url", ""),
                    "snippet": re.sub(r"\s+", " ", r.get("snippet", "")).strip()})
    return out


def search(query: str, cfg: dict = None, top_n: int = 5) -> list:
    """统一入口。优先用配置里的 key（serpapi / bing），否则走 DDG Lite。"""
    if cfg is None:
        from config import load_config
        cfg = load_config()
    ws = cfg.get("websearch", {})
    provider = ws.get("provider", "auto")
    if provider == "serpapi" and ws.get("serpapi_key"):
        return _serpapi(query, ws["serpapi_key"], top_n)
    if provider == "bing" and ws.get("bing_key"):
        return _bing(query, ws["bing_key"], top_n)
    if provider == "ddg":
        return _ddg_lite(query, top_n)
    # auto：有 key 用 key，否则 DDG
    if ws.get("serpapi_key"):
        return _serpapi(query, ws["serpapi_key"], top_n)
    if ws.get("bing_key"):
        return _bing(query, ws["bing_key"], top_n)
    return _ddg_lite(query, top_n)


def to_context(results: list, max_chars: int = 1500) -> str:
    """把检索结果拼成喂给模型的上下文。"""
    if not results:
        return ""
    parts = []
    for i, r in enumerate(results, 1):
        snippet = (r.get("snippet") or "")[:max_chars]
        parts.append(f"[{i}] {r.get('title','')}\nURL: {r.get('url','')}\n{snippet}")
    return "\n\n".join(parts)
