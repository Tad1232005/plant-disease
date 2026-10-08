import { History, LogIn, ScanLine, ShieldCheck, Sparkles, Loader2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getApiError } from '../../api/client.js'
import { explainPrediction, getPredictCapabilities, predictImage } from '../../api/predict.js'
import { farmsApi } from '../../api/farms.js'
import ResultCard from '../../components/ResultCard.jsx'
import UploadImage from '../../components/UploadImage.jsx'
import PageHeader from '../../components/common/PageHeader.jsx'
import { initialFarms } from '../../data/demoData.js'
import { useAuth } from '../../contexts/AuthContext.jsx'
import { usePreferences } from '../../contexts/PreferencesContext.jsx'
import { loadCollection, saveCollection } from '../../utils/storage.js'
import { compressImage, formatBytes } from '../../utils/imageCompressor.js'

const HISTORY_KEY = 'plantcare_scan_history'
const MODEL_META = {
  efficientnet_b0: {
    name: 'EfficientNet-B0',
    badge: 'Khuyên dùng',
    badgeEn: 'Recommended',
    desc: 'Cân bằng & Chính xác',
    descEn: 'Balanced & Accurate',
  },
  mobilenet_v2: {
    name: 'MobileNet-V2',
    badge: 'Nhanh',
    badgeEn: 'Fast',
    desc: 'Gọn nhẹ, tối ưu di động',
    descEn: 'Lightweight & Optimized',
  },
  resnet50: {
    name: 'ResNet-50',
    badge: 'Chuyên sâu',
    badgeEn: 'Deep',
    desc: 'Độ trích xuất cao (Tech/Admin)',
    descEn: 'High capacity (Tech/Admin)',
  },
}
const DEMO_RESULT = {
  label: 'tomato_late_blight', confidence: 0.948, is_valid_leaf: true, ood_score: 0.08,
  treatment: 'Loại bỏ lá bị bệnh, giữ vườn thông thoáng và tham khảo kỹ thuật viên trước khi xử lý.',
  top_k: [
    { label: 'tomato_late_blight', confidence: 0.948, rank: 1 },
    { label: 'tomato_early_blight', confidence: 0.034, rank: 2 },
    { label: 'tomato_healthy', confidence: 0.018, rank: 3 },
  ],
}

function toPercent(value) {
  const number = Number(value || 0)
  return number <= 1 ? number * 100 : number
}

function createHistoryRow(result, farmName) {
  const confidence = toPercent(result.confidence)
  const isHealthy = String(result.label || '').toLowerCase().includes('healthy')
  const isValidLeaf = result.is_valid_leaf ?? result.isValidLeaf ?? true
  return {
    id: result.scan_id || result.id || Date.now(),
    date: new Intl.DateTimeFormat('vi-VN', { dateStyle: 'short', timeStyle: 'short' }).format(new Date()),
    farm: farmName,
    result: isValidLeaf ? result.label : 'Ảnh ngoài miền dữ liệu',
    confidence: Number(confidence.toFixed(1)),
    severity: isHealthy ? 'low' : 'medium',
    top_k: result.top_k || [],
    is_valid_leaf: isValidLeaf,
    ood_score: result.ood_score,
    treatment: result.treatment || result.recommendation || (isValidLeaf ? 'Theo dõi cây và liên hệ kỹ thuật viên nếu triệu chứng lan rộng.' : 'Chụp lại một lá cây rõ nét dưới ánh sáng tự nhiên.'),
    gradcam_url: result.gradcam_url,
  }
}

