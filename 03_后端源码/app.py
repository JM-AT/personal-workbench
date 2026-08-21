"""本地 AI 工作台后端：对话 / 知识库 RAG / 每日工作安排 / 会话 / 角色 / 联网 / 数据接入。"""
import io
import json
import os

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, PlainTextResponse
from pydantic import BaseModel

import config as cfg_mod
from chat import chat as chat_fn, chat_stream
from connectors import (add_connector, delete_connector, list_connectors,
                        sync_connector)
from embeddings import Embedder
from kb import delete_doc, ingest_file, list_docs, query as kb_query
from roles import add_role, delete_role, list_roles
from schedule import get_schedule
from sessions import (create_session, delete_session, export_markdown,
                      get_session, list_sessions, rename_session, save_session)
from websearch import search as web_search, to_context as web_to_context

app = FastAPI(title="AI Workbench Local")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_embedder():
    return Embedder(cfg_mod.load_config()["embedding"])


def get_model_cfg(model_id: str = None) -> dict:
    cfg = cfg_mod.load_config()
    if not model_id:
        model_id = cfg.get("default_model")
    return next((x for x in cfg["models"] if x["id"] == model_id), None)


# ---------------- 配置 ----------------
@app.get("/api/config")
def get_config():
    return cfg_mod.load_config()


@app.post("/api/config")
def set_config(cfg: dict):
    return cfg_mod.save_config(cfg)


@app.get("/api/models")
def list_models():
    cfg = cfg_mod.load_config()
    return [
        {"id": m["id"], "name": m["name"], "type": m["type"],
         "model": m["model"], "enabled": m.get("enabled", True)}
        for m in cfg["models"]
    ]


# ---------------- 角色库 ----------------
@app.get("/api/roles")
def api_list_roles():
    return list_roles()


@app.post("/api/roles")
def api_add_role(role: dict):
    return add_role(role)


@app.delete("/api/roles/{rid}")
def api_del_role(rid: str):
    return delete_role(rid)


# ---------------- 对话（一次性） ----------------
class ChatReq(BaseModel):
    model_id: str
    messages: list
    system: str = None
    temperature: float = 0.7


@app.post("/api/chat")
def chat(req: ChatReq):
    m = get_model_cfg(req.model_id)
    if not m:
        return {"error": f"找不到模型 {req.model_id}"}
    if not m.get("enabled", True):
        return {"error": "该模型已禁用"}
    try:
        reply = chat_fn(m, req.messages, req.system, req.temperature)
        return {"reply": reply}
    except Exception as e:
        return {"error": f"调用失败：{e}"}


# ---------------- 对话（流式 SSE） ----------------
class StreamReq(BaseModel):
    model_id: str
    messages: list
    system: str = None
    temperature: float = 0.7


@app.post("/api/chat/stream")
def chat_stream_api(req: StreamReq):
    m = get_model_cfg(req.model_id)
    if not m:
        return {"error": f"找不到模型 {req.model_id}"}

    def gen():
        try:
            for piece in chat_stream(m, req.messages, req.system, req.temperature):
                yield f"data: {json.dumps({'delta': piece}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


# ---------------- 会话 ----------------
@app.get("/api/sessions")
def api_list_sessions():
    return list_sessions()


@app.post("/api/sessions")
def api_create_session(data: dict = None):
    data = data or {}
    return create_session(data.get("title"), data.get("model_id"), data.get("role_id"))


@app.get("/api/sessions/{sid}")
def api_get_session(sid: str):
    s = get_session(sid)
    return s or {"error": "会话不存在"}


@app.post("/api/sessions/{sid}")
def api_save_session(sess: dict):
    return save_session(sess)


@app.post("/api/sessions/{sid}/rename")
def api_rename(sid: str, data: dict):
    return rename_session(sid, data.get("title", "")) or {"error": "会话不存在"}


@app.delete("/api/sessions/{sid}")
def api_delete(sid: str):
    return delete_session(sid)


@app.get("/api/sessions/{sid}/export")
def api_export(sid: str):
    md = export_markdown(sid)
    if md is None:
        return {"error": "会话不存在"}
    headers = {"Content-Disposition": f"attachment; filename={sid}.md"}
    return PlainTextResponse(md, headers=headers)


# ---------------- 知识库 ----------------
def extract_text(filename: str, content: bytes) -> str:
    if filename.lower().endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(content))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("gbk", "ignore")


@app.post("/api/kb/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    text = extract_text(file.filename, content)
    n = ingest_file(file.filename, text, get_embedder())
    return {"filename": file.filename, "chunks": n}


@app.get("/api/kb/documents")
def documents():
    return list_docs()


@app.delete("/api/kb/documents/{name}")
def del_doc(name: str):
    return delete_doc(name)


class KBQuery(BaseModel):
    question: str
    top_k: int = 4
    model_id: str = None


@app.post("/api/kb/query")
def kb_q(req: KBQuery):
    emb = get_embedder()
    res = kb_query(req.question, emb, req.top_k)
    if not res:
        return {"answer": "知识库还没有内容，请先上传文档。", "sources": []}

    contexts, docs = [], []
    for row in res:
        contexts.append(f"[来自 {row['doc']}]\n{row['chunk']}")
        docs.append(row["doc"])
    context = "\n\n".join(contexts)
    sources = list(dict.fromkeys(docs))

    cfg = cfg_mod.load_config()
    model_id = req.model_id or cfg.get("default_model")
    m = get_model_cfg(model_id)
    if not m:
        return {"error": f"找不到模型 {model_id}"}
    if m.get("type") == "openai" and not m.get("api_key"):
        return {
            "answer": "（已检索到相关片段，但未配置模型 Key，无法作答）\n\n" + context,
            "sources": sources,
        }
    system = (
        "你是严谨的知识库助手，只依据下方【资料】回答；"
        "资料里没有的信息就如实说不知道，不要编造。\n\n【资料】\n" + context
    )
    try:
        ans = chat_fn(m, [{"role": "user", "content": req.question}], system)
        return {"answer": ans, "sources": sources}
    except Exception as e:
        return {"error": f"生成失败：{e}", "context": context, "sources": sources}


# ---------------- 联网检索 ----------------
class WebReq(BaseModel):
    query: str
    top_n: int = 5


@app.post("/api/websearch")
def api_websearch(req: WebReq):
    try:
        results = web_search(req.query, top_n=req.top_n)
        return {"results": results,
                "context": web_to_context(results)}
    except Exception as e:
        return {"error": f"检索失败：{e}"}


# ---------------- 数据接入（连接器） ----------------
@app.get("/api/connectors")
def api_list_conn():
    return list_connectors()


@app.post("/api/connectors")
def api_add_conn(c: dict):
    return add_connector(c)


@app.delete("/api/connectors/{cid}")
def api_del_conn(cid: str):
    return delete_connector(cid)


@app.post("/api/connectors/{cid}/sync")
def api_sync_conn(cid: str):
    try:
        return sync_connector(cid, get_embedder())
    except Exception as e:
        return {"error": f"同步失败：{e}"}


# ---------------- 每日工作安排 ----------------
@app.get("/api/schedule")
def schedule():
    return get_schedule()


@app.get("/api/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
