import { useEffect, useState } from 'react'
import Chat from './views/Chat'
import Knowledge from './views/Knowledge'
import Schedule from './views/Schedule'
import Settings from './views/Settings'
import Roles from './views/Roles'
import Connectors from './views/Connectors'
import { getConfig, getSchedule, listDocs } from './api'

type Tab = 'dashboard' | 'chat' | 'kb' | 'schedule' | 'roles' | 'connectors' | 'settings'

const today = () => {
  const d = new Date()
  const week = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'][d.getDay()]
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 ${week}`
}

function QuickCard({ icon, title, desc, onClick }: any) {
  return (
    <div className="quick-card" onClick={onClick}>
      <div className="qc-icon">{icon}</div>
      <div className="qc-title">{title}</div>
      <div className="qc-desc">{desc}</div>
    </div>
  )
}

function Dashboard({ config, setTab, schedule, docCount }: any) {
  const enabled = config?.models?.filter((m: any) => m.enabled !== false).length || 0
  const todayItems = schedule?.items?.slice(0, 3) || []
  const modeText = schedule?.mode === 'mock' ? '模拟数据' : '真实飞书'

  return (
    <div className="dashboard">
      <section className="card welcome-card">
        <h1>AI 工作台</h1>
        <p>纯本地 · 多模型可切换 · 知识库 RAG · 每日工作安排</p>
      </section>

      <section className="card">
        <h3>快速开始</h3>
        <div className="quick-grid">
          <QuickCard icon="💬" title="智能体对话" desc="调用多模型进行问答" onClick={() => setTab('chat')} />
          <QuickCard icon="📚" title="知识库问答" desc={`已入库 ${docCount} 份文档`} onClick={() => setTab('kb')} />
          <QuickCard icon="📅" title="每日安排" desc={todayItems.length ? `今日 ${schedule.items.length} 项` : '暂无安排'} onClick={() => setTab('schedule')} />
          <QuickCard icon="⚙️" title="模型设置" desc={`${enabled} 个模型可用`} onClick={() => setTab('settings')} />
        </div>
      </section>

      <div className="dash-cols">
        <section className="card dash-col">
          <div className="card-head">
            <h3>今日安排</h3>
            <span className="tag">{modeText}</span>
          </div>
          {todayItems.length === 0 && <div className="empty">今日暂无安排</div>}
          <ul className="mini-schedule">
            {todayItems.map((it: any, i: number) => (
              <li key={i}>
                <span className="time">{it.time}</span>
                <span className="title">{it.title}</span>
                <span className={`status ${it.status}`}>
                  {it.status === 'doing' ? '进行中' : it.status === 'done' ? '已完成' : '待办'}
                </span>
              </li>
            ))}
          </ul>
        </section>

        <section className="card dash-col">
          <h3>运行状态</h3>
          <div className="stat-grid">
            <div className="stat-cell">
              <div className="stat-num">{enabled}</div>
              <div className="stat-label">可用模型</div>
            </div>
            <div className="stat-cell">
              <div className="stat-num">{docCount}</div>
              <div className="stat-label">知识库文档</div>
            </div>
            <div className="stat-cell">
              <div className="stat-num">{schedule?.items?.length || 0}</div>
              <div className="stat-label">今日事项</div>
            </div>
            <div className="stat-cell">
              <div className="stat-num ok">✓</div>
              <div className="stat-label">本地服务</div>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}

export default function App() {
  const [tab, setTab] = useState<Tab>('dashboard')
  const [config, setConfig] = useState<any>(null)
  const [schedule, setSchedule] = useState<any>(null)
  const [docCount, setDocCount] = useState(0)
  const [search, setSearch] = useState('')

  useEffect(() => {
    getConfig().then(setConfig)
    getSchedule().then(setSchedule)
    listDocs().then((docs) => setDocCount(docs.length))
  }, [])

  const nav = (id: Tab, label: string) => (
    <button key={id} className={tab === id ? 'active' : ''} onClick={() => setTab(id)}>
      {label}
    </button>
  )

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">🧩</div>
          <div>
            <div className="brand-title">AI 工作台</div>
            <div className="brand-sub">Local · Multi-Model · RAG</div>
          </div>
        </div>

        <nav>
          <div className="nav-group">
            <span className="nav-label">工作台</span>
            {nav('dashboard', '工作台总览')}
          </div>

          <div className="nav-group">
            <span className="nav-label">AI 能力</span>
            {nav('chat', '智能体对话')}
            {nav('kb', '知识库问答')}
            {nav('roles', '角色库')}
            {nav('connectors', '数据接入')}
          </div>

          <div className="nav-group">
            <span className="nav-label">日程</span>
            {nav('schedule', '每日安排')}
          </div>

          <div className="nav-group">
            <span className="nav-label">系统</span>
            {nav('settings', '模型设置')}
          </div>
        </nav>
      </aside>

      <div className="right">
        <header className="topbar">
          <div className="topbar-left">
            <h2>{tab === 'dashboard' ? '工作台总览' : tab === 'chat' ? '智能体对话' : tab === 'kb' ? '知识库问答' : tab === 'schedule' ? '每日安排' : tab === 'roles' ? '角色库' : tab === 'connectors' ? '数据接入' : '模型设置'}</h2>
            <span className="today">{today()}</span>
          </div>
          <div className="topbar-right">
            <div className="search-box">
              <span className="search-icon">🔍</span>
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="搜索功能或文档…"
              />
            </div>
            <button className="btn-primary" onClick={() => setTab('kb')}>+ 快速新增</button>
            <div className="avatar">AI</div>
          </div>
        </header>

        <main className="main">
          {!config && <div className="loading">加载中…</div>}
          {config && tab === 'dashboard' && (
            <Dashboard config={config} setTab={setTab} schedule={schedule} docCount={docCount} />
          )}
          {config && tab === 'chat' && <Chat config={config} />}
          {config && tab === 'kb' && <Knowledge config={config} onChange={() => listDocs().then((d) => setDocCount(d.length))} />}
          {config && tab === 'schedule' && <Schedule />}
          {config && tab === 'roles' && <Roles />}
          {config && tab === 'connectors' && <Connectors />}
          {config && tab === 'settings' && <Settings config={config} setConfig={setConfig} />}
        </main>
      </div>
    </div>
  )
}
