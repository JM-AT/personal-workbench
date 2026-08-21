import { useState } from 'react'
import { saveConfig } from '../api'

export default function Settings({ config, setConfig }: { config: any; setConfig: any }) {
  const [draft, setDraft] = useState(JSON.parse(JSON.stringify(config)))
  const [msg, setMsg] = useState('')
  const [saving, setSaving] = useState(false)

  function updateModel(i: number, key: string, val: any) {
    const m = [...draft.models]
    m[i] = { ...m[i], [key]: val }
    setDraft({ ...draft, models: m })
  }
  function updateEmbed(key: string, val: any) {
    setDraft({ ...draft, embedding: { ...draft.embedding, [key]: val } })
  }
  function updateFeishu(key: string, val: any) {
    setDraft({ ...draft, feishu: { ...draft.feishu, [key]: val } })
  }

  async function save() {
    setSaving(true)
    setMsg('')
    const r = await saveConfig(draft)
    setSaving(false)
    if (r && !r.error) {
      setConfig(r)
      setMsg('已保存 ✓')
    } else setMsg('保存失败')
  }

  return (
    <div className="view settings-view">
      {msg && <div className="hint" style={{ marginBottom: 12 }}>{msg}</div>}

      <section>
        <div className="card-head">
          <h3>默认模型</h3>
          <button onClick={save} disabled={saving}>{saving ? '保存中…' : '保存'}</button>
        </div>
        <select value={draft.default_model} onChange={(e) => setDraft({ ...draft, default_model: e.target.value })}>
          {draft.models.map((m: any) => (
            <option key={m.id} value={m.id}>{m.name}（{m.model}）</option>
          ))}
        </select>
      </section>

      <section>
        <h3>模型供应商（多模型可切换）</h3>
        {draft.models.map((m: any, i: number) => (
          <div className="model-card" key={m.id}>
            <div className="mc-row">
              <label>名称</label>
              <input value={m.name} onChange={(e) => updateModel(i, 'name', e.target.value)} />
              <label>类型</label>
              <select value={m.type} onChange={(e) => updateModel(i, 'type', e.target.value)}>
                <option value="openai">OpenAI 兼容</option>
                <option value="ollama">Ollama 本地</option>
              </select>
              <label>启用</label>
              <input type="checkbox" checked={m.enabled !== false} onChange={(e) => updateModel(i, 'enabled', e.target.checked)} />
            </div>
            <div className="mc-row">
              <label>Base URL</label>
              <input value={m.base_url} onChange={(e) => updateModel(i, 'base_url', e.target.value)} />
            </div>
            <div className="mc-row">
              <label>模型名</label>
              <input value={m.model} onChange={(e) => updateModel(i, 'model', e.target.value)} />
              <label>API Key</label>
              <input type="password" value={m.api_key || ''} onChange={(e) => updateModel(i, 'api_key', e.target.value)} placeholder="本地模型可留空" />
            </div>
          </div>
        ))}
      </section>

      <section>
        <h3>知识库嵌入方式</h3>
        <div className="mc-row">
          <label>方式</label>
          <select value={draft.embedding.provider} onChange={(e) => updateEmbed('provider', e.target.value)}>
            <option value="hash">hash（离线·无需模型）</option>
            <option value="fastembed">fastembed（本地小模型·质量更好）</option>
            <option value="openai">OpenAI 兼容（含 Ollama 嵌入）</option>
          </select>
          <label>模型</label>
          <input value={draft.embedding.model} onChange={(e) => updateEmbed('model', e.target.value)} />
          <label>维度</label>
          <input type="number" value={draft.embedding.dim} onChange={(e) => updateEmbed('dim', Number(e.target.value))} />
        </div>
        <div className="hint">切换 fastembed / openai 后，已入库的向量维度需保持一致，否则请清空 data/lancedb 重新入库。</div>
      </section>

      <section>
        <h3>飞书工作安排</h3>
        <div className="mc-row">
          <label>模式</label>
          <select value={draft.feishu.mode} onChange={(e) => updateFeishu('mode', e.target.value)}>
            <option value="mock">模拟数据</option>
            <option value="real">真实飞书（需填下方凭证）</option>
          </select>
        </div>
        <div className="mc-row">
          <label>App ID</label>
          <input value={draft.feishu.app_id || ''} onChange={(e) => updateFeishu('app_id', e.target.value)} />
          <label>App Secret</label>
          <input type="password" value={draft.feishu.app_secret || ''} onChange={(e) => updateFeishu('app_secret', e.target.value)} />
        </div>
        <div className="hint">真实对接需在飞书开放平台创建应用并开通日历/任务权限，再在 backend/schedule.py 中补全 API 调用。</div>
      </section>
    </div>
  )
}
