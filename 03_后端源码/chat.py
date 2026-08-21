"""大模型对话：统一走 OpenAI 兼容接口（OpenAI / DeepSeek / 通义 / Ollama 等）。"""
from openai import OpenAI

from config import load_config


def chat(model_cfg: dict, messages: list, system: str = None,
         temperature: float = 0.7, max_tokens: int = 2000) -> str:
    """model_cfg: 单条模型配置；messages: [{role, content}]。"""
    if model_cfg.get("type") == "openai" and not model_cfg.get("api_key"):
        raise ValueError("该模型未配置 API Key，请在设置中填写后再用。")

    client = OpenAI(
        base_url=model_cfg.get("base_url") or None,
        api_key=model_cfg.get("api_key") or "EMPTY",
    )
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.extend(messages)

    resp = client.chat.completions.create(
        model=model_cfg.get("model"),
        messages=msgs,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content


def get_model_cfg(model_id: str) -> dict:
    cfg = load_config()
    m = next((x for x in cfg["models"] if x["id"] == model_id), None)
    if not m:
        raise ValueError(f"找不到模型 {model_id}")
    return m


def chat_stream(model_cfg: dict, messages: list, system: str = None,
                temperature: float = 0.7, max_tokens: int = 2000):
    """流式对话，yield 每个文本片段（增量）。"""
    if model_cfg.get("type") == "openai" and not model_cfg.get("api_key"):
        raise ValueError("该模型未配置 API Key，请在设置中填写后再用。")

    client = OpenAI(
        base_url=model_cfg.get("base_url") or None,
        api_key=model_cfg.get("api_key") or "EMPTY",
    )
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.extend(messages)

    stream = client.chat.completions.create(
        model=model_cfg.get("model"),
        messages=msgs,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
