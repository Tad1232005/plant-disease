import { CheckCircle2, Database, Plus, Rocket } from 'lucide-react'
import { useEffect, useState } from 'react'
import CrudForm from '../components/common/CrudForm.jsx'
import DataTable from '../components/common/DataTable.jsx'
import Modal from '../components/common/Modal.jsx'
import PageHeader from '../components/common/PageHeader.jsx'
import StatCard from '../components/common/StatCard.jsx'
import StatusBadge from '../components/common/StatusBadge.jsx'
import { useLanguage } from '../contexts/LanguageContext.jsx'
import { getApiError } from '../services/client.js'
import { modelVersionsApi } from '../services/modelVersions.js'

const UNKNOWN = '—'

/** Backend trả is_active/is_enabled; map sang nhãn mà StatusBadge đã có sẵn màu. */
function toStatus(item) {
  if (item.is_active) return 'production'
  return item.is_enabled === false ? 'inactive' : 'staging'
}

function formatDateTime(value) {
  const date = new Date(value)
  if (!value || Number.isNaN(date.getTime())) return UNKNOWN
  return new Intl.DateTimeFormat('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }).format(date)
}

/** Chuẩn hoá ModelVersionListItem của backend thành dòng hiển thị của DataTable. */
function toRow(item) {
  return {
    id: item.id,
    version_name: item.version_name,
    model_type: item.model_type,
    temperature: typeof item.temperature === 'number' ? item.temperature : null,
    accuracy: typeof item.accuracy === 'number' ? item.accuracy : null,
    status: toStatus(item),
    is_active: Boolean(item.is_active),
    created_at: item.created_at || '',
  }
}

export default function ModelVersionsPage() {
  const { t } = useLanguage()
  const [versions, setVersions] = useState([])
  const [loading, setLoading] = useState(true)
  const [reloadKey, setReloadKey] = useState(0)
  const [formOpen, setFormOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    let active = true
    setLoading(true)
    modelVersionsApi.list()
      .then((payload) => { if (active) setVersions(Array.isArray(payload) ? payload.map(toRow) : []) })
      .catch((error) => { if (active) { setVersions([]); setMessage(getApiError(error, t('models.err_load'))) } })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [reloadKey])

  function reload() { setReloadKey((value) => value + 1) }

  // Backend đọc manifest.json trên server; accuracy/macro_f1/ece là metadata tuỳ chọn.
  const fields = [
    { name: 'manifest_path', label: t('models.field_manifest'), placeholder: t('models.ph_manifest'), hint: t('models.hint_manifest'), fullWidth: true },
    { name: 'accuracy', label: t('models.field_accuracy'), type: 'number', min: 0, max: 1, step: 0.0001, required: false, hint: t('models.hint_metric') },
    { name: 'macro_f1', label: t('models.field_macro_f1'), type: 'number', min: 0, max: 1, step: 0.0001, required: false, hint: t('models.hint_metric') },
    { name: 'ece', label: t('models.field_ece'), type: 'number', min: 0, max: 1, step: 0.0001, required: false, hint: t('models.hint_metric') },
    { name: 'metrics_path', label: t('models.field_metrics_path'), placeholder: t('models.ph_metrics_path'), required: false, fullWidth: true },
  ]

  async function registerVersion(values) {
    setSaving(true)
    setMessage('')
    try {
      await modelVersionsApi.register({
        manifest_path: values.manifest_path.trim(),
        accuracy: values.accuracy ?? null,
        macro_f1: values.macro_f1 ?? null,
        ece: values.ece ?? null,
        metrics_path: values.metrics_path?.trim() ? values.metrics_path.trim() : null,
      })
      setFormOpen(false)
      setMessage(t('models.msg_registered'))
      reload()
    } catch (error) {
      setMessage(getApiError(error, t('models.err_register')))
    } finally {
      setSaving(false)
    }
  }

  async function activate(row) {
    setSaving(true)
    setMessage('')
    try {
      const saved = await modelVersionsApi.activate(row.id)
      const replaced = saved?.deactivated_version_name
      setMessage(replaced
        ? `Đã kích hoạt ${row.version_name} cho ${row.model_type}; version cũ ${replaced} chuyển sang inactive.`
        : `Đã kích hoạt ${row.version_name} cho ${row.model_type}.`)
      reload()
    } catch (error) {
      setMessage(getApiError(error, t('models.err_activate')))
    } finally {
      setSaving(false)
    }
  }

  const activeVersions = versions.filter((item) => item.is_active)
  const activeAccuracies = activeVersions.map((item) => item.accuracy).filter((value) => value !== null)
  const bestAccuracy = activeAccuracies.length ? `${(Math.max(...activeAccuracies) * 100).toFixed(1)}%` : UNKNOWN

  const columns = [
    {
      key: 'version_name',
      label: t('models.col_version'),
      sortable: true,
      render: (value, row) => (
        <div>
          <p className="font-black text-slate-800 dark:text-slate-100">{value}</p>
          <p className="mt-0.5 text-xs text-slate-400 dark:text-slate-500">#{row.id}</p>
        </div>
      ),
    },
    {
      key: 'model_type',
      label: t('models.col_arch'),
      sortable: true,
      render: (value) => <code className="rounded-lg bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">{value}</code>,
    },
    {
      key: 'accuracy',
      label: t('models.col_acc'),
      sortable: true,
      render: (value) => (value === null
        ? <span className="text-slate-400 dark:text-slate-500">{UNKNOWN}</span>
        : <span className="font-extrabold text-leaf-700 dark:text-leaf-400">{(value * 100).toFixed(1)}%</span>),
    },
    {
      key: 'temperature',
      label: t('models.col_temperature'),
      render: (value) => (value === null
        ? UNKNOWN
        : value === 1
          ? <span className="text-slate-400 dark:text-slate-500">{t('models.calib_none')}</span>
          : value.toFixed(3)),
    },
    { key: 'status', label: t('models.col_status'), render: (value) => <StatusBadge value={value}>{t(`models.status_${value}`)}</StatusBadge> },
    { key: 'created_at', label: t('models.col_updated'), render: (value) => formatDateTime(value) },
  ]

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader
        eyebrow={t('models.eyebrow')}
        title={t('models.title')}
        description={t('models.desc')}
        action={<button className="btn-primary" onClick={() => { setMessage(''); setFormOpen(true) }}><Plus size={18} /> {t('models.add_btn')}</button>}
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <StatCard icon={Database} label={t('models.stat_total')} value={loading ? UNKNOWN : versions.length} />
        <StatCard icon={Rocket} label={t('models.stat_production')} value={loading ? UNKNOWN : activeVersions.length} tone="blue" />
        <StatCard icon={CheckCircle2} label={t('models.stat_accuracy')} value={loading ? UNKNOWN : bestAccuracy} tone="amber" />
      </div>
      {loading && <p className="mb-5 text-sm text-slate-500 dark:text-slate-400">{t('common.loading')}</p>}
      {message && <p className="mb-5 rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">{t(message)}</p>}

      <DataTable
        columns={columns}
        data={versions}
        searchPlaceholder={t('models.search_placeholder')}
        emptyDescription={t('models.empty_desc')}
        actions={(row) => (
          <button
            type="button"
            disabled={row.is_active || saving}
            onClick={() => activate(row)}
            className="rounded-lg p-2 text-slate-400 hover:bg-leaf-50 hover:text-leaf-700 disabled:opacity-30 dark:hover:bg-slate-800 dark:hover:text-leaf-300"
            aria-label={t('models.activate_prod')}
            title={row.is_active ? t('models.already_active') : t('models.activate_prod')}
          >
            <Rocket size={17} />
          </button>
        )}
      />

      <Modal open={formOpen} onClose={() => setFormOpen(false)} title={t('models.modal_create')} description={t('models.modal_desc')} size="xl">
        <CrudForm fields={fields} onSubmit={registerVersion} onCancel={() => setFormOpen(false)} submitLabel={t('models.save_btn')} loading={saving} />
      </Modal>
    </div>
  )
}

