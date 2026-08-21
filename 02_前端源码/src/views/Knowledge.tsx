import { useEffect, useState } from 'react'
import { deleteDoc, kbQuery, listDocs, uploadDoc } from '../api'

export default function Knowledge({ config, onChange }: { config: any; onChange?: () => void }) {
  const [docs, setDocs] = useState<any[]>([])
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadMsg, setUploadMsg] = useState('')
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [sources, setSources] = useState<string[]>([])
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState('')

  const enabledModels = config.models.filter((m: any) => m.enabled !== false)
  const [modelId, setModelId] = useState(config.default_model || enabledModels[0]?.id)

  async function refresh() {
    const d = await listDocs()
    setDocs(d)
    onChange?.()
  }
  useEffect(() => {
    refresh()
  }, [])

  async function onUpload() {
    if (!file) return
    setUploading(true)
    setUploadMsg('')
    const r = await uploadDoc(file)
    setUploading(false)
    if (r.error) setUploadMsg('上传失败：' + r.error)
    else setUploadMsg(`已入库《${r.filename}》，切分 ${r.chunks} 段`)
    setFile(null)
    refresh()
  }

  async function ask() {
    if (!question.trim() || busy) return
    setBusy(true)
    setErr('')
    setAnswer('')
    setSources([])
    const r = await kbQuery(question, modelId)
    setBusy(false)
    if (r.error) {
      setErr(r.error)
      if (r.context) setAnswer(r.context)
      return
    }
    setAnswer(r.answer)
    setSources(r.sources || [])
  }

  return (
    <div className="view kb-view">
      <div className="kb-cols">
        <div className="kb-docs">
          <h3>已上传文档</h3>
          {docs.length === 0 && <div className="empty">还没有文档</div>}
          <ul>
            {docs.map((d) => (
              <li key={d.doc}>
                <span>{d.doc} <em>（{d.chunks} 段）</em></span>
                <button onClick={async () => { await deleteDoc(d.doc); refresh() }}>删除</button>
              </li>
            ))}
          </ul>
          <div className="upload-row">
            <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} />
            <button onClick={onUpload} disabled={!file || uploading}>
              {uploading ? '入库中…' : '上传并向量化'}
            </button>
          </div>
          {uploadMsg && <div className="hint">{uploadMsg}</div>}
          <div className="hint">支持 .txt / .md / .pdf；嵌入默认 hash（离线），可在设置切换 fastembed 提升质量。</div>
        </div>

        <div className="kb-qa">
          <h3>基于知识库提问</h3>
          <div className="input-row">
            <select value={modelId} onChange={(e) => setModelId(e.target.value)}>
              {enabledModels.map((m: any) => (
                <option key={m.id} value={m.id}>{m.name}（{m.model}）</option>
              ))}
            </select>
            <textarea
              value={question}
              placeholder="输入问题…"
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); ask() } }}
            />
            <button onClick={ask} disabled={busy}>{busy ? '…' : '提问'}</button>
          </div>
          {err && <div className="err">{err}</div>}
          {answer && (
            <div className="answer">
              <div className="text">{answer}</div>
              {sources.length > 0 && (
                <div className="sources">来源：{sources.join('、')}</div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
