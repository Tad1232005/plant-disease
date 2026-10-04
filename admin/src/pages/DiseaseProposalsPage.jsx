import { Check, Eye, FileCheck2, LoaderCircle, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import DataTable from '../components/common/DataTable.jsx'
import ConfirmDialog from '../components/common/ConfirmDialog.jsx'
import Modal from '../components/common/Modal.jsx'
import PageHeader from '../components/common/PageHeader.jsx'
import StatusBadge from '../components/common/StatusBadge.jsx'
import { useLanguage } from '../contexts/LanguageContext.jsx'

import { adminProposalsApi } from '../services/proposals.js'
import { getApiError } from '../services/client.js'

function unwrapList(payload) {
  if (Array.isArray(payload)) return payload
  return payload?.items || payload?.proposals || payload?.data || []
}

export default function DiseaseProposalsPage() {
  const { t } = useLanguage()
  const [proposals, setProposals] = useState([])
  const [mode, setMode] = useState('loading')
  const [selected, setSelected] = useState(null)
  const [adminNote, setAdminNote] = useState('')
  const [saving, setSaving] = useState(false)
  // Trạng thái 'approved' | 'rejected' đang chờ ConfirmDialog xác nhận trước khi gọi API.
  const [pendingReview, setPendingReview] = useState(null)
  const [message, setMessage] = useState('')

  useEffect(() => {
    let active = true
    adminProposalsApi.list()
      .then((payload) => { if (active) { setProposals(unwrapList(payload)); setMode('api') } })
      .catch((error) => { if (active) { setMode('error'); setMessage(getApiError(error)) } })
    return () => { active = false }
  }, [])

  function openReview(row) {
    setSelected(row)
    setAdminNote(row.admin_note || '')
    setMessage('')
  }

  async function review(status) {
    if (!selected) return
    setSaving(true)
    try {
      const updated = await adminProposalsApi.update(selected.id, { status, admin_note: adminNote })
      setProposals((items) => items.map((item) => item.id === selected.id ? { ...item, ...updated, status } : item))
      setMessage(status === 'approved' ? 'Đã duyệt đề xuất. Nội dung có thể xuất hiện trong disease_info.' : 'Đã từ chối đề xuất và lưu ghi chú phản hồi.')
      setSelected(null)
    } catch (error) {
      setMessage(error?.response?.data?.detail || 'Không thể cập nhật đề xuất. Vui lòng kiểm tra API Admin.')
    } finally {
      setSaving(false)
    }
  }

  // Chỉ gọi API sau khi ConfirmDialog xác nhận; đóng dialog dù thành công hay lỗi
  // để message lỗi hiển thị ở trang chính thay vì bị che sau modal.
  async function confirmReview() {
    if (!pendingReview || saving) return
    await review(pendingReview)
    setPendingReview(null)
  }

  const rejecting = pendingReview === 'rejected'
  const reviewTargetName = selected?.disease_name || ''

  const columns = [
    { key: 'disease_name', label: t('proposals.col_label'), sortable: true, render: (value, row) => <div><p className="font-bold text-slate-800 dark:text-slate-100">{value}</p><p className="mt-0.5 text-xs text-slate-400 dark:text-slate-500">{row.label_key}</p></div> },
    { key: 'plant', label: t('proposals.col_crop'), sortable: true },
    { key: 'proposer_name', label: t('proposals.col_author'), sortable: true },
    { key: 'created_at', label: t('proposals.col_date'), sortable: true },
    { key: 'status', label: t('proposals.col_status'), render: (value) => <StatusBadge value={value} /> },
  ]

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader eyebrow={t('proposals.eyebrow')} title={t('proposals.title')} description={t('proposals.desc')} />
      <div className={`mb-5 flex items-center gap-2 rounded-2xl border p-4 text-sm ${mode === 'api' ? 'border-emerald-100 bg-emerald-50 text-emerald-800 dark:border-emerald-900/40 dark:bg-emerald-950/40 dark:text-emerald-200' : mode === 'error' ? 'border-rose-100 bg-rose-50 text-rose-800 dark:border-rose-900/40 dark:bg-rose-950/40 dark:text-rose-200' : 'border-amber-100 bg-amber-50 text-amber-800 dark:border-amber-900/40 dark:bg-amber-950/40 dark:text-amber-200'}`}>{mode === 'loading' && <LoaderCircle className="animate-spin" size={17} />}{mode === 'api' ? t('proposals.mode_api') : mode === 'error' ? t('proposals.mode_error') : t('proposals.mode_loading')}</div>
      {message && <p className="mb-5 rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">{t(message)}</p>}
      <DataTable columns={columns} data={proposals} searchPlaceholder={t('proposals.search_placeholder')} actions={(row) => <button type="button" onClick={() => openReview(row)} className="rounded-lg p-2 text-slate-400 hover:bg-leaf-50 hover:text-leaf-700 dark:hover:bg-slate-800 dark:hover:text-leaf-300" aria-label={t('proposals.btn_view')}><Eye size={17} /></button>} emptyTitle={t('proposals.empty_title')} emptyDescription={t('proposals.empty_desc')} />

      <Modal open={Boolean(selected)} onClose={() => setSelected(null)} title={t('proposals.detail_title')} description={selected ? `${selected.disease_name} • ${selected.proposer_name}` : ''} size="xl">
        {selected && <div className="space-y-5"><div className="grid gap-4 sm:grid-cols-2"><div className="rounded-2xl bg-slate-50 p-4 dark:bg-slate-800/60"><p className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">{t('proposals.field_label_key')}</p><p className="mt-2 font-bold text-slate-800 dark:text-slate-100">{selected.label_key}</p></div><div className="rounded-2xl bg-slate-50 p-4 dark:bg-slate-800/60"><p className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">{t('proposals.field_plant')}</p><p className="mt-2 font-bold text-slate-800 dark:text-slate-100">{selected.plant}</p></div></div><section><h3 className="text-sm font-extrabold text-slate-800 dark:text-slate-200">{t('proposals.field_symptoms')}</h3><p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{selected.symptoms}</p></section><section><h3 className="text-sm font-extrabold text-slate-800 dark:text-slate-200">{t('proposals.field_treatment')}</h3><p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{selected.treatment}</p></section><section><h3 className="text-sm font-extrabold text-slate-800 dark:text-slate-200">{t('proposals.field_evidence')}</h3><p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{selected.evidence}</p></section><label><span className="mb-2 block text-sm font-semibold text-slate-700 dark:text-slate-200">{t('proposals.admin_note')}</span><textarea className="input-control resize-y" rows="3" value={adminNote} onChange={(event) => setAdminNote(event.target.value)} placeholder={t('proposals.note_placeholder')} /></label><div className="flex flex-col-reverse gap-3 border-t border-slate-100 pt-5 dark:border-slate-800 sm:flex-row sm:justify-end"><button type="button" className="inline-flex items-center justify-center gap-2 rounded-xl bg-rose-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-rose-700" disabled={saving} onClick={() => setPendingReview('rejected')}><X size={17} /> {t('proposals.btn_reject')}</button><button type="button" className="btn-primary" disabled={saving} onClick={() => setPendingReview('approved')}>{saving ? <LoaderCircle className="animate-spin" size={17} /> : <Check size={17} />} {t('proposals.btn_approve')}</button></div></div>}
      </Modal>

      <ConfirmDialog
        open={Boolean(pendingReview)}
        onClose={() => setPendingReview(null)}
        onConfirm={confirmReview}
        title={rejecting ? 'proposals.confirm_reject_title' : 'proposals.confirm_approve_title'}
        message={t(rejecting ? 'proposals.confirm_reject_msg' : 'proposals.confirm_approve_msg', { name: reviewTargetName })}
        confirmLabel={rejecting ? 'proposals.btn_reject' : 'proposals.btn_approve'}
        tone={rejecting ? 'danger' : 'primary'}
        loading={saving}
      />
    </div>
  )
}
