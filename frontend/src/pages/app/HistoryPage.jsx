import { ExternalLink, Eye, History, Leaf, LoaderCircle, ShieldAlert } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { scansApi } from '../../api/scans.js'
import DataTable from '../../components/common/DataTable.jsx'
import Modal from '../../components/common/Modal.jsx'
import PageHeader from '../../components/common/PageHeader.jsx'
import StatusBadge from '../../components/common/StatusBadge.jsx'
import { scanHistory } from '../../data/demoData.js'
import { loadCollection } from '../../utils/storage.js'
import { usePreferences } from '../../contexts/PreferencesContext.jsx'
import { useAuth } from '../../contexts/AuthContext.jsx'

const HISTORY_KEY = 'plantcare_scan_history'

function friendlyLabel(label = '') {
  return String(label)
    .replaceAll('___', ' - ')
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function toPercent(value) {
  const number = Number(value || 0)
  return number <= 1 ? number * 100 : number
}

function unwrapList(payload) {
  if (Array.isArray(payload)) return payload
  return payload?.items || payload?.scans || payload?.data || []
}

function normalizeScan(scan, language = 'vi', farms = []) {
  const rawDate = scan.date || scan.created_at || scan.scanned_at
  const parsedDate = rawDate ? new Date(rawDate) : null
  const date = parsedDate && !Number.isNaN(parsedDate.valueOf())
    ? new Intl.DateTimeFormat(language === 'vi' ? 'vi-VN' : 'en-US', { dateStyle: 'short', timeStyle: 'short' }).format(parsedDate)
    : rawDate || (language === 'vi' ? 'Chưa có thời gian' : 'No timestamp')
  const confidence = toPercent(scan.confidence)

  const matchedFarm = Array.isArray(farms) ? farms.find((f) => String(f.id) === String(scan.farm_id)) : null
  const farmName = typeof scan.farm === 'string'
    ? scan.farm
    : scan.farm?.name || matchedFarm?.name || scan.farm_name || (scan.farm_id ? `Khu vực #${scan.farm_id}` : (language === 'vi' ? 'Không gắn khu vực' : 'No farm'))

  const isValidLeaf = scan.is_valid_leaf ?? (scan.validation_status === 'accepted')
  const label = scan.predicted_label || scan.result || scan.label || scan.prediction

  let result = ''
  if (!isValidLeaf || scan.validation_status === 'low_confidence' || scan.validation_status === 'ambiguous') {
    result = language === 'vi' ? 'Ảnh ngoài miền dữ liệu' : 'Out of distribution'
  } else if (label) {
    result = label
  } else {
    result = language === 'vi' ? 'Chưa có kết quả' : 'No result'
  }

  return {
    ...scan,
    id: scan.id || scan.scan_id,
    date,
    farm: farmName,
    result,
    confidence: Number(confidence.toFixed(1)),
    severity: scan.severity || (String(result).toLowerCase().includes('healthy') ? 'low' : 'medium'),
    top_k: scan.top_k || scan.top3 || [],
    is_valid_leaf: isValidLeaf,
    leafStatus: isValidLeaf ? 'valid' : 'invalid',
    treatment: scan.treatment || scan.recommendation || (language === 'vi'
      ? (isValidLeaf ? 'Tiếp tục theo dõi và đối chiếu triệu chứng thực tế.' : 'Chụp lại một lá cây rõ nét dưới ánh sáng tự nhiên.')
      : (isValidLeaf ? 'Continue monitoring and compare with real symptoms.' : 'Retake a clear leaf photo in natural light.')),
  }
}

export default function HistoryPage() {
  const { language } = usePreferences()
  const copy = language === 'vi' ? {
    eyebrow: 'Tuần 5 • Lịch sử & cảnh báo OOD', title: 'Lịch sử chẩn đoán', description: 'Xem lại kết quả, cảnh báo ảnh không hợp lệ và gợi ý xử lý cho từng lần quét.', time: 'Thời gian', farm: 'Khu vực', result: 'Kết quả', confidence: 'Độ tin cậy', ood: 'Kiểm tra OOD', severity: 'Mức độ', api: 'Đã kết nối API /scans/history.', local: 'Đang hiển thị các kết quả vừa chẩn đoán đã lưu trên trình duyệt.', demo: 'Backend lịch sử chưa phản hồi nên đang hiển thị dữ liệu mẫu.', loading: 'Đang tải lịch sử chẩn đoán...', search: 'Tìm theo khu vực hoặc kết quả...', detail: 'Xem chi tiết', empty: 'Chưa có lần chẩn đoán nào', emptyText: 'Hãy tải ảnh lá cây đầu tiên để bắt đầu lưu lịch sử.', detailTitle: 'Chi tiết lần chẩn đoán', detailLoading: 'Đang tải chi tiết...', invalid: 'Ảnh ngoài miền dữ liệu', top: 'Top dự đoán', treatment: 'Gợi ý xử lý',
  } : {
    eyebrow: 'Week 5 • History & OOD alerts', title: 'Diagnosis history', description: 'Review results, invalid-image warnings, and guidance for each scan.', time: 'Time', farm: 'Farm', result: 'Result', confidence: 'Confidence', ood: 'OOD check', severity: 'Severity', api: 'Connected to /scans/history.', local: 'Showing diagnoses saved in this browser.', demo: 'The history API is unavailable, so sample data is shown.', loading: 'Loading diagnosis history...', search: 'Search by farm or result...', detail: 'View details', empty: 'No diagnoses yet', emptyText: 'Upload your first leaf image to start saving history.', detailTitle: 'Diagnosis details', detailLoading: 'Loading details...', invalid: 'Out-of-domain image', top: 'Top predictions', treatment: 'Suggested action',
  }
  const [rows, setRows] = useState([])
  const [source, setSource] = useState('loading')
  const [detail, setDetail] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)

  const { user } = useAuth()
  const farms = useMemo(() => loadCollection('plantcare_farms', []), [])

  useEffect(() => {
    let active = true
    const historyKey = user?.id ? `plantcare_scan_history_${user.id}` : HISTORY_KEY
    scansApi.history()
      .then((payload) => {
        if (!active) return
        setRows(unwrapList(payload).map((item) => normalizeScan(item, language, farms)))
        setSource('api')
      })
      .catch(() => {
        if (!active) return
        const localRows = loadCollection(historyKey, [])
        setRows((localRows.length ? localRows : scanHistory).map((item) => normalizeScan(item, language, farms)))
        setSource(localRows.length ? 'local' : 'demo')
      })
    return () => { active = false }
  }, [language, user?.id, farms])

  async function openDetail(row) {
    setDetail(row)
    if (source !== 'api' || !row.id) return
    setDetailLoading(true)
    try { setDetail(normalizeScan(await scansApi.getById(row.id), language, farms)) }
    catch { setDetail(row) }
    finally { setDetailLoading(false) }
  }

  const columns = [
    { key: 'date', label: copy.time, sortable: true },
    { key: 'farm', label: copy.farm, sortable: true, render: (value) => <span className="font-semibold text-slate-800">{value}</span> },
    { key: 'result', label: copy.result, sortable: true, render: (value) => friendlyLabel(value) },
    { key: 'confidence', label: copy.confidence, sortable: true, render: (value) => <span className="font-extrabold text-leaf-700">{value}%</span> },
    { key: 'leafStatus', label: copy.ood, render: (value) => <StatusBadge value={value} /> },
    { key: 'severity', label: copy.severity, render: (value) => <StatusBadge value={value} /> },
  ]

  const sourceText = source === 'api'
    ? copy.api
    : source === 'local'
      ? copy.local
      : source === 'demo'
        ? copy.demo
        : copy.loading

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader eyebrow={copy.eyebrow} title={copy.title} description={copy.description} />
      {source !== 'api' && source !== 'loading' && (
        <div className="mb-5 flex items-start gap-3 rounded-2xl border border-sky-100 bg-sky-50 p-4 text-sm text-sky-800">
          <History className="mt-0.5 shrink-0" size={19} />
          <p className="leading-6">{sourceText}</p>
        </div>
      )}
      <DataTable columns={columns} data={rows} searchPlaceholder={copy.search} actions={(row) => <button type="button" onClick={() => openDetail(row)} className="rounded-lg p-2 text-slate-400 hover:bg-leaf-50 hover:text-leaf-700" aria-label={copy.detail}><Eye size={17} /></button>} emptyTitle={copy.empty} emptyDescription={copy.emptyText} />

      <Modal open={Boolean(detail)} onClose={() => setDetail(null)} title={copy.detailTitle} description={detail?.date} size="sm">
        {detailLoading ? (
          <div className="flex items-center justify-center gap-2 py-10 text-sm text-slate-500"><LoaderCircle className="animate-spin" size={18} />{copy.detailLoading}</div>
        ) : detail && (
          <div className="space-y-4">
            <div className={`rounded-2xl p-5 ${detail.is_valid_leaf ? 'bg-leaf-50' : 'border border-amber-200 bg-amber-50'}`}><div className="flex items-center gap-2">{detail.is_valid_leaf ? <Leaf size={17} className="text-leaf-700" /> : <ShieldAlert size={17} className="text-amber-700" />}<p className={`text-xs font-bold uppercase tracking-wider ${detail.is_valid_leaf ? 'text-leaf-600' : 'text-amber-700'}`}>{detail.is_valid_leaf ? copy.result : copy.invalid}</p></div><p className={`mt-2 text-xl font-black ${detail.is_valid_leaf ? 'text-leaf-900' : 'text-amber-900'}`}>{friendlyLabel(detail.result)}</p><p className={`mt-1 text-sm ${detail.is_valid_leaf ? 'text-leaf-700' : 'text-amber-700'}`}>{copy.confidence} {detail.confidence}%</p></div>
            <dl className="grid grid-cols-[auto_1fr] gap-x-5 gap-y-3 text-sm"><dt className="text-slate-400">{copy.farm}</dt><dd className="text-right font-semibold text-slate-700">{detail.farm}</dd><dt className="text-slate-400">{copy.severity}</dt><dd className="text-right"><StatusBadge value={detail.severity} /></dd></dl>
            {detail.top_k?.length > 0 && <div><p className="text-sm font-bold text-slate-800">{copy.top}</p><div className="mt-3 space-y-2">{detail.top_k.slice(0, 3).map((item, index) => <div key={`${item.label}-${index}`} className="flex justify-between rounded-xl bg-slate-50 px-3 py-2 text-xs"><span>{index + 1}. {friendlyLabel(item.label)}</span><strong>{toPercent(item.confidence).toFixed(1)}%</strong></div>)}</div></div>}
            <div className="rounded-2xl bg-emerald-50 p-4"><p className="text-xs font-bold uppercase tracking-wider text-emerald-700">{copy.treatment}</p><p className="mt-2 text-sm leading-6 text-emerald-900/75">{detail.treatment}</p></div>
            {detail.id && (
              <Link
                to={`/app/scans/${detail.id}`}
                className="btn-primary flex w-full items-center justify-center gap-2 !py-2.5 text-xs font-bold"
              >
                <ExternalLink size={14} />
                {language === 'vi' ? 'Xem trang chi tiết đầy đủ (Bản in & Grad-CAM)' : 'View Full Details & Grad-CAM'}
              </Link>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
