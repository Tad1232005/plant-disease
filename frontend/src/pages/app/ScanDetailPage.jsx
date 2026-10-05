import { ArrowLeft, Calendar, CheckCircle2, FileText, Leaf, LoaderCircle, MapPin, Printer, ShieldAlert, Sparkles } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import PageHeader from '../../components/common/PageHeader.jsx'
import StatusBadge from '../../components/common/StatusBadge.jsx'
import { usePreferences } from '../../contexts/PreferencesContext.jsx'
import { scansApi } from '../../api/scans.js'
import { getScanGradCam } from '../../api/predict.js'

function friendlyLabel(label = '') {
  return String(label).replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function toPercent(value) {
  const num = Number(value || 0)
  return num <= 1 ? num * 100 : num
}

export default function ScanDetailPage() {
  const { id } = useParams()
  const { language } = usePreferences()
  const isVi = language === 'vi'

  const [scan, setScan] = useState(null)
  const [gradcamUrl, setGradcamUrl] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    setLoading(true)
    scansApi.getById(id)
      .then((data) => {
        if (!active) return
        setScan(data)
        // Nếu có scan, thử nạp gradcam
        getScanGradCam(id).then((url) => {
          if (active) setGradcamUrl(url)
        }).catch(() => {})
      })
      .catch((err) => {
        if (!active) return
        setError(err?.response?.data?.detail || (isVi ? 'Không tìm thấy ca quét này.' : 'Scan not found.'))
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => { active = false }
  }, [id, isVi])

  if (loading) {
    return (
      <div className="mx-auto flex min-h-96 max-w-5xl flex-col items-center justify-center p-8 text-center">
        <LoaderCircle className="animate-spin text-leaf-600" size={36} />
        <p className="mt-4 text-sm font-semibold text-slate-500">
          {isVi ? 'Đang tải chi tiết ca quét...' : 'Loading scan details...'}
        </p>
      </div>
    )
  }

  if (error || !scan) {
    return (
      <div className="mx-auto max-w-2xl text-center py-16">
        <ShieldAlert className="mx-auto text-rose-500" size={48} />
        <h2 className="mt-4 text-xl font-bold text-slate-800">{isVi ? 'Không tìm thấy dữ liệu' : 'Data not found'}</h2>
        <p className="mt-2 text-sm text-slate-500">{error}</p>
        <Link to="/app/history" className="btn-secondary mt-6 inline-flex">
          <ArrowLeft size={16} /> {isVi ? 'Quay lại Lịch sử' : 'Back to History'}
        </Link>
      </div>
    )
  }

  const confidence = toPercent(scan.confidence)
  const isValidLeaf = scan.is_valid_leaf ?? true
  const topK = scan.top3 || scan.top_k || []
  const dateFormatted = scan.created_at
    ? new Intl.DateTimeFormat('vi-VN', { dateStyle: 'full', timeStyle: 'short' }).format(new Date(scan.created_at))
    : 'Chưa xác định'

  return (
    <div className="mx-auto max-w-5xl">
      <div className="mb-4 flex items-center justify-between">
        <Link to="/app/history" className="inline-flex items-center gap-1.5 text-xs font-bold text-leaf-700 hover:text-leaf-800">
          <ArrowLeft size={15} /> {isVi ? 'Quay lại Lịch sử' : 'Back to History'}
        </Link>
        <button
          onClick={() => window.print()}
          className="btn-secondary text-xs !py-2 !px-3"
        >
          <Printer size={15} /> {isVi ? 'In kết quả' : 'Print PDF'}
        </button>
      </div>

      <PageHeader
        eyebrow={`ID Ca quét #${scan.id}`}
        title={friendlyLabel(scan.predicted_label || (isVi ? 'Ảnh ngoài miền dữ liệu' : 'Out of distribution'))}
        description={`${dateFormatted} • Model: ${scan.model_version || 'Ensemble Cascade'}`}
      />

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        {/* Kết quả chính & khuyến nghị */}
        <div className="space-y-6">
          <div className="card overflow-hidden">
            <div className={`p-6 text-white bg-gradient-to-r ${isValidLeaf ? 'from-leaf-700 to-leaf-600' : 'from-amber-700 to-orange-600'}`}>
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-white/70">
                    {isValidLeaf ? (isVi ? 'Chẩn đoán xác nhận' : 'Verified diagnosis') : (isVi ? 'Cảnh báo OOD' : 'Out of distribution')}
                  </span>
                  <h3 className="mt-1 text-2xl font-black">{friendlyLabel(scan.predicted_label)}</h3>
                </div>
                <span className="grid h-12 w-12 place-items-center rounded-2xl bg-white/20">
                  {isValidLeaf ? <CheckCircle2 size={24} /> : <ShieldAlert size={24} />}
                </span>
              </div>
              <div className="mt-6 flex items-baseline justify-between">
                <span className="text-sm text-white/70">{isVi ? 'Độ tin cậy mô hình' : 'Confidence'}</span>
                <span className="text-3xl font-extrabold">{confidence.toFixed(1)}%</span>
              </div>
              <div className="mt-2 h-2 overflow-hidden rounded-full bg-black/15">
                <div className="h-full rounded-full bg-white transition-all" style={{ width: `${Math.min(confidence, 100)}%` }} />
              </div>
            </div>

            <div className="p-6 space-y-5">
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  {isVi ? 'Chi tiết phân loại Top 3' : 'Top 3 Probabilities'}
                </h4>
                <div className="mt-3 space-y-2.5">
                  {topK.map((item, index) => {
                    const pct = toPercent(item.confidence)
                    return (
                      <div key={index} className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-slate-700">{index + 1}. {friendlyLabel(item.label)}</span>
                        <span className="font-bold text-slate-600">{pct.toFixed(1)}%</span>
                      </div>
                    )
                  })}
                </div>
              </div>

              {scan.treatment && (
                <div className="rounded-2xl border border-emerald-100 bg-emerald-50/60 p-4">
                  <div className="flex items-center gap-2 text-emerald-800">
                    <Leaf size={16} />
                    <span className="text-xs font-bold uppercase tracking-wider">{isVi ? 'Biện pháp điều trị' : 'Treatment plan'}</span>
                  </div>
                  <p className="mt-2 text-xs leading-5 text-emerald-950/80">{scan.treatment}</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Khối hiển thị ảnh và Grad-CAM */}
        <div className="space-y-6">
          <div className="card p-5">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
              {isVi ? 'Bản đồ nhiệt Grad-CAM' : 'Grad-CAM Heatmap'}
            </h4>
            <div className="relative aspect-square w-full overflow-hidden rounded-2xl bg-slate-900">
              {gradcamUrl ? (
                <img src={gradcamUrl} alt="Grad-CAM" className="h-full w-full object-contain" />
              ) : (
                <div className="flex h-full w-full flex-col items-center justify-center p-6 text-center text-slate-400">
                  <Sparkles size={28} className="text-amber-500/70" />
                  <p className="mt-2 text-xs">
                    {isVi ? 'Đang tạo hoặc xem heatmap mô hình...' : 'Generating or viewing model heatmap...'}
                  </p>
                </div>
              )}
            </div>
            <p className="mt-3 text-[11px] leading-4 text-slate-400">
              {isVi
                ? 'Vùng màu đỏ thể hiện các đặc trưng lá cây mà mô hình mạng nơ-ron tập trung cao độ để đưa ra chẩn đoán.'
                : 'Red regions show where the convolutional neural network focused to classify this leaf disease.'}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
