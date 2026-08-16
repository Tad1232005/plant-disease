import { Edit3, MapPin, Plus, Sprout, Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import ConfirmDialog from '../../components/common/ConfirmDialog.jsx'
import CrudForm from '../../components/common/CrudForm.jsx'
import DataTable from '../../components/common/DataTable.jsx'
import Modal from '../../components/common/Modal.jsx'
import PageHeader from '../../components/common/PageHeader.jsx'
import StatCard from '../../components/common/StatCard.jsx'
import StatusBadge from '../../components/common/StatusBadge.jsx'
import { initialFarms } from '../../data/demoData.js'
import { loadCollection, saveCollection } from '../../utils/storage.js'

const STORAGE_KEY = 'plantcare_farms'
const farmFields = [
  { name: 'name', label: 'Tên khu vực', placeholder: 'Ví dụ: Vườn cà chua A1', fullWidth: true },
  { name: 'location', label: 'Vị trí', placeholder: 'Tỉnh/thành phố' },
  { name: 'crop', label: 'Loại cây', placeholder: 'Cà chua, khoai tây...' },
  { name: 'area', label: 'Diện tích (ha)', type: 'number', min: 0.1, step: 0.1 },
  { name: 'status', label: 'Trạng thái', type: 'select', options: [
    { value: 'healthy', label: 'Khỏe mạnh' }, { value: 'attention', label: 'Cần chú ý' }, { value: 'risk', label: 'Nguy cơ cao' },
  ] },
]

export default function FarmsPage({ adminMode = false }) {
  const [farms, setFarms] = useState(() => loadCollection(STORAGE_KEY, initialFarms))
  const [editing, setEditing] = useState(null)
  const [formOpen, setFormOpen] = useState(false)
  const [deleting, setDeleting] = useState(null)

  useEffect(() => saveCollection(STORAGE_KEY, farms), [farms])

  function openCreate() { setEditing(null); setFormOpen(true) }
  function openEdit(farm) { setEditing(farm); setFormOpen(true) }
  function saveFarm(values) {
    if (editing) {
      setFarms((items) => items.map((item) => item.id === editing.id ? { ...item, ...values } : item))
    } else {
      setFarms((items) => [{ ...values, id: Date.now(), lastScan: 'Chưa quét' }, ...items])
    }
    setFormOpen(false)
  }
  function deleteFarm() { setFarms((items) => items.filter((item) => item.id !== deleting.id)); setDeleting(null) }

  const columns = [
    { key: 'name', label: 'Khu vực', sortable: true, render: (value, row) => <div><p className="font-bold text-slate-800">{value}</p><p className="mt-1 inline-flex items-center gap-1 text-xs text-slate-400"><MapPin size={12} />{row.location}</p></div> },
    { key: 'crop', label: 'Cây trồng', sortable: true },
    { key: 'area', label: 'Diện tích', sortable: true, render: (value) => `${value} ha` },
    { key: 'status', label: 'Sức khỏe', render: (value) => <StatusBadge value={value} /> },
    { key: 'lastScan', label: 'Lần quét cuối', sortable: true },
  ]

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader
        eyebrow={adminMode ? 'Quản trị dữ liệu' : 'Tuần 2 • Farm Management'}
        title={adminMode ? 'Dữ liệu trang trại' : 'Quản lý trang trại'}
        description="Thêm, sửa, xóa và theo dõi trạng thái từng khu vực trồng. Dữ liệu demo được lưu ở trình duyệt trong khi chờ API /farms."
        action={<button className="btn-primary" onClick={openCreate}><Plus size={18} /> Thêm khu vực</button>}
      />
      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <StatCard icon={Sprout} label="Tổng khu vực" value={String(farms.length).padStart(2, '0')} tone="green" />
        <StatCard icon={MapPin} label="Tổng diện tích" value={`${farms.reduce((sum, item) => sum + Number(item.area), 0).toFixed(1)} ha`} tone="blue" />
        <StatCard icon={Sprout} label="Khu vực ổn định" value={farms.filter((item) => item.status === 'healthy').length} tone="amber" />
      </div>
      <DataTable columns={columns} data={farms} searchPlaceholder="Tìm theo tên, vị trí hoặc cây trồng..." actions={(row) => (
        <span className="inline-flex gap-1">
          <button onClick={() => openEdit(row)} className="rounded-lg p-2 text-slate-400 hover:bg-leaf-50 hover:text-leaf-700" aria-label="Sửa"><Edit3 size={17} /></button>
          <button onClick={() => setDeleting(row)} className="rounded-lg p-2 text-slate-400 hover:bg-rose-50 hover:text-rose-600" aria-label="Xóa"><Trash2 size={17} /></button>
        </span>
      )} />
      <Modal open={formOpen} onClose={() => setFormOpen(false)} title={editing ? 'Cập nhật khu vực' : 'Thêm khu vực mới'} description="Thông tin này sẽ được dùng để nhóm lịch sử chẩn đoán theo vị trí.">
        <CrudForm fields={farmFields} defaultValues={editing || { status: 'healthy' }} onSubmit={saveFarm} onCancel={() => setFormOpen(false)} submitLabel={editing ? 'Lưu cập nhật' : 'Tạo khu vực'} />
      </Modal>
      <ConfirmDialog open={Boolean(deleting)} onClose={() => setDeleting(null)} onConfirm={deleteFarm} message={deleting ? `Bạn có chắc muốn xóa “${deleting.name}”? Hành động này không thể hoàn tác.` : ''} />
    </div>
  )
}
