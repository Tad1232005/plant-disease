import { CheckCircle2, Database, Edit3, Plus, Rocket } from 'lucide-react'
import { useEffect, useState } from 'react'
import CrudForm from '../components/common/CrudForm.jsx'
import DataTable from '../components/common/DataTable.jsx'
import Modal from '../components/common/Modal.jsx'
import PageHeader from '../components/common/PageHeader.jsx'
import StatCard from '../components/common/StatCard.jsx'
import StatusBadge from '../components/common/StatusBadge.jsx'
import { useLanguage } from '../contexts/LanguageContext.jsx'
import { initialModelVersions } from '../data/demoData.js'
import { modelVersionsApi } from '../services/modelVersions.js'
import { loadCollection, saveCollection } from '../utils/storage.js'

const STORAGE_KEY = 'plantcare_model_versions'
const fields = [
  { name: 'version', label: 'Phiên bản', placeholder: 'v2.2.0' },
  { name: 'backbone', label: 'Backbone', placeholder: 'EfficientNet-B0' },
  { name: 'accuracy', label: 'Accuracy (%)', type: 'number', min: 0, step: 0.1 },
  { name: 'classes', label: 'Số lớp', type: 'number', min: 1 },
  { name: 'calibration', label: 'Calibration', placeholder: 'Temperature 1.18' },
  { name: 'status', label: 'Trạng thái', type: 'select', options: [{ value: 'staging', label: 'Staging' }, { value: 'production', label: 'Production' }, { value: 'archived', label: 'Lưu trữ' }] },
]

function unwrapList(payload) {
  if (Array.isArray(payload)) return payload
  return payload?.items || payload?.models || payload?.data || []
}

export default function ModelVersionsPage() {
  const { t } = useLanguage()
  const [models, setModels] = useState(() => loadCollection(STORAGE_KEY, initialModelVersions))
  const [mode, setMode] = useState('loading')
  const [editing, setEditing] = useState(null)
  const [formOpen, setFormOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    let active = true
    modelVersionsApi.list().then((payload) => { if (active) { setModels(unwrapList(payload)); setMode('api') } }).catch(() => { if (active) setMode('demo') })
    return () => { active = false }
  }, [])
  useEffect(() => { if (mode !== 'loading') saveCollection(STORAGE_KEY, models) }, [mode, models])

  function openCreate() { setEditing(null); setMessage(''); setFormOpen(true) }
  function openEdit(row) { setEditing(row); setMessage(''); setFormOpen(true) }

  async function saveModel(values) {
    setSaving(true)
    try {
      let saved
      if (mode === 'api') saved = editing ? await modelVersionsApi.update(editing.id, values) : await modelVersionsApi.create(values)
      else saved = { ...editing, ...values, id: editing?.id || Date.now(), created_at: editing?.created_at || new Intl.DateTimeFormat('vi-VN').format(new Date()) }
      setModels((items) => editing ? items.map((item) => item.id === editing.id ? { ...item, ...saved } : item) : [saved, ...items])
      setFormOpen(false)
      setMessage('Đã lưu phiên bản mô hình.')
    } catch (error) { setMessage(error?.response?.data?.detail || 'Không thể lưu model version.') }
    finally { setSaving(false) }
  }

  async function activate(row) {
    setSaving(true)
    try {
      if (mode === 'api') await modelVersionsApi.update(row.id, { status: 'production' })
      setModels((items) => items.map((item) => ({ ...item, status: item.id === row.id ? 'production' : item.status === 'production' ? 'archived' : item.status })))
      setMessage(`Đã chuyển ${row.version} sang Production.`)
    } catch (error) { setMessage(error?.response?.data?.detail || 'Không thể kích hoạt phiên bản.') }
    finally { setSaving(false) }
  }

  const production = models.find((item) => item.status === 'production')
  const columns = [
    { key: 'version', label: t('models.col_version'), sortable: true, render: (value, row) => <div><p className="font-black text-slate-800 dark:text-slate-100">{value}</p><p className="mt-0.5 text-xs text-slate-400 dark:text-slate-500">{row.backbone}</p></div> },
    { key: 'accuracy', label: t('models.col_acc'), sortable: true, render: (value) => <span className="font-extrabold text-leaf-700 dark:text-leaf-400">{value}%</span> },
    { key: 'classes', label: t('models.col_classes'), sortable: true },
    { key: 'calibration', label: 'Calibration' },
    { key: 'status', label: t('models.col_status'), render: (value) => <StatusBadge value={value} /> },
  ]

  return (
    <div className="mx-auto max-w-7xl"><PageHeader eyebrow={t('models.eyebrow')} title={t('models.title')} description={t('models.desc')} action={<button className="btn-primary" onClick={openCreate}><Plus size={18} /> {t('models.add_btn')}</button>} /><div className="mb-6 grid gap-4 sm:grid-cols-3"><StatCard icon={Database} label={t('models.stat_total')} value={models.length} /><StatCard icon={Rocket} label={t('models.stat_production')} value={production?.version || '—'} tone="blue" /><StatCard icon={CheckCircle2} label={t('models.stat_accuracy')} value={production ? `${production.accuracy}%` : '—'} tone="amber" /></div>{message && <p className="mb-5 rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">{t(message)}</p>}<DataTable columns={columns} data={models} searchPlaceholder={t('models.search_placeholder')} actions={(row) => <span className="inline-flex gap-1"><button type="button" onClick={() => openEdit(row)} className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200" aria-label={t('common.edit')}><Edit3 size={17} /></button><button type="button" disabled={row.status === 'production' || saving} onClick={() => activate(row)} className="rounded-lg p-2 text-slate-400 hover:bg-leaf-50 hover:text-leaf-700 dark:hover:bg-slate-800 dark:hover:text-leaf-300 disabled:opacity-30" aria-label={t('models.activate_prod')}><Rocket size={17} /></button></span>} /><Modal open={formOpen} onClose={() => setFormOpen(false)} title={editing ? t('models.modal_edit') : t('models.modal_create')} description={t('models.modal_desc')} size="xl"><CrudForm fields={fields} defaultValues={editing || { status: 'staging', classes: 38 }} onSubmit={saveModel} onCancel={() => setFormOpen(false)} submitLabel={t('models.save_btn')} loading={saving} /></Modal></div>
  )
}
