import { AlertTriangle, Ban, CheckCircle2, LoaderCircle, ScanLine, Sprout } from 'lucide-react'
import { useEffect, useState } from 'react'
import { statsApi } from '../../api/stats.js'
import MiniBarChart from '../../components/charts/MiniBarChart.jsx'
import PageHeader from '../../components/common/PageHeader.jsx'
import StatCard from '../../components/common/StatCard.jsx'
import { farmStatsDemo, initialFarms } from '../../data/demoData.js'
import { loadCollection } from '../../utils/storage.js'
import { usePreferences } from '../../contexts/PreferencesContext.jsx'

function normalizeStats(payload) {
  return payload?.stats || payload?.data || payload
}

export default function FarmDashboardPage() {
  const { language } = usePreferences()
  const copy = language === 'vi' ? {
    eyebrow: 'Tuần 7 • Dashboard Persona Quản lý', title: 'Dashboard theo trang trại', description: 'Theo dõi lượt quét và tình trạng cây trồng của từng Farm từ API /stats/farm/{id}.', viewing: 'Trang trại đang xem', api: 'Dữ liệu API trực tiếp', demo: 'Dữ liệu demo', loading: 'Đang tải số liệu...', scans: 'Tổng lượt quét', healthy: 'Mẫu khỏe mạnh', attention: 'Mẫu cần chú ý', invalid: 'Ảnh OOD/không hợp lệ', week: 'Lượt quét 7 ngày', distribution: 'Phân bố kết quả', breakdown: 'Tỷ lệ theo nhóm bệnh',
  } : {
    eyebrow: 'Week 7 • Manager dashboard', title: 'Farm dashboard', description: 'Monitor scans and crop health per farm from /stats/farm/{id}.', viewing: 'Viewing farm', api: 'Live API data', demo: 'Demo data', loading: 'Loading metrics...', scans: 'Total scans', healthy: 'Healthy samples', attention: 'Needs attention', invalid: 'OOD/invalid images', week: 'Scans over 7 days', distribution: 'Result distribution', breakdown: 'Breakdown by disease group',
  }
  const [farms] = useState(() => loadCollection('plantcare_farms', initialFarms))
  const [farmId, setFarmId] = useState(String(farms[0]?.id || ''))
  const [stats, setStats] = useState(farmStatsDemo[farms[0]?.id] || farmStatsDemo[1])
  const [mode, setMode] = useState('loading')

  useEffect(() => {
    if (!farmId) return
    let active = true
    setMode('loading')
    statsApi.farm(farmId)
      .then((payload) => {
        if (!active) return
        setStats(normalizeStats(payload))
        setMode('api')
      })
      .catch(() => {
        if (!active) return
        setStats(farmStatsDemo[farmId] || farmStatsDemo[1])
        setMode('demo')
      })
    return () => { active = false }
  }, [farmId])

  const selectedFarm = farms.find((farm) => String(farm.id) === farmId)
  const trend = stats?.trend || stats?.daily_scans || []
  const diseases = stats?.diseases || stats?.disease_breakdown || []
  const totalDisease = Math.max(diseases.reduce((sum, item) => sum + Number(item.value || item.count || 0), 0), 1)

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader eyebrow={copy.eyebrow} title={copy.title} description={copy.description} />
      <div className="mb-6 flex flex-col gap-4 rounded-3xl border border-leaf-100 bg-white p-5 shadow-soft sm:flex-row sm:items-end sm:justify-between">
        <label className="w-full max-w-lg"><span className="mb-2 block text-xs font-bold uppercase tracking-wider text-leaf-700">{copy.viewing}</span><select className="input-control" value={farmId} onChange={(event) => setFarmId(event.target.value)}>{farms.map((farm) => <option key={farm.id} value={farm.id}>{farm.name} — {farm.location}</option>)}</select></label>
        <div className={`inline-flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-semibold ${mode === 'api' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'}`}>{mode === 'loading' && <LoaderCircle className="animate-spin" size={15} />}{mode === 'api' ? copy.api : mode === 'demo' ? copy.demo : copy.loading}</div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={ScanLine} label={copy.scans} value={stats?.total_scans || 0} />
        <StatCard icon={CheckCircle2} label={copy.healthy} value={stats?.healthy || 0} tone="blue" />
        <StatCard icon={AlertTriangle} label={copy.attention} value={stats?.attention || 0} tone="amber" />
        <StatCard icon={Ban} label={copy.invalid} value={stats?.invalid || 0} tone="purple" />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1.15fr_.85fr]">
        <section className="card p-5 sm:p-6"><div className="flex items-center justify-between"><div><h2 className="text-lg font-extrabold text-slate-900">{copy.week}</h2><p className="mt-1 text-sm text-slate-400">{selectedFarm?.name}</p></div><span className="grid h-10 w-10 place-items-center rounded-xl bg-leaf-50 text-leaf-700"><ScanLine size={19} /></span></div><MiniBarChart values={trend} labels={language === 'vi' ? ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'] : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']} /></section>
        <section className="card p-5 sm:p-6"><div className="flex items-center justify-between"><div><h2 className="text-lg font-extrabold text-slate-900">{copy.distribution}</h2><p className="mt-1 text-sm text-slate-400">{copy.breakdown}</p></div><Sprout className="text-leaf-600" size={21} /></div><div className="mt-7 space-y-5">{diseases.map((item, index) => { const value = Number(item.value || item.count || 0); const percent = (value / totalDisease) * 100; return <div key={item.name || item.label}><div className="mb-2 flex justify-between text-sm"><span className="font-semibold text-slate-600">{item.name || item.label}</span><strong className="text-slate-800">{value} ({percent.toFixed(0)}%)</strong></div><div className="h-2.5 overflow-hidden rounded-full bg-slate-100"><div className={`h-full rounded-full ${index === 0 ? 'bg-leaf-500' : index === 1 ? 'bg-amber-400' : 'bg-sky-400'}`} style={{ width: `${percent}%` }} /></div></div> })}</div></section>
      </div>
    </div>
  )
}
