import { FileCheck2, Plus, Send, Stethoscope } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { proposalsApi } from '../../api/proposals.js'
import CrudForm from '../../components/common/CrudForm.jsx'
import DataTable from '../../components/common/DataTable.jsx'
import Modal from '../../components/common/Modal.jsx'
import PageHeader from '../../components/common/PageHeader.jsx'
import StatCard from '../../components/common/StatCard.jsx'
import StatusBadge from '../../components/common/StatusBadge.jsx'
import { initialProposals, scanHistory } from '../../data/demoData.js'
import { loadCollection, saveCollection } from '../../utils/storage.js'
import { usePreferences } from '../../contexts/PreferencesContext.jsx'

const STORAGE_KEY = 'plantcare_disease_proposals'

function unwrapList(payload) {
  if (Array.isArray(payload)) return payload
  return payload?.items || payload?.proposals || payload?.data || []
}

export default function DiseaseProposalsPage() {
  const { language } = usePreferences()
  const copy = language === 'vi' ? {
    eyebrow: 'Tuần 5 • Technician Proposal', title: 'Đề xuất nội dung bệnh', description: 'Kỹ thuật viên gửi kiến thức chuyên môn để Admin kiểm duyệt trước khi hiển thị cho Nông dân.', send: 'Gửi đề xuất', total: 'Tổng đề xuất', approved: 'Đã duyệt', pending: 'Đang chờ', loading: 'Đang kết nối API đề xuất...', api: 'Đã kết nối GET /disease-proposals/mine.', demo: 'API chưa phản hồi, màn hình đang dùng dữ liệu demo localStorage.', disease: 'Đề xuất bệnh', crop: 'Cây trồng', date: 'Ngày gửi', status: 'Trạng thái', search: 'Tìm tên bệnh, label hoặc cây trồng...', empty: 'Chưa có đề xuất nào', emptyText: 'Gửi đề xuất bệnh đầu tiên để Admin kiểm duyệt.', modalTitle: 'Gửi đề xuất bệnh', modalText: 'Điền thông tin chuyên môn và liên kết với một lần chẩn đoán nếu có.', submit: 'Gửi chờ duyệt', reference: 'Ảnh chẩn đoán tham chiếu', name: 'Tên bệnh đề xuất', symptoms: 'Triệu chứng quan sát', treatment: 'Gợi ý xử lý', evidence: 'Bằng chứng chuyên môn', success: 'Đề xuất đã được gửi và đang chờ Admin duyệt.', failure: 'Không thể gửi đề xuất. Vui lòng kiểm tra API.',
  } : {
    eyebrow: 'Week 5 • Technician Proposal', title: 'Disease content proposals', description: 'Technicians submit expert knowledge for Admin review before it appears for Farmers.', send: 'Submit proposal', total: 'Total proposals', approved: 'Approved', pending: 'Pending', loading: 'Connecting to the proposal API...', api: 'Connected to GET /disease-proposals/mine.', demo: 'The API is unavailable; using local demo data.', disease: 'Disease proposal', crop: 'Crop', date: 'Submitted', status: 'Status', search: 'Search by disease, label, or crop...', empty: 'No proposals yet', emptyText: 'Submit the first disease proposal for Admin review.', modalTitle: 'Submit disease proposal', modalText: 'Enter expert information and optionally link a diagnosis.', submit: 'Submit for review', reference: 'Reference diagnosis', name: 'Proposed disease name', symptoms: 'Observed symptoms', treatment: 'Suggested action', evidence: 'Professional evidence', success: 'The proposal was submitted for Admin review.', failure: 'Unable to submit the proposal. Check the API.',
  }
  const [proposals, setProposals] = useState(() => loadCollection(STORAGE_KEY, initialProposals))
  const [mode, setMode] = useState('loading')
  const [formOpen, setFormOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const scans = loadCollection('plantcare_scan_history', scanHistory)

  useEffect(() => {
    let active = true
    proposalsApi.mine()
      .then((payload) => {
        if (!active) return
        setProposals(unwrapList(payload))
        setMode('api')
      })
      .catch(() => { if (active) setMode('demo') })
    return () => { active = false }
  }, [])

  useEffect(() => {
    if (mode !== 'loading') saveCollection(STORAGE_KEY, proposals)
  }, [mode, proposals])

  const fields = useMemo(() => [
    { name: 'scan_id', label: copy.reference, type: 'select', required: false, options: scans.slice(0, 20).map((scan) => ({ value: String(scan.id), label: `${scan.farm} — ${scan.result}` })) },
    { name: 'disease_name', label: copy.name, placeholder: language === 'vi' ? 'Đốm lá vi khuẩn cà chua' : 'Tomato bacterial spot' },
    { name: 'label_key', label: 'Label key', placeholder: 'tomato_bacterial_spot', hint: 'Dùng chữ thường và dấu gạch dưới' },
    { name: 'plant', label: copy.crop, placeholder: language === 'vi' ? 'Cà chua' : 'Tomato' },
    { name: 'symptoms', label: copy.symptoms, type: 'textarea', rows: 3, fullWidth: true },
    { name: 'treatment', label: copy.treatment, type: 'textarea', rows: 3, fullWidth: true },
    { name: 'evidence', label: copy.evidence, type: 'textarea', rows: 3, fullWidth: true },
  ], [copy, language, scans])

  async function createProposal(values) {
    setSaving(true)
    setMessage('')
    const payload = { ...values, scan_id: values.scan_id ? Number(values.scan_id) : null }
    try {
      if (mode === 'api') {
        const created = await proposalsApi.create(payload)
        setProposals((items) => [{ ...created, status: created.status || 'pending' }, ...items])
      } else {
        setProposals((items) => [{ ...payload, id: Date.now(), status: 'pending', created_at: new Intl.DateTimeFormat(language === 'vi' ? 'vi-VN' : 'en-US', { dateStyle: 'short', timeStyle: 'short' }).format(new Date()) }, ...items])
      }
      setMessage(copy.success)
      setFormOpen(false)
    } catch (error) {
      setMessage(error?.response?.data?.detail || copy.failure)
    } finally {
      setSaving(false)
    }
  }

  const columns = [
    { key: 'disease_name', label: copy.disease, sortable: true, render: (value, row) => <div><p className="font-bold text-slate-800">{value}</p><p className="mt-0.5 text-xs text-slate-400">{row.label_key}</p></div> },
    { key: 'plant', label: copy.crop, sortable: true },
    { key: 'created_at', label: copy.date, sortable: true },
    { key: 'status', label: copy.status, render: (value) => <StatusBadge value={value} /> },
  ]

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader eyebrow={copy.eyebrow} title={copy.title} description={copy.description} action={<button className="btn-primary" onClick={() => { setMessage(''); setFormOpen(true) }}><Plus size={18} />{copy.send}</button>} />
      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <StatCard icon={Send} label={copy.total} value={proposals.length} />
        <StatCard icon={FileCheck2} label={copy.approved} value={proposals.filter((item) => item.status === 'approved').length} tone="blue" />
        <StatCard icon={Stethoscope} label={copy.pending} value={proposals.filter((item) => item.status === 'pending').length} tone="amber" />
      </div>
      <div className={`mb-5 rounded-2xl border p-4 text-sm ${mode === 'api' ? 'border-emerald-100 bg-emerald-50 text-emerald-800' : 'border-amber-100 bg-amber-50 text-amber-800'}`}>
        {mode === 'loading' ? copy.loading : mode === 'api' ? copy.api : copy.demo}
      </div>
      {message && <p className="mb-5 rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-700">{message}</p>}
      <DataTable columns={columns} data={proposals} searchPlaceholder={copy.search} emptyTitle={copy.empty} emptyDescription={copy.emptyText} />
      <Modal open={formOpen} onClose={() => setFormOpen(false)} title={copy.modalTitle} description={copy.modalText} size="xl"><CrudForm fields={fields} onSubmit={createProposal} onCancel={() => setFormOpen(false)} submitLabel={copy.submit} loading={saving} /></Modal>
    </div>
  )
}
