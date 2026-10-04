import { Edit3, MapPin, Plus, Sprout, Trash2 } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import ConfirmDialog from '../../components/common/ConfirmDialog.jsx'
import CrudForm from '../../components/common/CrudForm.jsx'
import DataTable from '../../components/common/DataTable.jsx'
import Modal from '../../components/common/Modal.jsx'
import PageHeader from '../../components/common/PageHeader.jsx'
import StatCard from '../../components/common/StatCard.jsx'
import StatusBadge from '../../components/common/StatusBadge.jsx'
import { initialFarms } from '../../data/demoData.js'
import { loadCollection, saveCollection } from '../../utils/storage.js'
import { usePreferences } from '../../contexts/PreferencesContext.jsx'

const STORAGE_KEY = 'plantcare_farms'

export default function FarmsPage({ adminMode = false }) {
  const { language } = usePreferences()
  const copy = language === 'vi' ? {
    eyebrow: 'Tuần 2 • Farm Management', title: 'Quản lý trang trại', description: 'Manager thêm, sửa, xóa và theo dõi từng khu vực. Dữ liệu demo được lưu trên trình duyệt trong khi chờ API /farms.', add: 'Thêm khu vực', total: 'Tổng khu vực', areaTotal: 'Tổng diện tích', stable: 'Khu vực ổn định', area: 'Khu vực', crop: 'Cây trồng', areaSize: 'Diện tích', health: 'Sức khỏe', last: 'Lần quét cuối', search: 'Tìm theo tên, vị trí hoặc cây trồng...', edit: 'Sửa', remove: 'Xóa', update: 'Cập nhật khu vực', create: 'Thêm khu vực mới', formText: 'Thông tin này được dùng để nhóm lịch sử chẩn đoán theo vị trí.', save: 'Lưu cập nhật', createButton: 'Tạo khu vực', name: 'Tên khu vực', location: 'Vị trí', cropType: 'Loại cây', status: 'Trạng thái', healthy: 'Khỏe mạnh', attention: 'Cần chú ý', risk: 'Nguy cơ cao', never: 'Chưa quét',
  } : {
    eyebrow: 'Week 2 • Farm Management', title: 'Farm management', description: 'Managers add, edit, remove, and monitor their growing areas. Demo data is stored in the browser while waiting for /farms.', add: 'Add area', total: 'Total areas', areaTotal: 'Total area', stable: 'Stable areas', area: 'Area', crop: 'Crop', areaSize: 'Area size', health: 'Health', last: 'Last scan', search: 'Search by name, location, or crop...', edit: 'Edit', remove: 'Delete', update: 'Update area', create: 'Add a new area', formText: 'This information groups diagnosis history by location.', save: 'Save changes', createButton: 'Create area', name: 'Area name', location: 'Location', cropType: 'Crop type', status: 'Status', healthy: 'Healthy', attention: 'Needs attention', risk: 'High risk', never: 'No scans yet',
  }
  const [farms, setFarms] = useState(() => loadCollection(STORAGE_KEY, initialFarms))
  const [editing, setEditing] = useState(null)
  const [formOpen, setFormOpen] = useState(false)
  const [deleting, setDeleting] = useState(null)
  const farmFields = useMemo(() => [
    { name: 'name', label: copy.name, placeholder: language === 'vi' ? 'Ví dụ: Vườn cà chua A1' : 'Example: Tomato Farm A1', fullWidth: true },
    { name: 'location', label: copy.location, placeholder: language === 'vi' ? 'Tỉnh/thành phố' : 'Province/city' },
    { name: 'crop', label: copy.cropType, placeholder: language === 'vi' ? 'Cà chua, khoai tây...' : 'Tomato, potato...' },
    { name: 'area', label: `${copy.areaSize} (ha)`, type: 'number', min: 0.1, step: 0.1 },
    { name: 'status', label: copy.status, type: 'select', options: [
      { value: 'healthy', label: copy.healthy }, { value: 'attention', label: copy.attention }, { value: 'risk', label: copy.risk },
    ] },
  ], [copy, language])

  useEffect(() => saveCollection(STORAGE_KEY, farms), [farms])

  function openCreate() { setEditing(null); setFormOpen(true) }
  function openEdit(farm) { setEditing(farm); setFormOpen(true) }
  function saveFarm(values) {
    if (editing) {
      setFarms((items) => items.map((item) => item.id === editing.id ? { ...item, ...values } : item))
    } else {
      setFarms((items) => [{ ...values, id: Date.now(), lastScan: copy.never }, ...items])
    }
    setFormOpen(false)
  }
  function deleteFarm() { setFarms((items) => items.filter((item) => item.id !== deleting.id)); setDeleting(null) }

  const columns = [
    { key: 'name', label: copy.area, sortable: true, render: (value, row) => <div><p className="font-bold text-slate-800">{value}</p><p className="mt-1 inline-flex items-center gap-1 text-xs text-slate-400"><MapPin size={12} />{row.location}</p></div> },
    { key: 'crop', label: copy.crop, sortable: true },
    { key: 'area', label: copy.areaSize, sortable: true, render: (value) => `${value} ha` },
    { key: 'status', label: copy.health, render: (value) => <StatusBadge value={value} /> },
    { key: 'lastScan', label: copy.last, sortable: true },
  ]

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader
        eyebrow={adminMode ? (language === 'vi' ? 'Quản trị dữ liệu' : 'Data administration') : copy.eyebrow}
        title={adminMode ? (language === 'vi' ? 'Dữ liệu trang trại' : 'Farm data') : copy.title}
        description={copy.description}
        action={<button className="btn-primary" onClick={openCreate}><Plus size={18} />{copy.add}</button>}
      />
      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <StatCard icon={Sprout} label={copy.total} value={String(farms.length).padStart(2, '0')} tone="green" />
        <StatCard icon={MapPin} label={copy.areaTotal} value={`${farms.reduce((sum, item) => sum + Number(item.area), 0).toFixed(1)} ha`} tone="blue" />
        <StatCard icon={Sprout} label={copy.stable} value={farms.filter((item) => item.status === 'healthy').length} tone="amber" />
      </div>
      <DataTable columns={columns} data={farms} searchPlaceholder={copy.search} actions={(row) => (
        <span className="inline-flex gap-1">
          <button onClick={() => openEdit(row)} className="rounded-lg p-2 text-slate-400 hover:bg-leaf-50 hover:text-leaf-700" aria-label={copy.edit}><Edit3 size={17} /></button>
          <button onClick={() => setDeleting(row)} className="rounded-lg p-2 text-slate-400 hover:bg-rose-50 hover:text-rose-600" aria-label={copy.remove}><Trash2 size={17} /></button>
        </span>
      )} />
      <Modal open={formOpen} onClose={() => setFormOpen(false)} title={editing ? copy.update : copy.create} description={copy.formText}>
        <CrudForm fields={farmFields} defaultValues={editing || { status: 'healthy' }} onSubmit={saveFarm} onCancel={() => setFormOpen(false)} submitLabel={editing ? copy.save : copy.createButton} />
      </Modal>
      <ConfirmDialog open={Boolean(deleting)} onClose={() => setDeleting(null)} onConfirm={deleteFarm} message={deleting ? `Bạn có chắc muốn xóa “${deleting.name}”? Hành động này không thể hoàn tác.` : ''} />
    </div>
  )
}
