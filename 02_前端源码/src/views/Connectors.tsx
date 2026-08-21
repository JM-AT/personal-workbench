import { useEffect, useState } from 'react'
import { addConnector, deleteConnector, listConnectors, syncConnector } from '../api'

type Conn = {
  id?: string
  name: string
  type: 'local_folder' | 'rest_api' | 'feishu'
  config: any
}

export default function Connectors() {
  const [conns, setConns] = useState<any[]>([])
  const [type, setType] = useState<Conn['type']>('local_folder')
  const [name, setName] = useState('')
  const [path, setPath] = useState('')
  const [url, setUrl] = useState('')
  const [msg, setMsg] = useState('')
  const [syncing, setSyncing] = useState('')

  async function refresh() {
    setConns(await listConnectors())
  }
  useEffect(() => { refresh() }, [])

  async function add() {
    const c: Conn = { name: name || type, type, config: {} }
    if (type === 'local_folder') {
      if (!path) return alert('请填写目录路径')
      c.config = { path, label: name }
    } else if (type === 'rest_api') {
      if (!url) return alert('请填写接口 URL')
      c.config = { url, label: name }
    } else if (type === 'feishu') {
      c.config = {}
    }
    const r = await addConnector(c)
    if (r.error) return alert(r.error)
    setName(''); setPath(''); setUrl('')
    refresh()
  }

  async function sync(cid: string) {
    setSyncing(cid)
    setMsg('')
    const r = await syncConnector(cid)
    setSyncing('')
    setMsg(r.error ? `同步失败：${r.error}` : `已同步，新增文档 ${r.synced} 个`)
    refresh()
  }

  async function del(cid: string) {
    if (!confirm('删除该接入配置？')) return
    await deleteConnector(cid)
    refresh()
  }

  return (
    <div className="view">
      <div className="card">
        <div className="card-head">
          <h3>数据接入</h3>
          <span className="tag">{conns.length} 个接入</span>
        </div>
        <p className="hint">
          把「其他软件的数据」灌进本地知识库，让 AI 基于这些数据回答。支持：本机文件夹（免联网）、
          REST 接口、飞书（当前为模拟）。接入后到「知识库问答」即可对话。
        </p>

        <div className="conn-form">
          <div className="row">
            <select value={type} onChange={(e) => setType(e.target.value as Conn['type'])}>
              <option value="local_folder">本机文件夹</option>
              <option value="rest_api">REST 接口</option>
              <option value="feishu">飞书（模拟）</option>
            </select>
            <input placeholder="名称（可选）" value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          {type === 'local_folder' && (
            <input placeholder="目录完整路径，如 D:\\docs" value={path}
              onChange={(e) => setPath(e.target.value)} />
          )}
          {type === 'rest_api' && (
            <input placeholder="接口 URL，如 https://api.xxx.com/data" value={url}
              onChange={(e) => setUrl(e.target.value)} />
          )}
          {type === 'feishu' && <div className="empty sm">将把模拟飞书日程作为知识入库。</div>}
          <button className="btn-primary" onClick={add}>＋ 添加接入</button>
        </div>

        {msg && <div className="msg">{msg}</div>}

        <div className="conn-list">
          {conns.length === 0 && <div className="empty">还没有接入，先添加一个试试。</div>}
          {conns.map((c) => (
            <div key={c.id} className="conn-item">
              <div className="conn-main">
                <div className="conn-name">{c.name}</div>
                <div className="conn-type">{c.type}</div>
                <div className="conn-meta">
                  {c.config?.path || c.config?.url || ''}
                  {c.last_sync ? ` · 上次同步 ${new Date(c.last_sync * 1000).toLocaleString('zh-CN')}` : ' · 未同步'}
                </div>
              </div>
              <div className="conn-actions">
                <button className="btn-primary sm" disabled={syncing === c.id}
                  onClick={() => sync(c.id)}>{syncing === c.id ? '同步中…' : '立即同步'}</button>
                <button className="btn-ghost sm" onClick={() => del(c.id)}>删除</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
