import { Activity, Database, ScanLine, Sprout, Users } from 'lucide-react'
import { useEffect, useState } from 'react'
import MiniBarChart from '../components/charts/MiniBarChart.jsx'
import PageHeader from '../components/common/PageHeader.jsx'
import StatCard from '../components/common/StatCard.jsx'
import { useLanguage } from '../contexts/LanguageContext.jsx'
import { adminUsersApi } from '../services/auth.js'
import { getApiError } from '../services/client.js'
import { adminStatsApi } from '../services/stats.js'
import { systemHealthApi } from '../services/systemHealth.js'

function unwrapOverview(payload) { return payload?.stats || payload?.data || payload || {} }

const UNKNOWN = '—'
const ROLE_ORDER = ['user', 'technician', 'manager', 'admin']
const WEEKDAYS = {
  vi: ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'],
  en: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
}
// BE giới hạn limit ≤ 100 cho /admin/scans và /admin/users; 20 trang (2000 dòng) đủ cho dữ liệu đồ án.
const PAGE_SIZE = 100
const MAX_PAGES = 20

// created_at từ BE là UTC không kèm timezone ("2026-10-04T03:12:00") — tự gắn Z rồi quy về ngày local (giờ VN).
function toLocalDate(value) {
  const text = String(value || '')
  return new Date(/[zZ]|[+-]\d{2}:\d{2}$/.test(text) ? text : `${text}Z`)
}

// 00:00 local của ngày offsetDays trước hôm nay (offsetDays=6 → mốc bắt đầu chuỗi 7 ngày).
function startOfLocalDay(offsetDays) {
  const date = new Date()
  date.setHours(0, 0, 0, 0)
  date.setDate(date.getDate() - offsetDays)
  return date
}

// Phân trang thủ công vì BE trả list thuần (không có total).
async function fetchAllPages(request) {
  const rows = []
  for (let page = 0; page < MAX_PAGES; page += 1) {
    const batch = await request(page * PAGE_SIZE)
    if (!Array.isArray(batch)) return rows
    rows.push(...batch)
    if (batch.length < PAGE_SIZE) break
  }
  return rows
}

