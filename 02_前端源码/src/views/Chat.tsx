import { useEffect, useRef, useState } from 'react'
import {
  chatStream,
  createSession,
  deleteSession,
  exportSession,
  getSession,
  listRoles,
  listSessions,
  renameSession,
  saveSession,
} from '../api'

export default function Chat({ config }: { config: any }) {
  const enabledModels = config.models.filter((m: any) => m.enabled !== false)
  const [sessions, setSessions] = useState<any[]>([])
  const [sid, setSid] = useState<string>('')
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([])
  const [input, setInput] = useState('')
  const [modelId, setModelId] = useState(config.default_model || enabledModels[0]?.id)
  const [roleId, setRoleId] = useState<string>('general')
  const [roles, setRoles] = useState<any[]>([])
  const [useWeb, setUseWeb] = useState(false)
  const [sysOpen, setSysOpen] = useState(false)
  const [system, setSystem] = useState('')
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')
  const boxRef = useRef<HTMLDivElement>(null)

  // 初始：加载角色 + 会话列表，自动打开/新建一个会话
  useEffect(() => {
    listRoles().then(setRoles)
    refreshSessions()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function refreshSessions() {
    const list = await listSessions()
    setSessions(list)
    if (!sid && list.length > 0) openSession(list[0].id)
  }

  async function openSession(id: string) {
    const s = await getSession(id)
    if (s?.error) return
    setSid(id)
    setMessages(s.messages || [])
    if (s.model_id) setModelId(s.model_id)
    setRoleId(s.role_id || 'general')
  }

  async function newSession() {
    const s = await createSession({ model_id: modelId, role_id: roleId })
    setSid(s.id)
    setMessages([])
    refreshSessions()
  }

  async function removeSession(id: string) {
    await deleteSession(id)
    if (sid === id) setSid('')
    refreshSessions()
  }

  async function rename(id: string) {
    const t = prompt('重命名会话')
    if (t) {
      await renameSession(id, t)
      refreshSessions()
    }
  }

  useEffect(() => {
    boxRef.current?.scrollTo({ top: boxRef.current.scrollHeight })
  }, [messages, busy])

  // 当前角色的系统提示词（选中角色时自动填充）
  useEffect(() => {
    const r = roles.find((x) => x.id === roleId)
    if (r) setSystem(r.prompt)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [roleId, roles])

  async function persist() {
    if (!sid) return
    await saveSession({
      id: sid,
      model_id: modelId,
      role_id: roleId,
      messages,
    })
  }

  async function send() {
    if (!input.trim() || busy) return
    if (!sid) await newSession()
    const userMsg = { role: 'user', content: input.trim() }
    const next = [...messages, userMsg]
    setMessages(next)
    setInput('')
    setBusy(true)
    setErr('')

    // 先放一个空的 assistant 占位，流式追加
    setMessages([...next, { role: 'assistant', content: '' }])
    const cur = next
    const r = await chatStream(modelId, cur, {
      system: system || undefined,
      onDelta: (d) => {
        setMessages((prev) => {
          const copy = [...prev]
          copy[copy.length - 1] = { role: 'assistant', content: copy[copy.length - 1].content + d }
          return copy
        })
      },
      useWeb,
    })
    if (r.error) {
      setErr(r.error)
    }
    // 刷新最新消息（占位已被流式更新，这里确保落盘）
    setMessages((prev) => {
      const copy = [...prev]
      if (copy[copy.length - 1].role === 'assistant' && copy[copy.length - 1].content === '') {
        copy[copy.length - 1] = { role: 'assistant', content: r.text || r.error || '(无内容)' }
      }
      // 持久化
      if (sid) {
        saveSession({ id: sid, model_id: modelId, role_id: roleId, messages: copy })
      }
      return copy
    })
    if (sid) refreshSessions()
    setBusy(false)
  }

  const selRole = roles.find((x) => x.id === roleId)

  return (
    <div className="view chat-view">
      {/* 会话侧栏 */}
      <aside className="chat-side">
        <button className="btn-primary full" onClick={newSession}>＋ 新建对话</button>
        <div className="sess-list">
          {sessions.length === 0 && <div className="empty sm">还没有会话</div>}
          {sessions.map((s) => (
            <div key={s.id} className={`sess-item ${s.id === sid ? 'active' : ''}`} onClick={() => openSession(s.id)}>
              <div className="sess-title">{s.title}</div>
              <div className="sess-meta">{s.count} 条 · {s.model_id}</div>
              <div className="sess-actions">
                <button onClick={(e) => { e.stopPropagation(); rename(s.id) }}>改名</button>
                <button onClick={(e) => { e.stopPropagation(); removeSession(s.id) }}>删</button>
              </div>
            </div>
          ))}
        </div>
        {sid && (
          <button className="btn-ghost full" onClick={() => exportSession(sid)}>⬇ 导出此对话</button>
        )}
      </aside>

      <div className="chat-main">
        <div className="chat-toolbar">
          <select value={modelId} onChange={(e) => setModelId(e.target.value)}>
            {enabledModels.map((m: any) => (
              <option key={m.id} value={m.id}>{m.name}（{m.model}）</option>
            ))}
          </select>
          <select value={roleId} onChange={(e) => setRoleId(e.target.value)}>
            {roles.map((r: any) => (
              <option key={r.id} value={r.id}>{r.icon || '🤖'} {r.name}</option>
            ))}
          </select>
          <label className="web-toggle">
            <input type="checkbox" checked={useWeb} onChange={(e) => setUseWeb(e.target.checked)} />
            联网检索
          </label>
          <button className="btn-ghost" onClick={() => setSysOpen((v) => !v)}>系统提示词</button>
        </div>

        {sysOpen && (
          <details open className="sys-box">
            <summary>系统提示词（{selRole?.name || '默认'}）</summary>
            <textarea value={system} onChange={(e) => setSystem(e.target.value)} rows={3} />
          </details>
        )}

        <div className="chat-box" ref={boxRef}>
          {messages.length === 0 && <div className="empty">开始和你的本地智能体对话吧。<br />可切换角色、开启联网检索。</div>}
          {messages.map((m, i) => (
            <div key={i} className={`bubble ${m.role}`}>
              <div className="who">{m.role === 'user' ? '你' : '助手'}</div>
              <div className="text">{m.content || '……'}</div>
            </div>
          ))}
          {err && <div className="err">{err}</div>}
        </div>

        <div className="input-row">
          <textarea
            value={input}
            placeholder="输入消息，Enter 发送 / Shift+Enter 换行"
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                send()
              }
            }}
          />
          <button onClick={send} disabled={busy}>
            {busy ? '生成中…' : '发送'}
          </button>
        </div>
      </div>
    </div>
  )
}
