import { useEffect, useState } from 'react'
import { getSchedule } from '../api'

export default function Schedule() {
  const [data, setData] = useState<any>(null)

  useEffect(() => {
    getSchedule().then(setData)
  }, [])

  if (!data) return <div className="view loading">加载中…</div>

  const badge = (s: string) => (s === 'doing' ? '进行中' : s === 'done' ? '已完成' : '待办')

  return (
    <div className="view sched-view">
      <div className="date">{data.date} · <span className={`mode ${data.mode}`}>{data.mode === 'mock' ? '模拟数据' : '真实飞书'}</span></div>

      <ul className="sched-list">
        {data.items.map((it: any, i: number) => (
          <li key={i}>
            <span className="time">{it.time}</span>
            <span className="title">{it.title}</span>
            <span className={`status ${it.status}`}>{badge(it.status)}</span>
            <span className="src">{it.source}</span>
          </li>
        ))}
        {data.items.length === 0 && <li className="empty">今日暂无安排</li>}
      </ul>

      <div className="note">{data.note}</div>
    </div>
  )
}