export default function SystemStatsPage() {
  const { t, isEn } = useLanguage()
  const [stats, setStats] = useState({})
  // null = đang tải; object = đủ 7 mốc ngày cho biểu đồ.
  const [scanChart, setScanChart] = useState(null)
  // null = đang tải; [] = API OK nhưng không có người dùng.
  const [roles, setRoles] = useState(null)
  // null = đang tải; [] = API OK nhưng không có version active.
  const [modelVersions, setModelVersions] = useState(null)
  const [message, setMessage] = useState('')

  useEffect(() => {
    let active = true
    const fail = (error) => { if (active) setMessage((current) => current || getApiError(error)) }

    adminStatsApi.overview()
      .then((payload) => { if (active) setStats(unwrapOverview(payload)) })
      .catch(fail)

    // Widget "Lượt quét 7 ngày": gộp từ GET /admin/scans trong cửa sổ [from, to).
    const from = startOfLocalDay(6).toISOString()
    fetchAllPages((offset) => adminStatsApi.scans({ from, limit: PAGE_SIZE, offset }))
      .then((scans) => {
        if (!active) return
        const days = Array.from({ length: 7 }, (_, index) => startOfLocalDay(6 - index))
        const buckets = new Map(days.map((day) => [day.toDateString(), 0]))
        scans.forEach((scan) => {
          const key = toLocalDate(scan.created_at).toDateString()
          if (buckets.has(key)) buckets.set(key, buckets.get(key) + 1)
        })
        setScanChart({ days, values: days.map((day) => buckets.get(day.toDateString())) })
      })
      .catch(fail)

    // Widget "Người dùng theo vai trò": đếm client-side từ GET /admin/users.
    fetchAllPages((offset) => adminUsersApi.list({ limit: PAGE_SIZE, offset }))
      .then((users) => {
        if (!active) return
        const counts = new Map()
        users.forEach((user) => counts.set(user.role, (counts.get(user.role) || 0) + 1))
        setRoles(ROLE_ORDER.map((role) => ({ role, value: counts.get(role) || 0 })).filter((item) => item.value > 0))
      })
      .catch(fail)

    // Widget "Model đang chạy": các bundle đang active ở Production.
    systemHealthApi.activeModelVersions()
      .then((items) => { if (active) setModelVersions((Array.isArray(items) ? items : []).map((item) => item.version_name)) })
      .catch(() => { if (active) setModelVersions([]) })

    return () => { active = false }
  }, [])

  const diseases = stats.disease_counts || []
  const maxRole = Math.max(...(roles || []).map((item) => item.value), 1)
  const modelValue = modelVersions === null
    ? t('common.loading')
    : modelVersions.length === 1
      ? modelVersions[0]
      : modelVersions.length
        ? t('system.stat_model_multi', { count: modelVersions.length })
        : UNKNOWN

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader
        eyebrow={t('system.eyebrow')}
        title={t('system.title')}
        description={t('system.desc')}
      />
      {message && <p className="mb-5 rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">{t(message)}</p>}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={Users} label={t('system.stat_users')} value={stats.total_users || 0} />
        <StatCard icon={ScanLine} label={t('system.stat_scans')} value={stats.total_scans || 0} tone="blue" />
        <StatCard icon={Sprout} label={t('system.stat_farms')} value={stats.total_farms || 0} tone="amber" />
        <StatCard icon={Database} label={t('system.stat_model')} value={modelValue} tone="purple" />
      </div>
      <div className="mt-6 grid gap-6 xl:grid-cols-[1.2fr_.8fr]">
        <section className="card p-5 sm:p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-extrabold text-slate-900 dark:text-slate-50">{t('system.chart_7days')}</h2>
              <p className="mt-1 text-sm text-slate-400 dark:text-slate-500">{t('system.chart_sub')}</p>
            </div>
            <Activity className="text-leaf-600 dark:text-leaf-400" size={21} />
          </div>
          {scanChart ? (
            <MiniBarChart values={scanChart.values} labels={scanChart.days.map((day) => (isEn ? WEEKDAYS.en : WEEKDAYS.vi)[day.getDay()])} />
          ) : (
            <p className="flex h-52 items-center justify-center text-sm text-slate-400 dark:text-slate-500">{t('common.loading')}</p>
          )}
        </section>
        <section className="card p-5 sm:p-6">
          <h2 className="text-lg font-extrabold text-slate-900 dark:text-slate-50">{t('system.role_breakdown')}</h2>
          <div className="mt-7 space-y-5">
            {roles === null && <p className="text-sm text-slate-400 dark:text-slate-500">{t('common.loading')}</p>}
            {roles?.length === 0 && <p className="text-sm text-slate-400 dark:text-slate-500">{t('common.no_data')}</p>}
            {roles?.map((item) => {
              const value = item.value
              const roleKey = item.role
              const label = t(`roles.${roleKey}`) || roleKey
              return (
                <div key={roleKey}>
                  <div className="mb-2 flex justify-between text-sm">
                    <span className="font-semibold text-slate-600 dark:text-slate-300">{label}</span>
                    <strong className="text-slate-900 dark:text-slate-100">{value}</strong>
                  </div>
                  <div className="h-2.5 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                    <div className="h-full rounded-full bg-sky-500" style={{ width: `${(value / maxRole) * 100}%` }} />
                  </div>
                </div>
              )
            })}
          </div>
        </section>
      </div>
      <section className="card mt-6 p-5 sm:p-6">
        <h2 className="text-lg font-extrabold text-slate-900 dark:text-slate-50">{t('system.disease_breakdown')}</h2>
        <div className="mt-5 grid gap-4 sm:grid-cols-3">
          {diseases.map((item, index) => (
            <div key={item.label_key || item.name || item.label} className={`rounded-2xl p-5 ${index === 0 ? 'bg-emerald-50 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300' : index === 1 ? 'bg-amber-50 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300' : 'bg-violet-50 text-violet-800 dark:bg-violet-950/40 dark:text-violet-300'}`}>
              <p className="text-2xl font-black">{item.count ?? item.value}</p>
              <p className="mt-1 text-sm font-semibold">{item.label_key || item.name || item.label}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}