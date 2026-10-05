import { Edit3, MapPin, Plus, Sprout, Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import ConfirmDialog from '../components/common/ConfirmDialog.jsx'
import CrudForm from '../components/common/CrudForm.jsx'
import DataTable from '../components/common/DataTable.jsx'
import Modal from '../components/common/Modal.jsx'
import PageHeader from '../components/common/PageHeader.jsx'
import StatCard from '../components/common/StatCard.jsx'
import StatusBadge from '../components/common/StatusBadge.jsx'
import { useLanguage } from '../contexts/LanguageContext.jsx'
import { initialFarms } from '../data/demoData.js'
import { adminFarmsApi } from '../services/farms.js'
import { loadCollection, saveCollection } from '../utils/storage.js'

// Key riêng của admin: tách khỏi localStorage app người dùng và không nạp dữ liệu seed cũ.
const STORAGE_KEY = 'plantcare_admin_farms'

function normalizeFarm(farm) {
  return {
    ...farm,
    location: farm.location_text || farm.location || 'Chưa cập nhật',
    crop: farm.crop || 'Cà chua / Đa canh',
    area: farm.area || 1.5,
    status: farm.status || 'healthy',
    lastScan: farm.lastScan || 'Hôm nay',
  }
}

export default function FarmsPage() {
  const { t } = useLanguage()
  const [farms, setFarms] = useState(() => loadCollection(STORAGE_KEY, []))
  const [farms, setFarms] = useState(() => loadCollection(STORAGE_KEY, initialFarms).map(normalizeFarm))
  const [editing, setEditing] = useState(null)
  const [formOpen, setFormOpen] = useState(false)
  const [deleting, setDeleting] = useState(null)

  useEffect(() => {
    let active = true
    adminFarmsApi.list()
      .then((data) => {
        if (!active || !Array.isArray(data)) return
        if (data.length > 0) {
          const mapped = data.map(normalizeFarm)
          setFarms(mapped)
          saveCollection(STORAGE_KEY, mapped)
        }
      })
      .catch(() => {})
    return () => { active = false }
  }, [])

  useEffect(() => saveCollection(STORAGE_KEY, farms), [farms])

  const farmFields = [
    { name: 'name', label: t('farms.field_name'), placeholder: 'Ví dụ: Vườn cà chua A1', fullWidth: true },
    { name: 'location', label: t('farms.field_location'), placeholder: 'Tỉnh/thành phố' },
    { name: 'crop', label: t('farms.field_crop'), placeholder: 'Cà chua, khoai tây...' },
    { name: 'area', label: t('farms.field_area'), type: 'number', min: 0.1, step: 0.1 },
    { name: 'status', label: t('farms.field_status'), type: 'select', options: [
      { value: 'healthy', label: t('common.healthy') }, { value: 'attention', label: t('common.attention') }, { value: 'risk', label: t('common.risk') },
    ] },
  ]

  function openCreate() { setEditing(null); setFormOpen(true) }
  function openEdit(farm) { setEditing(farm); setFormOpen(true) }

  async function saveFarm(values) {
    if (editing) {
      try {
        const res = await adminFarmsApi.update(editing.id, { name: values.name, location_text: values.location })
        const updated = normalizeFarm({ ...editing, ...values, ...res })
        setFarms((items) => items.map((item) => item.id === editing.id ? updated : item))
      } catch {
        setFarms((items) => items.map((item) => item.id === editing.id ? { ...item, ...values } : item))
      }
    } else {
      try {
        const res = await adminFarmsApi.create({ name: values.name, location_text: values.location })
        const created = normalizeFarm({ ...values, ...res, lastScan: t('farms.not_scanned') })
        setFarms((items) => [created, ...items])
      } catch {
        setFarms((items) => [{ ...values, id: Date.now(), lastScan: t('farms.not_scanned') }, ...items])
      }
    }
    setFormOpen(false)
  }

  async function deleteFarm() {
    if (!deleting) return
    try {
      await adminFarmsApi.remove(deleting.id)
    } catch {}
    setFarms((items) => items.filter((item) => item.id !== deleting.id))
    setDeleting(null)
  }

  const columns = [
    { key: 'name', label: t('farms.col_name'), sortable: true, render: (value, row) => <div><p className="font-bold text-slate-800 dark:text-slate-100">{value}</p><p className="mt-1 inline-flex items-center gap-1 text-xs text-slate-400 dark:text-slate-500"><MapPin size={12} />{row.location}</p></div> },
    { key: 'crop', label: t('farms.col_crop'), sortable: true },
    { key: 'area', label: t('farms.col_area'), sortable: true, render: (value) => `${value} ha` },
    { key: 'status', label: t('farms.col_status'), render: (value) => <StatusBadge value={value} /> },
    { key: 'lastScan', label: t('farms.col_last_scan'), sortable: true },
  ]

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader
        eyebrow={t('farms.eyebrow')}
        title={t('farms.title')}
        description={t('farms.desc')}
        action={<button className="btn-primary" onClick={openCreate}><Plus size={18} /> {t('farms.add_btn')}</button>}
      />
      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <StatCard icon={Sprout} label={t('farms.stat_total')} value={String(farms.length).padStart(2, '0')} tone="green" />
        <StatCard icon={MapPin} label={t('farms.stat_area')} value={`${farms.reduce((sum, item) => sum + Number(item.area), 0).toFixed(1)} ha`} tone="blue" />
        <StatCard icon={Sprout} label={t('farms.stat_healthy')} value={farms.filter((item) => item.status === 'healthy').length} tone="amber" />
      </div>
      <DataTable columns={columns} data={farms} searchPlaceholder={t('farms.search_placeholder')} actions={(row) => (
        <span className="inline-flex gap-1">
          <button onClick={() => openEdit(row)} className="rounded-lg p-2 text-slate-400 hover:bg-leaf-50 hover:text-leaf-700 dark:hover:bg-slate-800 dark:hover:text-leaf-300" aria-label={t('common.edit')}><Edit3 size={17} /></button>
          <button onClick={() => setDeleting(row)} className="rounded-lg p-2 text-slate-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/40 dark:hover:text-rose-400" aria-label={t('common.delete')}><Trash2 size={17} /></button>
        </span>
      )} />
      <Modal open={formOpen} onClose={() => setFormOpen(false)} title={editing ? t('farms.modal_edit') : t('farms.modal_create')} description={t('farms.modal_desc')}>
        <CrudForm fields={farmFields} defaultValues={editing || { status: 'healthy' }} onSubmit={saveFarm} onCancel={() => setFormOpen(false)} submitLabel={editing ? t('farms.save_edit') : t('farms.save_create')} />
      </Modal>
      <ConfirmDialog open={Boolean(deleting)} onClose={() => setDeleting(null)} onConfirm={deleteFarm} message={deleting ? t('common.confirm_delete_msg', { name: deleting.name }) : ''} />
    </div>
  )
}
