import {
  ArrowLeft,
  Calendar,
  CheckCircle2,
  FileText,
  Image as ImageIcon,
  Layers,
  Leaf,
  LoaderCircle,
  Lock,
  LogIn,
  MapPin,
  Printer,
  ShieldAlert,
  Sparkles,
} from 'lucide-react'
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
  const [imageUrl, setImageUrl] = useState('')
  const [imageLoading, setImageLoading] = useState(false)
  const [gradcamUrl, setGradcamUrl] = useState('')
  const [gradcamLoading, setGradcamLoading] = useState(false)
  const [loading, setLoading] = useState(true)
  const [errorStatus, setErrorStatus] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    setLoading(true)
    setError('')
    setErrorStatus(null)

    let createdImageUrl = ''
    let createdGradcamUrl = ''

    scansApi.getById(id)
      .then((data) => {
        if (!active) return
        setScan(data)

        // 1. Tải ảnh gốc lá cây chụp thực tế
        setImageLoading(true)
        scansApi.getImage(id)
          .then((url) => {
            if (!active) {
              URL.revokeObjectURL(url)
              return
            }
            createdImageUrl = url
            setImageUrl(url)
          })
          .catch(() => {})
          .finally(() => {
            if (active) setImageLoading(false)
          })

        // 2. Nạp ảnh Grad-CAM nếu ca quét được chấp nhận
        if (data.is_valid_leaf && data.validation_status === 'accepted') {
          setGradcamLoading(true)
          getScanGradCam(id)
            .then((url) => {
              if (!active) {
                URL.revokeObjectURL(url)
                return
              }
              createdGradcamUrl = url
              setGradcamUrl(url)
            })
            .catch(() => {})
            .finally(() => {
              if (active) setGradcamLoading(false)
            })
        }
      })
      .catch((err) => {
        if (!active) return
        const status = err?.response?.status
        setErrorStatus(status)
        if (status === 401) {
          setError(
            isVi
              ? 'Phiên đăng nhập đã hết hạn hoặc bạn chưa đăng nhập. Vui lòng đăng nhập để xem chi tiết ca quét.'
              : 'Your session expired or you are not logged in. Please log in to view this scan.',
          )
        } else if (status === 403) {
          setError(
            isVi
              ? `Bạn không có quyền truy cập ca quét #${id}. Ca quét này thuộc quyền sở hữu của một tài khoản khác theo quy định bảo mật riêng tư.`
              : `You do not have permission to view scan #${id}. This scan belongs to another account under privacy policy.`,
          )
        } else if (status === 404) {
          setError(
            isVi
              ? `Không tìm thấy ca quét #${id}. Ca quét này không tồn tại hoặc đã bị xóa khỏi hệ thống.`
              : `Scan #${id} was not found or has been removed from the system.`,
          )
        } else {
          setError(
            err?.response?.data?.detail ||
              (isVi ? 'Không thể tải thông tin ca quét này.' : 'Unable to load scan details.'),
          )
        }
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
      if (createdImageUrl) URL.revokeObjectURL(createdImageUrl)
      if (createdGradcamUrl) URL.revokeObjectURL(createdGradcamUrl)
    }
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
    const isForbidden = errorStatus === 403
    const isUnauthorized = errorStatus === 401

    return (
      <div className="mx-auto max-w-xl text-center py-16 px-4">
        <div
          className={`mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl ${
            isForbidden
              ? 'bg-amber-100 text-amber-700'
              : isUnauthorized
                ? 'bg-sky-100 text-sky-700'
                : 'bg-rose-100 text-rose-600'
          }`}
        >
          {isForbidden ? <Lock size={32} /> : isUnauthorized ? <LogIn size={32} /> : <ShieldAlert size={32} />}
        </div>
        <h2 className="text-xl font-bold text-slate-800">
          {isForbidden
            ? (isVi ? 'Không có quyền truy cập ca quét' : 'Access Restricted')
            : isUnauthorized
              ? (isVi ? 'Yêu cầu đăng nhập' : 'Authentication Required')
              : (isVi ? 'Không tìm thấy dữ liệu' : 'Data Not Found')}
        </h2>
        <p className="mt-3 text-sm leading-6 text-slate-600 bg-slate-50 rounded-xl p-4 border border-slate-200/80">
          {error}
        </p>

        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          <Link to="/app/history" className="btn-secondary inline-flex items-center gap-1.5 text-xs">
            <ArrowLeft size={16} /> {isVi ? 'Quay lại Lịch sử' : 'Back to History'}
          </Link>
          {(isForbidden || isUnauthorized) && (
            <Link to="/login" className="btn-primary inline-flex items-center gap-1.5 text-xs">
              <LogIn size={16} /> {isForbidden ? (isVi ? 'Đổi tài khoản đăng nhập' : 'Switch Account') : (isVi ? 'Đăng nhập ngay' : 'Log in')}
            </Link>
          )}
        </div>
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

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
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

              {/* So sánh đối chiếu 2 tầng (nếu có model_results) */}
              {scan.model_results && scan.model_results.length > 1 && (
                <div className="rounded-2xl border border-slate-200/80 bg-slate-50/70 p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Layers size={16} className="text-leaf-600" />
                      <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                        {isVi ? 'Đối chiếu kiểm định 2 tầng' : 'Two-Tier Model Verification'}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
                    {scan.model_results.map((m, idx) => {
                      const isPrimary = (scan.model_version && m.version_name.includes(scan.model_version)) || idx === 0
                      const mConf = toPercent(m.confidence)
                      return (
                        <div
                          key={idx}
                          className={`rounded-xl p-2.5 border transition-all ${
                            isPrimary
                              ? 'bg-white border-leaf-400 shadow-xs'
                              : 'bg-white/60 border-slate-200'
                          }`}
                        >
                          <div className="flex items-center justify-between text-[11px] mb-1">
                            <span className="font-semibold text-slate-700 truncate" title={m.version_name}>
                              {m.version_name.replace(/_f_v\d+$/, '').replace(/_/g, ' ')}
                            </span>
                            {isPrimary && (
                              <span className="text-[9px] font-bold uppercase tracking-wider text-leaf-700 bg-leaf-50 px-1 rounded">
                                {isVi ? 'Chính' : 'Primary'}
                              </span>
                            )}
                          </div>
                          <div className="flex items-baseline justify-between">
                            <span className="text-base font-black text-slate-800">{mConf.toFixed(1)}%</span>
                            <span className="text-[10px] text-slate-400 truncate max-w-[100px]" title={m.predicted_label}>
                              {friendlyLabel(m.predicted_label)}
                            </span>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

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

        {/* Khối hiển thị ảnh gốc và Grad-CAM */}
        <div className="space-y-6">
          {/* 1. Ảnh lá cây chụp gốc */}
          <div className="card p-5">
            <h4 className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
              <ImageIcon size={15} className="text-leaf-600" />
              {isVi ? 'Ảnh chụp lá cây gốc' : 'Original Leaf Image'}
            </h4>
            <div className="relative aspect-square w-full overflow-hidden rounded-2xl bg-slate-900 flex items-center justify-center">
              {imageLoading ? (
                <div className="flex flex-col items-center gap-2 text-slate-400 text-xs">
                  <LoaderCircle className="animate-spin text-leaf-500" size={24} />
                  <span>{isVi ? 'Đang tải ảnh...' : 'Loading image...'}</span>
                </div>
              ) : imageUrl ? (
                <img src={imageUrl} alt="Original Scan Leaf" className="h-full w-full object-contain" />
              ) : (
                <p className="text-xs text-slate-400">
                  {isVi ? 'Không thể tải ảnh gốc' : 'Unable to load original image'}
                </p>
              )}
            </div>
          </div>

          {/* 2. Bản đồ nhiệt Grad-CAM */}
          <div className="card p-5">
            <h4 className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
              <Sparkles size={15} className="text-amber-500" />
              {isVi ? 'Bản đồ nhiệt Grad-CAM' : 'Grad-CAM Heatmap'}
            </h4>
            <div className="relative aspect-square w-full overflow-hidden rounded-2xl bg-slate-900 flex items-center justify-center">
              {gradcamLoading ? (
                <div className="flex flex-col items-center gap-2 text-slate-400 text-xs">
                  <LoaderCircle className="animate-spin text-amber-500" size={24} />
                  <span>{isVi ? 'Đang tạo heatmap mô hình...' : 'Generating heatmap...'}</span>
                </div>
              ) : gradcamUrl ? (
                <img src={gradcamUrl} alt="Grad-CAM" className="h-full w-full object-contain" />
              ) : (
                <div className="flex h-full w-full flex-col items-center justify-center p-6 text-center text-slate-400">
                  <Sparkles size={28} className="text-amber-500/70" />
                  <p className="mt-2 text-xs">
                    {isValidLeaf
                      ? (isVi ? 'Chưa tạo hoặc không khả dụng cho ca quét này.' : 'Grad-CAM not available.')
                      : (isVi ? 'Không hỗ trợ Grad-CAM cho ảnh OOD.' : 'Grad-CAM unsupported for OOD.')}
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
