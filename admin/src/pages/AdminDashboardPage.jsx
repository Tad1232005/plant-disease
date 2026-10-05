import { Activity, Database, Leaf, ScanLine, Server, ShieldCheck, Sprout, Users } from 'lucide-react'
import { useEffect, useState } from 'react'
import StatCard from '../components/common/StatCard.jsx'
import StatusBadge from '../components/common/StatusBadge.jsx'
import { useLanguage } from '../contexts/LanguageContext.jsx'
import { API_ORIGIN } from '../services/client.js'
import { adminStatsApi } from '../services/stats.js'
import { DB_TABLE_COUNT, systemHealthApi } from '../services/systemHealth.js'

const UNKNOWN = '—'

export default function AdminDashboardPage() {
  const { t } = useLanguage()
  const [overview, setOverview] = useState(null)
  // null = đang kiểm tra, true = OK, false = lỗi (BE tắt / DB chưa sẵn sàng / không đọc được policy).
  const [health, setHealth] = useState({ backend: null, database: null, model: null })
  // null = chưa lấy được danh sách version, [] = API OK nhưng không có version active.
  const [modelVersions, setModelVersions] = useState(null)
  const [recentInvalid, setRecentInvalid] = useState([])

  useEffect(() => {
    let active = true
    const update = (key, value) => { if (active) setHealth((current) => ({ ...current, [key]: value })) }

    adminStatsApi.overview()
      .then((payload) => { if (active) setOverview(payload?.stats || payload?.data || payload || null) })
      .catch(() => { if (active) setOverview(null) })
    adminStatsApi.recentInvalid()
      .then((items) => { if (active && Array.isArray(items)) setRecentInvalid(items) })
      .catch(() => {})
    systemHealthApi.live().then((ok) => update('backend', ok))
    systemHealthApi.ready().then((ok) => update('database', ok))
    systemHealthApi.capabilities().then((ok) => update('model', ok))
    systemHealthApi.activeModelVersions()
      .then((items) => { if (active) setModelVersions((Array.isArray(items) ? items : []).map((item) => item.version_name)) })
      .catch(() => { if (active) setModelVersions(null) })

    return () => { active = false }
  }, [])

  const pendingStatus = (value) => (value === null ? 'pending' : value ? 'active' : 'inactive')
  const statusLabel = (status, offlineLabel) => {
    if (status === 'pending') return t('dashboard.service_checking')
    return status === 'active' ? t('dashboard.service_active') : (offlineLabel || t('dashboard.service_inactive'))
  }

  const databaseDetail = health.database === null
    ? t('dashboard.service_checking')
    : health.database
      ? t('dashboard.service_tables', { count: DB_TABLE_COUNT })
      : t('dashboard.service_db_error')

  const modelDetail = health.model === null
    ? t('dashboard.service_checking')
    : health.model === false
      ? t('dashboard.service_model_error')
      : modelVersions?.length
        ? modelVersions.join(' · ')
        : t('dashboard.service_model_ready')

  const services = [
    { key: 'backend', name: t('dashboard.service_backend'), detail: API_ORIGIN, status: pendingStatus(health.backend) },
    { key: 'database', name: t('dashboard.service_db'), detail: databaseDetail, status: pendingStatus(health.database), offlineLabel: t('dashboard.service_not_ready') },
    { key: 'model', name: t('dashboard.service_model'), detail: modelDetail, status: pendingStatus(health.model), offlineLabel: t('dashboard.service_not_ready') },
  ]

  return (
    <div className="mx-auto max-w-7xl">
      <div className="mb-7">
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-leaf-600 dark:text-leaf-400">{t('dashboard.eyebrow')}</p>
        <h1 className="mt-2 text-3xl font-black tracking-tight text-slate-900 dark:text-slate-50">{t('dashboard.title')}</h1>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          {t('dashboard.desc')}
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={Users} label={t('dashboard.stat_users')} value={overview?.total_users ?? UNKNOWN} />
        <StatCard icon={ScanLine} label={t('dashboard.stat_scans')} value={overview?.total_scans ?? UNKNOWN} tone="blue" />
        <StatCard icon={Sprout} label={t('dashboard.stat_farms')} value={overview?.total_farms ?? UNKNOWN} tone="amber" />
        <StatCard icon={Database} label={t('dashboard.stat_model')} value={modelVersions?.length ?? UNKNOWN} tone="purple" />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1.05fr_.95fr]">
        <section className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-extrabold text-slate-900 dark:text-slate-50">{t('dashboard.service_status')}</h2>
              <p className="mt-1 text-sm text-slate-400 dark:text-slate-500">{t('dashboard.service_sub')}</p>
            </div>
            <span className="grid h-10 w-10 place-items-center rounded-xl bg-leaf-50 text-leaf-700 dark:bg-leaf-900/40 dark:text-leaf-300">
              <Activity size={20} />
            </span>
          </div>
          <div className="mt-5 divide-y divide-slate-100 dark:divide-slate-800">
            {services.map((service) => (
              <div key={service.key} className="flex items-center justify-between gap-3 py-4">
                <div className="flex items-center gap-3">
                  <span className="grid h-10 w-10 place-items-center rounded-xl bg-slate-50 text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                    <Server size={18} />
                  </span>
                  <div>
                    <p className="text-sm font-bold text-slate-800 dark:text-slate-200">{service.name}</p>
                    <p className="mt-0.5 text-xs text-slate-400 dark:text-slate-500">{service.detail}</p>
                  </div>
                </div>
                <StatusBadge value={service.status}>{statusLabel(service.status, service.offlineLabel)}</StatusBadge>
              </div>
            ))}
          </div>
        </section>

        <section className="overflow-hidden rounded-3xl bg-leaf-900 p-6 text-white shadow-soft">
          <span className="grid h-12 w-12 place-items-center rounded-2xl bg-white/10 text-leaf-200"><ShieldCheck size={23} /></span>
          <h2 className="mt-5 text-2xl font-black">{t('dashboard.banner_title')}</h2>
          <p className="mt-3 text-sm leading-7 text-leaf-100/65">{t('dashboard.banner_desc')}</p>
          <div className="mt-6 grid grid-cols-2 gap-3">
            <div className="rounded-2xl bg-white/10 p-4">
              <Leaf size={18} className="text-leaf-200" />
              <p className="mt-3 text-2xl font-black">04</p>
              <p className="mt-1 text-xs text-leaf-100/60">{t('dashboard.banner_diseases')}</p>
            </div>
            <div className="rounded-2xl bg-white/10 p-4">
              <Activity size={18} className="text-leaf-200" />
              <p className="mt-3 text-2xl font-black">99.9%</p>
              <p className="mt-1 text-xs text-leaf-100/60">{t('dashboard.banner_uptime')}</p>
            </div>
          </div>
        </section>
      </div>

      {recentInvalid?.length > 0 && (
        <section className="card mt-6 p-6">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-4">
            <div>
              <h2 className="text-lg font-black text-slate-800 dark:text-slate-100">
                {t('dashboard.recent_invalid_title') || 'Ca quét ngoài miền dữ liệu gần đây (OOD / Rejected)'}
              </h2>
              <p className="text-xs text-slate-400">Các ca quét bị thuật toán ensemble từ chối hoặc phát hiện bất thường</p>
            </div>
            <StatusBadge value="inactive">{recentInvalid.length} ca cảnh báo</StatusBadge>
          </div>
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {recentInvalid.slice(0, 5).map((scan) => (
              <div key={scan.id} className="flex items-center justify-between py-3.5">
                <div>
                  <p className="text-sm font-bold text-slate-800 dark:text-slate-200">
                    Ca quét #{scan.id} • {scan.rejection_reason || 'Out of distribution'}
                  </p>
                  <p className="text-xs text-slate-400">
                    Mô hình: {scan.model_version || 'Ensemble'} • Độ bất định (OOD): {((scan.ood_score || 0) * 100).toFixed(1)}%
                  </p>
                </div>
                <span className="rounded-lg bg-amber-50 dark:bg-amber-950/40 px-2.5 py-1 text-xs font-semibold text-amber-700 dark:text-amber-300">
                  {scan.validation_status}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}

