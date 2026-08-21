import { useEffect, useState } from 'react'
import { addRole, deleteRole, listRoles } from '../api'

export default function Roles() {
  const [roles, setRoles] = useState<any[]>([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ id: '', name: '', icon: '🤖', prompt: '', temperature: 0.7 })

  async function refresh() {
    setRoles(await listRoles())
  }
  useEffect(() => { refresh() }, [])

  async function submit() {
    if (!form.id || !form.name || !form.prompt) return alert('请填写 id / 名称 / 提示词')
    const r = await addRole(form)
    if (r.error) return alert(r.error)
    setForm({ id: '', name: '', icon: '🤖', prompt: '', temperature: 0.7 })
    setShowForm(false)
    refresh()
  }

  async function del(r: any) {
    if (r.builtin) return alert('内置角色不可删除')
    if (!confirm(`删除角色「${r.name}」？`)) return
    await deleteRole(r.id)
    refresh()
  }

  return (
    <div className="view">
      <div className="card">
        <div className="card-head">
          <h3>角色库</h3>
          <button className="btn-primary" onClick={() => setShowForm((v) => !v)}>＋ 新建角色</button>
        </div>
        <p className="hint">内置角色开箱即用；自定义角色可在对话页一键切换，决定系统提示词与温度。</p>

        {showForm && (
          <div className="role-form">
            <div className="row">
              <input placeholder="角色 id（英文，如 sales）" value={form.id}
                onChange={(e) => setForm({ ...form, id: e.target.value })} />
              <input placeholder="名称" value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })} />
              <input placeholder="图标 emoji" value={form.icon} style={{ width: 80 }}
                onChange={(e) => setForm({ ...form, icon: e.target.value })} />
            </div>
            <textarea placeholder="系统提示词（角色人设）" rows={3} value={form.prompt}
              onChange={(e) => setForm({ ...form, prompt: e.target.value })} />
            <div className="row">
              <label>温度：{form.temperature}</label>
              <input type="range" min={0} max={1} step={0.1} value={form.temperature}
                onChange={(e) => setForm({ ...form, temperature: parseFloat(e.target.value) })} />
              <button className="btn-primary" onClick={submit}>保存角色</button>
            </div>
          </div>
        )}

        <div className="role-grid">
          {roles.map((r) => (
            <div key={r.id} className="role-card">
              <div className="role-icon">{r.icon}</div>
              <div className="role-name">{r.name}</div>
              <div className="role-prompt">{r.prompt}</div>
              <div className="role-foot">
                <span className="tag">temp {r.temperature}</span>
                {r.builtin ? <span className="tag dim">内置</span> : (
                  <button className="btn-ghost sm" onClick={() => del(r)}>删除</button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
