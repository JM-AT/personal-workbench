// 浏览器开发：相对路径经 Vite 代理到 :8000；Tauri 生产：直连本地后端。
const isTauri =
  typeof window !== "undefined" &&
  (("__TAURI__" in window) || location.protocol === "tauri:");
export const API_BASE = isTauri ? "http://127.0.0.1:8000/api" : "/api";

export async function getConfig() {
  return (await fetch(`${API_BASE}/config`)).json();
}
export async function saveConfig(cfg: any) {
  return (
    await fetch(`${API_BASE}/config`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cfg),
    })
  ).json();
}
export async function listModels() {
  return (await fetch(`${API_BASE}/models`)).json();
}

// ---------------- 角色 ----------------
export async function listRoles() {
  return (await fetch(`${API_BASE}/roles`)).json();
}
export async function addRole(role: any) {
  return (
    await fetch(`${API_BASE}/roles`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(role),
    })
  ).json();
}
export async function deleteRole(rid: string) {
  return (await fetch(`${API_BASE}/roles/${encodeURIComponent(rid)}`, { method: "DELETE" })).json();
}

// ---------------- 普通对话 ----------------
export async function chat(model_id: string, messages: any[], system?: string, temperature = 0.7) {
  return (
    await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model_id, messages, system, temperature }),
    })
  ).json();
}

// ---------------- 流式对话（SSE） ----------------
// 返回 Promise<{text, error}>，过程中通过 onDelta 回调实时拿到片段。
export async function chatStream(
  model_id: string,
  messages: any[],
  opts: { system?: string; temperature?: number; onDelta?: (s: string) => void; useWeb?: boolean }
): Promise<{ text: string; error?: string }> {
  let body: any = {
    model_id,
    messages,
    system: opts.system,
    temperature: opts.temperature ?? 0.7,
  };
  if (opts.useWeb) body.web = true;
  const resp = await fetch(`${API_BASE}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok) return { text: "", error: `HTTP ${resp.status}` };
  const reader = resp.body!.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  let text = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const parts = buf.split("\n\n");
    buf = parts.pop() || "";
    for (const part of parts) {
      const line = part.trim();
      if (!line.startsWith("data:")) continue;
      const payload = line.slice(5).trim();
      if (payload === "[DONE]") continue;
      try {
        const obj = JSON.parse(payload);
        if (obj.error) return { text, error: obj.error };
        if (obj.delta) {
          text += obj.delta;
          opts.onDelta?.(obj.delta);
        }
      } catch {
        /* ignore */
      }
    }
  }
  return { text };
}

// ---------------- 会话 ----------------
export async function listSessions() {
  return (await fetch(`${API_BASE}/sessions`)).json();
}
export async function createSession(data?: any) {
  return (
    await fetch(`${API_BASE}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data || {}),
    })
  ).json();
}
export async function getSession(sid: string) {
  return (await fetch(`${API_BASE}/sessions/${sid}`)).json();
}
export async function saveSession(sess: any) {
  return (
    await fetch(`${API_BASE}/sessions/${sess.id}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(sess),
    })
  ).json();
}
export async function renameSession(sid: string, title: string) {
  return (
    await fetch(`${API_BASE}/sessions/${sid}/rename`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title }),
    })
  ).json();
}
export async function deleteSession(sid: string) {
  return (await fetch(`${API_BASE}/sessions/${sid}`, { method: "DELETE" })).json();
}
export async function exportSession(sid: string) {
  window.open(`${API_BASE}/sessions/${sid}/export`, "_blank");
}

// ---------------- 知识库 ----------------
export async function uploadDoc(file: File) {
  const fd = new FormData();
  fd.append("file", file);
  return (await fetch(`${API_BASE}/kb/upload`, { method: "POST", body: fd })).json();
}
export async function listDocs() {
  return (await fetch(`${API_BASE}/kb/documents`)).json();
}
export async function deleteDoc(name: string) {
  return (
    await fetch(`${API_BASE}/kb/documents/${encodeURIComponent(name)}`, { method: "DELETE" })
  ).json();
}
export async function kbQuery(question: string, model_id?: string, top_k = 4) {
  return (
    await fetch(`${API_BASE}/kb/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, model_id, top_k }),
    })
  ).json();
}

// ---------------- 联网检索 ----------------
export async function webSearch(query: string, top_n = 5) {
  return (
    await fetch(`${API_BASE}/websearch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, top_n }),
    })
  ).json();
}

// ---------------- 数据接入 ----------------
export async function listConnectors() {
  return (await fetch(`${API_BASE}/connectors`)).json();
}
export async function addConnector(c: any) {
  return (
    await fetch(`${API_BASE}/connectors`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(c),
    })
  ).json();
}
export async function deleteConnector(cid: string) {
  return (
    await fetch(`${API_BASE}/connectors/${encodeURIComponent(cid)}`, { method: "DELETE" })
  ).json();
}
export async function syncConnector(cid: string) {
  return (
    await fetch(`${API_BASE}/connectors/${encodeURIComponent(cid)}/sync`, { method: "POST" })
  ).json();
}

// ---------------- 日程 ----------------
export async function getSchedule() {
  return (await fetch(`${API_BASE}/schedule`)).json();
}
