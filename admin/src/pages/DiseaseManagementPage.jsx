import { Edit3, Leaf, Plus, Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import ConfirmDialog from '../components/common/ConfirmDialog.jsx'
import CrudForm from '../components/common/CrudForm.jsx'
import DataTable from '../components/common/DataTable.jsx'
import Modal from '../components/common/Modal.jsx'
import PageHeader from '../components/common/PageHeader.jsx'
import StatusBadge from '../components/common/StatusBadge.jsx'
import { useLanguage } from '../contexts/LanguageContext.jsx'
import { adminDiseasesApi } from '../services/diseases.js'
import { getApiError } from '../services/client.js'

function normalizeDisease(item) {
  const labelKey = item.label_key || item.labelKey || ''
  const rawPlant = item.plant || (labelKey ? labelKey.split('_')[0] : 'Cây trồng')
  const plant = rawPlant.charAt(0).toUpperCase() + rawPlant.slice(1)
  return {
    ...item,
    id: item.id || labelKey,
    labelKey,
    name: item.disease_name || item.name,
    plant,
    severity: item.severity_level || item.severity || 'medium',
    symptoms: item.description || item.symptoms || '',
    treatment: item.treatment || '',
  }
}

export default function DiseaseManagementPage() {
  const { t } = useLanguage()
  const [diseases, setDiseases] = useState([])
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')
  const [editing, setEditing] = useState(null)
  const [formOpen, setFormOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(null)
  const [confirmingDelete, setConfirmingDelete] = useState(false)

  useEffect(() => {
    let active = true
    setLoading(true)
    adminDiseasesApi.list()
      .then((payload) => { if (active) setDiseases(Array.isArray(payload) ? payload.map(normalizeDisease) : []) })
      .catch((error) => { if (active) setMessage(getApiError(error, t('diseases.err_load'))) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  const diseaseFields = [
    { name: 'label_key', label: t('diseases.field_label_key'), placeholder: t('diseases.ph_label_key'), hint: t('diseases.hint_label_key'), disabled: Boolean(editing) },
    { name: 'disease_name', label: t('diseases.field_name'), placeholder: t('diseases.ph_disease_name') },
    { name: 'severity_level', label: t('diseases.field_severity'), type: 'select', options: [{ value: 'low', label: t('common.low') }, { value: 'medium', label: t('common.medium') }, { value: 'high', label: t('common.high') }] },
    { name: 'description', label: t('diseases.field_symptoms'), type: 'textarea', rows: 3, fullWidth: true, required: false },
    { name: 'treatment', label: t('diseases.field_treatment'), type: 'textarea', rows: 4, fullWidth: true, required: false },
  ]

  function openCreate() { setEditing(null); setMessage(''); setFormOpen(true) }
  function openEdit(item) { setEditing(item); setMessage(''); setFormOpen(true) }

  async function saveDisease(values) {
    // BE dùng label_key làm khóa trong URL nên form tạo mới vẫn cho nhập; form sửa khóa label.
    const labelKey = editing ? editing.label_key : values.label_key.trim()
    const payload = {
      disease_name: values.disease_name.trim(),
      description: values.description?.trim() ? values.description.trim() : null,
      treatment: values.treatment?.trim() ? values.treatment.trim() : null,
      severity_level: values.severity_level,
    }
    setSaving(true)
    try {
      const saved = editing
        ? await adminDiseasesApi.update(labelKey, payload)
        : await adminDiseasesApi.create({ label_key: labelKey, ...payload })
      setDiseases((items) => editing
        ? items.map((item) => item.label_key === labelKey ? saved : item)
        : [saved, ...items])
      setFormOpen(false)
      setEditing(null)
      setMessage(t(editing ? 'diseases.msg_updated' : 'diseases.msg_created', { name: saved.disease_name }))
    } catch (error) {
      setMessage(getApiError(error, t(editing ? 'diseases.err_update' : 'diseases.err_create')))
    } finally {
      setSaving(false)
    }
  }

  async function deleteDisease() {
    if (!deleting || confirmingDelete) return
    setConfirmingDelete(true)
    try {
      await adminDiseasesApi.remove(deleting.label_key || deleting.labelKey)
      setDiseases((items) => items.filter((item) => item.label_key !== deleting.label_key))
      setDeleting(null)
      setMessage(t('diseases.msg_deleted', { name: deleting.disease_name }))
    } catch (error) {
      setMessage(getApiError(error, t('diseases.err_delete')))
    } finally {
      setConfirmingDelete(false)
    }
  }
  const columns = [
    { key: 'disease_name', label: t('diseases.col_name'), sortable: true, render: (value, row) => <div className="flex items-center gap-3"><span className="grid h-9 w-9 place-items-center rounded-xl bg-leaf-50 text-leaf-700 dark:bg-leaf-900/40 dark:text-leaf-300"><Leaf size={17} /></span><div><p className="font-bold text-slate-800 dark:text-slate-100">{value ? t(value) : '—'}</p><p className="mt-0.5 text-xs text-slate-400 dark:text-slate-500">{row.label_key}</p></div></div> },
    { key: 'severity_level', label: t('diseases.col_severity'), render: (value) => <StatusBadge value={value} /> },
    { key: 'description', label: t('diseases.col_symptoms'), render: (value) => <p className="max-w-xs truncate">{value ? t(value) : '—'}</p> },
  ]

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader eyebrow={t('diseases.eyebrow')} title={t('diseases.title')} description={t('diseases.desc')} action={<button className="btn-primary" onClick={openCreate}><Plus size={18} /> {t('diseases.add_btn')}</button>} />
      {loading && <p className="mb-5 text-sm text-slate-500 dark:text-slate-400">{t('common.loading')}</p>}
      {message && <p className="mb-5 rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">{t(message)}</p>}
      <DataTable columns={columns} data={diseases} searchPlaceholder={t('diseases.search_placeholder')} actions={(row) => <span className="inline-flex gap-1"><button onClick={() => openEdit(row)} className="rounded-lg p-2 text-slate-400 hover:bg-leaf-50 hover:text-leaf-700 dark:hover:bg-slate-800 dark:hover:text-leaf-300" aria-label={t('common.edit')}><Edit3 size={17} /></button><button onClick={() => setDeleting(row)} className="rounded-lg p-2 text-slate-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/40 dark:hover:text-rose-400" aria-label={t('common.delete')}><Trash2 size={17} /></button></span>} />
      <Modal open={formOpen} onClose={() => setFormOpen(false)} title={editing ? t('diseases.modal_edit') : t('diseases.modal_create')} description={t('diseases.modal_desc')} size="xl">
        <CrudForm
          fields={diseaseFields}
          defaultValues={editing || { severity_level: 'medium' }}
          onSubmit={saveDisease}
          onCancel={() => setFormOpen(false)}
          submitLabel={t('diseases.save_btn')}
          loading={saving}
        />
      </Modal>
      <ConfirmDialog open={Boolean(deleting)} onClose={() => setDeleting(null)} onConfirm={deleteDisease} message={deleting ? t('common.confirm_delete_msg', { name: deleting.disease_name }) : ''} />
    </div>
  )
}

