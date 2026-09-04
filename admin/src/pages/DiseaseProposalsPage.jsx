import { Check, Eye, FileCheck2, LoaderCircle, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import DataTable from '../components/common/DataTable.jsx'
import Modal from '../components/common/Modal.jsx'
import PageHeader from '../components/common/PageHeader.jsx'
import StatusBadge from '../components/common/StatusBadge.jsx'
import { initialProposals } from '../data/demoData.js'
import { adminProposalsApi } from '../services/proposals.js'
import { loadCollection, saveCollection } from '../utils/storage.js'

const STORAGE_KEY = 'plantcare_admin_proposals'

function unwrapList(payload) {
  if (Array.isArray(payload)) return payload
  return payload?.items || payload?.proposals || payload?.data || []
}

export default function DiseaseProposalsPage() {
  const [proposals, setProposals] = useState(() => loadCollection(STORAGE_KEY, initialProposals))
  const [mode, setMode] = useState('loading')
  const [selected, setSelected] = useState(null)
  const [adminNote, setAdminNote] = useState('')
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    let active = true
    adminProposalsApi.list()
      .then((payload) => { if (active) { setProposals(unwrapList(payload)); setMode('api') } })
      .catch(() => { if (active) setMode('demo') })
    return () => { active = false }
  }, [])

  useEffect(() => { if (mode !== 'loading') saveCollection(STORAGE_KEY, proposals) }, [mode, proposals])

  function openReview(row) {
    setSelected(row)
    setAdminNote(row.admin_note || '')
    setMessage('')
  }

  async function review(status) {
    if (!selected) return
    setSaving(true)
    try {
      let updated = { ...selected, status, admin_note: adminNote }
      if (mode === 'api') updated = await adminProposalsApi.update(selected.id, { status, admin_note: adminNote })
      setProposals((items) => items.map((item) => item.id === selected.id ? { ...item, ...updated, status } : item))
      setMessage(status === 'approved' ? 'Đã duyệt đề xuất. Nội dung có thể xuất hiện trong disease_info.' : 'Đã từ chối đề xuất và lưu ghi chú phản hồi.')
      setSelected(null)
    } catch (error) {
      setMessage(error?.response?.data?.detail || 'Không thể cập nhật đề xuất. Vui lòng kiểm tra API Admin.')
    } finally {
      setSaving(false)
    }
  }

  const columns = [
    { key: 'disease_name', label: 'Đề xuất bệnh', sortable: true, render: (value, row) => <div><p className="font-bold text-slate-800">{value}</p><p className="mt-0.5 text-xs text-slate-400">{row.label_key}</p></div> },
    { key: 'plant', label: 'Cây trồng', sortable: true },
    { key: 'proposer_name', label: 'Kỹ thuật viên', sortable: true },
    { key: 'created_at', label: 'Ngày gửi', sortable: true },
    { key: 'status', label: 'Trạng thái', render: (value) => <StatusBadge value={value} /> },
  ]

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader eyebrow="Tuần 6 • Admin Review" title="Duyệt đề xuất bệnh" description="Kiểm tra đề xuất của Kỹ thuật viên trước khi đưa nội dung vào thư viện disease_info." />
      <div className={`mb-5 flex items-center gap-2 rounded-2xl border p-4 text-sm ${mode === 'api' ? 'border-emerald-100 bg-emerald-50 text-emerald-800' : 'border-amber-100 bg-amber-50 text-amber-800'}`}>{mode === 'loading' && <LoaderCircle className="animate-spin" size={17} />}{mode === 'api' ? 'Đã kết nối GET /admin/disease-proposals.' : mode === 'demo' ? 'API chưa phản hồi, đang dùng dữ liệu demo.' : 'Đang tải đề xuất...'}</div>
      {message && <p className="mb-5 rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-700">{message}</p>}
      <DataTable columns={columns} data={proposals} searchPlaceholder="Tìm tên bệnh, cây trồng hoặc kỹ thuật viên..." actions={(row) => <button type="button" onClick={() => openReview(row)} className="rounded-lg p-2 text-slate-400 hover:bg-leaf-50 hover:text-leaf-700" aria-label="Xem và duyệt"><Eye size={17} /></button>} emptyTitle="Không có đề xuất" emptyDescription="Các đề xuất của Kỹ thuật viên sẽ xuất hiện tại đây." />

      <Modal open={Boolean(selected)} onClose={() => setSelected(null)} title="Chi tiết đề xuất" description={selected ? `${selected.disease_name} • ${selected.proposer_name}` : ''} size="xl">
        {selected && <div className="space-y-5"><div className="grid gap-4 sm:grid-cols-2"><div className="rounded-2xl bg-slate-50 p-4"><p className="text-xs font-bold uppercase tracking-wider text-slate-400">Label key</p><p className="mt-2 font-bold text-slate-800">{selected.label_key}</p></div><div className="rounded-2xl bg-slate-50 p-4"><p className="text-xs font-bold uppercase tracking-wider text-slate-400">Cây trồng</p><p className="mt-2 font-bold text-slate-800">{selected.plant}</p></div></div><section><h3 className="text-sm font-extrabold text-slate-800">Triệu chứng</h3><p className="mt-2 text-sm leading-6 text-slate-600">{selected.symptoms}</p></section><section><h3 className="text-sm font-extrabold text-slate-800">Gợi ý xử lý</h3><p className="mt-2 text-sm leading-6 text-slate-600">{selected.treatment}</p></section><section><h3 className="text-sm font-extrabold text-slate-800">Bằng chứng</h3><p className="mt-2 text-sm leading-6 text-slate-600">{selected.evidence}</p></section><label><span className="mb-2 block text-sm font-semibold text-slate-700">Ghi chú của Admin</span><textarea className="input-control resize-y" rows="3" value={adminNote} onChange={(event) => setAdminNote(event.target.value)} placeholder="Lý do duyệt hoặc từ chối..." /></label><div className="flex flex-col-reverse gap-3 border-t border-slate-100 pt-5 sm:flex-row sm:justify-end"><button type="button" className="inline-flex items-center justify-center gap-2 rounded-xl bg-rose-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-rose-700" disabled={saving} onClick={() => review('rejected')}><X size={17} /> Từ chối</button><button type="button" className="btn-primary" disabled={saving} onClick={() => review('approved')}>{saving ? <LoaderCircle className="animate-spin" size={17} /> : <Check size={17} />} Duyệt đề xuất</button></div></div>}
      </Modal>
    </div>
  )
}
