import { Activity, Database, LoaderCircle, ScanLine, Sprout, Users } from 'lucide-react'
import { useEffect, useState } from 'react'
import MiniBarChart from '../components/charts/MiniBarChart.jsx'
import PageHeader from '../components/common/PageHeader.jsx'
import StatCard from '../components/common/StatCard.jsx'
import { adminOverviewDemo } from '../data/demoData.js'
import { adminStatsApi } from '../services/stats.js'

function normalizeStats(payload) { return payload?.stats || payload?.data || payload }

export default function SystemStatsPage() {
  const [stats, setStats] = useState(adminOverviewDemo)
  const [mode, setMode] = useState('loading')
  useEffect(() => {
    let active = true
    adminStatsApi.overview().then((payload) => { if (active) { setStats(normalizeStats(payload)); setMode('api') } }).catch(() => { if (active) { setStats(adminOverviewDemo); setMode('demo') } })
    return () => { active = false }
  }, [])
  const roles = stats.users_by_role || []
  const diseases = stats.disease_breakdown || []
  const maxRole = Math.max(...roles.map((item) => Number(item.value || item.count || 0)), 1)
  return (
    <div className="mx-auto max-w-7xl"><PageHeader eyebrow="Tuần 6–7 • Admin Stats" title="Thống kê toàn hệ thống" description="Breakdown theo role, lượt quét và nhóm kết quả từ /stats/admin/overview." /><div className={`mb-5 flex items-center gap-2 rounded-2xl border p-4 text-sm ${mode === 'api' ? 'border-emerald-100 bg-emerald-50 text-emerald-800' : 'border-amber-100 bg-amber-50 text-amber-800'}`}>{mode === 'loading' && <LoaderCircle className="animate-spin" size={17} />}{mode === 'api' ? 'Đang hiển thị số liệu API trực tiếp.' : mode === 'demo' ? 'API chưa phản hồi, đang dùng số liệu demo.' : 'Đang tải thống kê...'}</div><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><StatCard icon={Users} label="Người dùng" value={stats.total_users || 0} /><StatCard icon={ScanLine} label="Tổng lượt quét" value={stats.total_scans || 0} tone="blue" /><StatCard icon={Sprout} label="Trang trại" value={stats.total_farms || 0} tone="amber" /><StatCard icon={Database} label="Model đang chạy" value={stats.active_model || '—'} tone="purple" /></div><div className="mt-6 grid gap-6 xl:grid-cols-[1.2fr_.8fr]"><section className="card p-5 sm:p-6"><div className="flex items-center justify-between"><div><h2 className="text-lg font-extrabold text-slate-900">Lượt quét 7 ngày</h2><p className="mt-1 text-sm text-slate-400">Tổng hợp toàn hệ thống</p></div><Activity className="text-leaf-600" size={21} /></div><MiniBarChart values={stats.scans_by_day || []} labels={['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']} /></section><section className="card p-5 sm:p-6"><h2 className="text-lg font-extrabold text-slate-900">Người dùng theo vai trò</h2><div className="mt-7 space-y-5">{roles.map((item) => { const value = Number(item.value || item.count || 0); return <div key={item.name || item.role}><div className="mb-2 flex justify-between text-sm"><span className="font-semibold text-slate-600">{item.name || item.role}</span><strong>{value}</strong></div><div className="h-2.5 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-sky-500" style={{ width: `${(value / maxRole) * 100}%` }} /></div></div> })}</div></section></div><section className="card mt-6 p-5 sm:p-6"><h2 className="text-lg font-extrabold text-slate-900">Phân bố kết quả chẩn đoán</h2><div className="mt-5 grid gap-4 sm:grid-cols-3">{diseases.map((item, index) => <div key={item.name || item.label} className={`rounded-2xl p-5 ${index === 0 ? 'bg-emerald-50 text-emerald-800' : index === 1 ? 'bg-amber-50 text-amber-800' : 'bg-violet-50 text-violet-800'}`}><p className="text-2xl font-black">{item.value || item.count}</p><p className="mt-1 text-sm font-semibold">{item.name || item.label}</p></div>)}</div></section></div>
  )
}