export default function ScanPage({ guestMode = false }) {
  const { user } = useAuth()
  const { language, t } = usePreferences()
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [validationError, setValidationError] = useState('')
  const [result, setResult] = useState(null)
  const [resultMeta, setResultMeta] = useState(null)
  const [loading, setLoading] = useState(false)
  const [explanation, setExplanation] = useState(null)
  const [explainLoading, setExplainLoading] = useState(false)
  const [compressing, setCompressing] = useState(false)
  const [compressionRatio, setCompressionRatio] = useState(null)
  const [error, setError] = useState('')
  const [farmId, setFarmId] = useState('')
  const [farms, setFarms] = useState([])
  const [selectedModel, setSelectedModel] = useState('efficientnet_b0')
  const [availableModels, setAvailableModels] = useState(['efficientnet_b0'])

  useEffect(() => {
    if (guestMode) return
    let active = true
    getPredictCapabilities()
      .then((data) => {
        if (!active) return
        if (Array.isArray(data?.allowed_model_types) && data.allowed_model_types.length > 0) {
          setAvailableModels(data.allowed_model_types)
          if (!data.allowed_model_types.includes(selectedModel)) {
            setSelectedModel(data.allowed_model_types[0])
          }
        }
      })
      .catch(() => {
        if (['technician', 'admin'].includes(user?.role)) {
          setAvailableModels(['efficientnet_b0', 'mobilenet_v2', 'resnet50'])
        } else {
          setAvailableModels(['efficientnet_b0', 'mobilenet_v2'])
        }
      })
    return () => { active = false }
  }, [guestMode, user?.role])

  useEffect(() => {
    if (guestMode) {
      setFarms([])
      return
    }
    let active = true
    const fetchFarms = user?.role === 'manager' ? farmsApi.list : farmsApi.myFarms
    fetchFarms()
      .then((data) => {
        if (!active || !Array.isArray(data)) return
        setFarms(data)
        if (data.length > 0) {
          saveCollection('plantcare_farms', data)
        }
      })
      .catch(() => {
        if (active) setFarms([])
      })
    return () => { active = false }
  }, [guestMode, user?.role])

  useEffect(() => () => { if (previewUrl) URL.revokeObjectURL(previewUrl) }, [previewUrl])

  async function handleFileSelect(nextFile) {
    setValidationError(''); setError(''); setResult(null); setResultMeta(null); setExplanation(null)
    if (!nextFile) return
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(nextFile.type) && !nextFile.type.startsWith('image/')) {
      setValidationError(language === 'vi' ? 'Ảnh không hợp lệ. Vui lòng chọn file JPG, PNG hoặc WEBP.' : 'Invalid image. Choose a JPG, PNG, or WEBP file.')
      return
    }
    if (nextFile.size > 35 * 1024 * 1024) {
      setValidationError(language === 'vi' ? 'Dung lượng ảnh vượt quá 35 MB.' : 'The image exceeds the 35 MB limit.')
      return
    }

    setCompressing(true)
    try {
      const { file: optimizedFile, originalSize, compressedSize, wasCompressed } = await compressImage(nextFile, {
        maxDimension: 1280,
        quality: 0.82
      })

      if (previewUrl) URL.revokeObjectURL(previewUrl)
      setFile(optimizedFile)
      setPreviewUrl(URL.createObjectURL(optimizedFile))
      if (wasCompressed) {
        setCompressionRatio({
          original: formatBytes(originalSize),
          compressed: formatBytes(compressedSize),
          savedPercent: Math.round(((originalSize - compressedSize) / originalSize) * 100)
        })
      } else {
        setCompressionRatio(null)
      }
    } catch {
      if (previewUrl) URL.revokeObjectURL(previewUrl)
      setFile(nextFile)
      setPreviewUrl(URL.createObjectURL(nextFile))
      setCompressionRatio(null)
    } finally {
      setCompressing(false)
    }
  }

  function clearFile() {
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    setFile(null); setPreviewUrl(''); setResult(null); setResultMeta(null); setExplanation(null); setError(''); setValidationError(''); setCompressionRatio(null); setCompressing(false)
  }

  function showResult(nextResult) {
    const farm = farms.find((item) => String(item.id) === String(farmId))
    const farmName = guestMode ? t('landing.guestTitle') : farm?.name || t('scan.optional')
    const row = createHistoryRow(nextResult, farmName)
    if (!guestMode) {
      const historyKey = user?.id ? `plantcare_scan_history_${user.id}` : 'plantcare_scan_history'
      const history = loadCollection(historyKey, [])
      saveCollection(historyKey, [row, ...history].slice(0, 100))
    }
    setResult(nextResult)
    if (nextResult.gradcam_url) setExplanation({ gradcam_url: nextResult.gradcam_url })
    setResultMeta({ farmName, date: row.date })
  }

  async function analyze() {
    if (!file) { setValidationError(language === 'vi' ? 'Vui lòng chọn ảnh lá cây trước khi phân tích.' : 'Choose a leaf image before analyzing.'); return }
    setLoading(true); setError(''); setResult(null); setResultMeta(null)
    const payload = { farmId }
    if (!guestMode && selectedModel) {
      payload.primaryModel = selectedModel
    }
    try { showResult(await predictImage(file, payload)) }
    catch (requestError) { setError(getApiError(requestError, language === 'vi' ? 'Không thể phân tích ảnh.' : 'Unable to analyze the image.')) }
    finally { setLoading(false) }
  }

  async function explain() {
    if (!file) return
    setExplainLoading(true)
    try { setExplanation(await explainPrediction(file, result?.scan_id)) }
    catch { setExplanation({ demo: true }) }
    finally { setExplainLoading(false) }
  }

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader eyebrow={guestMode ? t('guest.badge') : t('scan.eyebrow')} title={t('scan.title')} description={guestMode ? t('scan.guestDescription') : t('scan.userDescription')} />
      {guestMode ? (
        <div className="mb-6 flex flex-col gap-3 rounded-3xl border border-sky-200 bg-sky-50 p-4 text-sm text-sky-900 dark:border-sky-900 dark:bg-sky-950/40 dark:text-sky-100 sm:flex-row sm:items-center sm:justify-between sm:p-5">
          <div className="flex items-center gap-3"><History className="shrink-0 text-sky-600" size={20} /><span><strong>{t('guest.noHistory')}.</strong> {t('scan.guestDescription')}</span></div>
          <Link to="/login" className="btn-secondary shrink-0"><LogIn size={16} />{t('guest.saveHistory')}</Link>
        </div>
      ) : (
        <div className="mb-6 grid gap-4 rounded-3xl border border-leaf-100 bg-leaf-50/60 p-4 dark:border-leaf-900 dark:bg-leaf-950/30 sm:grid-cols-[1fr_auto] sm:items-center sm:p-5">
          {farms.length > 0 ? (
            <label>
              <span className="mb-2 block text-xs font-bold uppercase tracking-wider text-leaf-700 dark:text-leaf-300">
                {t('scan.farm')}
              </span>
              <select className="input-control max-w-md" value={farmId} onChange={(event) => setFarmId(event.target.value)}>
                <option value="">{t('scan.optional')}</option>
                {farms.map((farm) => (
                  <option key={farm.id} value={farm.id}>{farm.name}</option>
                ))}
              </select>
            </label>
          ) : (
            <div>
              <span className="mb-1 block text-xs font-bold uppercase tracking-wider text-leaf-700 dark:text-leaf-300">
                {t('scan.farm')}
              </span>
              <p className="text-xs text-slate-500">
                {user?.role === 'manager'
                  ? (language === 'vi' ? 'Bạn chưa tạo khu vực nào trong Quản lý trang trại.' : 'No areas created yet in Farm Management.')
                  : user?.created_by
                    ? (language === 'vi' ? 'Chưa được phân công khu vực (liên hệ Quản lý để được gán vào trang trại).' : 'Not assigned to any area yet (contact your manager).')
                    : (language === 'vi' ? 'Vườn cá nhân (Chẩn đoán được lưu vào hồ sơ cá nhân của bạn).' : 'Personal garden (Scans are saved to your personal history).')}
              </p>
            </div>
          )}
          <div className="flex items-center gap-2 text-xs text-leaf-800 dark:text-leaf-200"><ShieldCheck size={17} /><span>{t('scan.privacy')}</span></div>
        </div>
      )}
      <div className="grid items-start gap-6 xl:grid-cols-[1.15fr_.85fr]">
        <div>
          <UploadImage onFileSelect={handleFileSelect} previewUrl={previewUrl} fileName={file?.name} validationError={validationError} onClear={clearFile} />
          
          {compressionRatio && (
            <div className="mt-3 flex items-center gap-2 rounded-2xl border border-emerald-200 bg-emerald-50/90 px-4 py-2.5 text-xs font-medium text-emerald-800 shadow-sm dark:border-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300">
              <Sparkles size={16} className="shrink-0 text-emerald-600 dark:text-emerald-400" />
              <span>
                {language === 'vi'
                  ? `Đã tối ưu hóa ảnh: ${compressionRatio.original} → ${compressionRatio.compressed} (giảm ${compressionRatio.savedPercent}%, tải lên nhanh hơn)`
                  : `Image optimized: ${compressionRatio.original} → ${compressionRatio.compressed} (saved ${compressionRatio.savedPercent}%, faster upload)`}
              </span>
            </div>
          )}

          {!guestMode && (
            <div className="mt-4 rounded-3xl border border-leaf-100 bg-white/85 p-4 shadow-sm dark:border-leaf-900/60 dark:bg-slate-900/80">
              <div className="mb-2.5 flex items-center justify-between">
                <label className="text-xs font-bold uppercase tracking-wider text-leaf-700 dark:text-leaf-300">
                  {language === 'vi' ? 'Mô hình chẩn đoán chính' : 'Primary Diagnostic Model'}
                </label>
                <span className="text-[11px] font-medium text-leaf-600 dark:text-leaf-400">
                  {language === 'vi' ? 'Kiểm định 2 tầng' : 'Two-tier ensemble'}
                </span>
              </div>
              <div className="grid gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
                {availableModels.map((mType) => {
                  const meta = MODEL_META[mType] || { name: mType, badge: '', desc: '' }
                  const isSelected = selectedModel === mType
                  return (
                    <button
                      key={mType}
                      type="button"
                      onClick={() => setSelectedModel(mType)}
                      className={`flex flex-col items-start rounded-2xl border p-3 text-left transition-all ${
                        isSelected
                          ? 'border-leaf-500 bg-leaf-50/90 shadow-sm ring-2 ring-leaf-500/30 dark:border-leaf-500 dark:bg-leaf-950/50'
                          : 'border-slate-200 bg-slate-50/70 hover:border-slate-300 dark:border-slate-800 dark:bg-slate-800/40'
                      }`}
                    >
                      <div className="flex w-full items-center justify-between gap-1">
                        <span className={`text-xs font-bold ${isSelected ? 'text-leaf-800 dark:text-leaf-200' : 'text-slate-700 dark:text-slate-300'}`}>
                          {meta.name}
                        </span>
                        {meta.badge && (
                          <span className={`shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-semibold ${
                            isSelected ? 'bg-leaf-200/80 text-leaf-800 dark:bg-leaf-900 dark:text-leaf-200' : 'bg-slate-200/70 text-slate-600 dark:bg-slate-700 dark:text-slate-300'
                          }`}>
                            {language === 'vi' ? meta.badge : meta.badgeEn}
                          </span>
                        )}
                      </div>
                      <span className="mt-1 text-[11px] leading-tight text-slate-500 dark:text-slate-400">
                        {language === 'vi' ? meta.desc : meta.descEn}
                      </span>
                    </button>
                  )
                })}
              </div>
              <p className="mt-2 text-[11px] text-slate-400 dark:text-slate-500">
                {language === 'vi'
                  ? 'Mô hình đã chọn chạy ở Tầng 1 và được kiểm tra chéo ở Tầng 2 với các mô hình phụ trợ.'
                  : 'Selected model runs at Stage 1 and is cross-verified at Stage 2 with auxiliary models.'}
              </p>
            </div>
          )}

          <button className="btn-primary mt-4 w-full !py-3.5" disabled={!file || loading || compressing} onClick={analyze}>
            {compressing ? (
              <><Loader2 className="animate-spin" size={19} />{language === 'vi' ? 'Đang tối ưu dung lượng...' : 'Optimizing image...'}</>
            ) : loading ? (
              <><ScanLine size={19} />{t('scan.analyzing')}</>
            ) : (
              <><ScanLine size={19} />{t('scan.analyze')}</>
            )}
          </button>
        </div>
        <ResultCard result={result} loading={loading} error={error} meta={resultMeta} onReset={clearFile} onUseDemo={() => { setError(''); showResult(DEMO_RESULT) }} previewUrl={previewUrl} showGradCam={!guestMode && user?.role === 'technician'} explanation={explanation} explainLoading={explainLoading} onExplain={explain} />
      </div>
    </div>
  )
}
