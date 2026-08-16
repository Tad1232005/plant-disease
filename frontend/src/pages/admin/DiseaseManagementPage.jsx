import { Edit3, Leaf, Plus, Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import ConfirmDialog from '../../components/common/ConfirmDialog.jsx'
import CrudForm from '../../components/common/CrudForm.jsx'
import DataTable from '../../components/common/DataTable.jsx'
import Modal from '../../components/common/Modal.jsx'
import PageHeader from '../../components/common/PageHeader.jsx'
import StatusBadge from '../../components/common/StatusBadge.jsx'
import { initialDiseases } from '../../data/demoData.js'
import { loadCollection, saveCollection } from '../../utils/storage.js'

const STORAGE_KEY = 'plantcare_diseases'
const diseaseFields = [
  { name: 'labelKey', label: 'Label key', placeholder: 'tomato_late_blight', hint: 'Khớp với nhãn classes.json của model' },
  { name: 'name', label: 'Tên bệnh', placeholder: 'Mốc sương cà chua' },
  { name: 'plant', label: 'Cây trồng', placeholder: 'Cà chua' },
  { name: 'severity', label: 'Mức độ', type: 'select', options: [{ value: 'low', label: 'Thấp' }, { value: 'medium', label: 'Trung bình' }, { value: 'high', label: 'Cao' }] },
  { name: 'symptoms', label: 'Mô tả triệu chứng', type: 'textarea', rows: 3, fullWidth: true },
  { name: 'treatment', label: 'Gợi ý xử lý / điều trị', type: 'textarea', rows: 4, fullWidth: true },
]

export default function DiseaseManagementPage() {
  const [diseases, setDiseases] = useState(() => loadCollection(STORAGE_KEY, initialDiseases))
  const [editing, setEditing] = useState(null)
  const [formOpen, setFormOpen] = useState(false)
  const [deleting, setDeleting] = useState(null)

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
    { key: 'name', label: 'Nội dung bệnh', sortable: true, render: (value, row) => <div className="flex items-center gap-3"><span className="grid h-9 w-9 place-items-center rounded-xl bg-leaf-50 text-leaf-700"><Leaf size={17} /></span><div><p className="font-bold text-slate-800">{value}</p><p className="mt-0.5 text-xs text-slate-400">{row.labelKey}</p></div></div> },
    { key: 'plant', label: 'Cây trồng', sortable: true },
    { key: 'severity', label: 'Mức độ', render: (value) => <StatusBadge value={value} /> },
    { key: 'symptoms', label: 'Triệu chứng', render: (value) => <p className="max-w-xs truncate">{value}</p> },
  ]

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader eyebrow="Admin API #1" title="Quản lý nội dung bệnh" description="CRUD disease_info: public có thể đọc, chỉ quản trị viên được thêm, sửa hoặc xóa." action={<button className="btn-primary" onClick={openCreate}><Plus size={18} /> Thêm bệnh cây</button>} />
      <DataTable columns={columns} data={diseases} searchPlaceholder="Tìm tên bệnh, label hoặc cây trồng..." actions={(row) => <span className="inline-flex gap-1"><button onClick={() => openEdit(row)} className="rounded-lg p-2 text-slate-400 hover:bg-leaf-50 hover:text-leaf-700" aria-label="Sửa"><Edit3 size={17} /></button><button onClick={() => setDeleting(row)} className="rounded-lg p-2 text-slate-400 hover:bg-rose-50 hover:text-rose-600" aria-label="Xóa"><Trash2 size={17} /></button></span>} />
      <Modal open={formOpen} onClose={() => setFormOpen(false)} title={editing ? 'Cập nhật nội dung bệnh' : 'Thêm nội dung bệnh'} description="Thông tin này sẽ hiển thị trong thư viện bệnh cho nông dân và kỹ thuật viên." size="xl"><CrudForm fields={diseaseFields} defaultValues={editing || { severity: 'medium' }} onSubmit={saveDisease} onCancel={() => setFormOpen(false)} submitLabel={editing ? 'Lưu cập nhật' : 'Thêm nội dung'} /></Modal>
      <ConfirmDialog open={Boolean(deleting)} onClose={() => setDeleting(null)} onConfirm={deleteDisease} message={deleting ? `Bạn có chắc muốn xóa nội dung “${deleting.name}”?` : ''} />
    </div>
  )
}
