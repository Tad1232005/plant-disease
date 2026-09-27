import { Edit3, Leaf, Plus, Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import ConfirmDialog from '../components/common/ConfirmDialog.jsx'
import CrudForm from '../components/common/CrudForm.jsx'
import DataTable from '../components/common/DataTable.jsx'
import Modal from '../components/common/Modal.jsx'
import PageHeader from '../components/common/PageHeader.jsx'
import StatusBadge from '../components/common/StatusBadge.jsx'
import { useLanguage } from '../contexts/LanguageContext.jsx'
import { initialDiseases } from '../data/demoData.js'
import { loadCollection, saveCollection } from '../utils/storage.js'

const STORAGE_KEY = 'plantcare_diseases'

export default function DiseaseManagementPage() {
  const { t } = useLanguage()
  const [diseases, setDiseases] = useState(() => loadCollection(STORAGE_KEY, initialDiseases))
  const [editing, setEditing] = useState(null)
  const [formOpen, setFormOpen] = useState(false)
  const [deleting, setDeleting] = useState(null)

  const diseaseFields = [
    { name: 'labelKey', label: t('diseases.field_label_key'), placeholder: 'tomato_late_blight', hint: 'Khớp với nhãn classes.json của model' },
    { name: 'name', label: t('diseases.field_name'), placeholder: 'Mốc sương cà chua' },
    { name: 'plant', label: t('diseases.field_plant'), placeholder: 'Cà chua' },
    { name: 'severity', label: t('diseases.field_severity'), type: 'select', options: [{ value: 'low', label: t('common.low') }, { value: 'medium', label: t('common.medium') }, { value: 'high', label: t('common.high') }] },
    { name: 'symptoms', label: t('diseases.field_symptoms'), type: 'textarea', rows: 3, fullWidth: true },
    { name: 'treatment', label: t('diseases.field_treatment'), type: 'textarea', rows: 4, fullWidth: true },
  ]

  useEffect(() => saveCollection(STORAGE_KEY, diseases), [diseases])
  function openCreate() { setEditing(null); setFormOpen(true) }
  function openEdit(item) { setEditing(item); setFormOpen(true) }
  function saveDisease(values) {
    if (editing) setDiseases((items) => items.map((item) => item.id === editing.id ? { ...item, ...values } : item))
    else setDiseases((items) => [{ ...values, id: Date.now() }, ...items])
    setFormOpen(false)
  }
  function deleteDisease() { setDiseases((items) => items.filter((item) => item.id !== deleting.id)); setDeleting(null) }

  const columns = [
    { key: 'name', label: t('diseases.col_name'), sortable: true, render: (value, row) => <div className="flex items-center gap-3"><span className="grid h-9 w-9 place-items-center rounded-xl bg-leaf-50 text-leaf-700 dark:bg-leaf-900/40 dark:text-leaf-300"><Leaf size={17} /></span><div><p className="font-bold text-slate-800 dark:text-slate-100">{value}</p><p className="mt-0.5 text-xs text-slate-400 dark:text-slate-500">{row.labelKey}</p></div></div> },
    { key: 'plant', label: t('diseases.col_crop'), sortable: true },
    { key: 'severity', label: t('diseases.col_severity'), render: (value) => <StatusBadge value={value} /> },
    { key: 'symptoms', label: t('diseases.col_symptoms'), render: (value) => <p className="max-w-xs truncate">{value}</p> },
  ]

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader eyebrow={t('diseases.eyebrow')} title={t('diseases.title')} description={t('diseases.desc')} action={<button className="btn-primary" onClick={openCreate}><Plus size={18} /> {t('diseases.add_btn')}</button>} />
      <DataTable columns={columns} data={diseases} searchPlaceholder={t('diseases.search_placeholder')} actions={(row) => <span className="inline-flex gap-1"><button onClick={() => openEdit(row)} className="rounded-lg p-2 text-slate-400 hover:bg-leaf-50 hover:text-leaf-700 dark:hover:bg-slate-800 dark:hover:text-leaf-300" aria-label={t('common.edit')}><Edit3 size={17} /></button><button onClick={() => setDeleting(row)} className="rounded-lg p-2 text-slate-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/40 dark:hover:text-rose-400" aria-label={t('common.delete')}><Trash2 size={17} /></button></span>} />
      <Modal open={formOpen} onClose={() => setFormOpen(false)} title={editing ? t('diseases.modal_edit') : t('diseases.modal_create')} description={t('diseases.modal_desc')} size="xl"><CrudForm fields={diseaseFields} defaultValues={editing || { severity: 'medium' }} onSubmit={saveDisease} onCancel={() => setFormOpen(false)} submitLabel={editing ? t('common.save') : t('common.save')} /></Modal>
      <ConfirmDialog open={Boolean(deleting)} onClose={() => setDeleting(null)} onConfirm={deleteDisease} message={deleting ? t('common.confirm_delete_msg', { name: deleting.name }) : ''} />
    </div>
  )
}

