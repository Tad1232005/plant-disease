import { ChevronDown, ChevronUp, Cpu, History, Loader2, LogIn, ScanLine, ShieldCheck, Sliders, Sparkles } from 'lucide-react'
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
    id: result.id || Date.now(),
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
  const [farms, setFarms] = useState(() => loadCollection('plantcare_farms', initialFarms))
  const [capabilities, setCapabilities] = useState(null)
  const [mode, setMode] = useState('auto')
  const [strategy, setStrategy] = useState('ensemble')
  const [modelType, setModelType] = useState('efficientnet_b0')
  const [showModelConfig, setShowModelConfig] = useState(false)

  useEffect(() => {
    let active = true
    getPredictCapabilities()
      .then((data) => {
        if (!active || !data) return
        setCapabilities(data)
        if (data.default_strategy) setStrategy(data.default_strategy)
      })
      .catch(() => {
        if (active) {
          setCapabilities({
            role: user?.role || 'guest',
            default_mode: user?.role === 'technician' ? 'advanced' : (user?.role ? 'standard' : 'basic'),
            allowed_modes: user?.role === 'technician' ? ['basic', 'standard', 'advanced'] : (user?.role ? ['basic', 'standard'] : ['basic']),
            allowed_model_types: ['efficientnet_b0', 'mobilenet_v2', 'resnet50'],
            supported_strategies: ['ensemble', 'single'],
          })
        }
      })
    return () => { active = false }
  }, [user?.role])

  useEffect(() => {
    let active = true
    const fetchFarms = user?.role === 'manager' ? farmsApi.list : farmsApi.myFarms
    fetchFarms()
      .catch(() => farmsApi.list())
      .then((data) => {
        if (!active || !Array.isArray(data)) return
        if (data.length > 0) {
          setFarms(data)
          saveCollection('plantcare_farms', data)
        }
      })
      .catch(() => {})
    return () => { active = false }
  }, [user?.role])

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
      const history = loadCollection(HISTORY_KEY, [])
      saveCollection(HISTORY_KEY, [row, ...history].slice(0, 100))
    }
    setResult(nextResult)
    if (nextResult.gradcam_url) setExplanation({ gradcam_url: nextResult.gradcam_url })
    setResultMeta({ farmName, date: row.date })
  }

  async function analyze() {
    if (!file) { setValidationError(language === 'vi' ? 'Vui lòng chọn ảnh lá cây trước khi phân tích.' : 'Choose a leaf image before analyzing.'); return }
    setLoading(true); setError(''); setResult(null); setResultMeta(null)
    try {
      const options = {
        farmId,
        mode: mode !== 'auto' ? mode : undefined,
        strategy,
        modelType: strategy === 'single' ? modelType : undefined,
      }
      showResult(await predictImage(file, options))
    } catch (requestError) {
      if (!requestError?.response) {
        showResult({
          ...DEMO_RESULT,
          id: Date.now(),
          filename: file.name,
          model_version: strategy === 'single' ? modelType : `ensemble-${mode}`,
          inference_strategy: strategy,
          inference_mode: mode,
        })
      } else {
        setError(getApiError(requestError, language === 'vi' ? 'Không thể phân tích ảnh.' : 'Unable to analyze the image.'))
      }
    } finally {
      setLoading(false)
    }
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
          <label><span className="mb-2 block text-xs font-bold uppercase tracking-wider text-leaf-700 dark:text-leaf-300">{t('scan.farm')}</span><select className="input-control max-w-md" value={farmId} onChange={(event) => setFarmId(event.target.value)}><option value="">{t('scan.optional')}</option>{farms.map((farm) => <option key={farm.id} value={farm.id}>{farm.name}</option>)}</select></label>
          <div className="flex items-center gap-2 text-xs text-leaf-800 dark:text-leaf-200"><ShieldCheck size={17} /><span>{t('scan.privacy')}</span></div>
        </div>
      )}

      {/* Cấu hình Mô hình AI & Chế độ suy luận */}
      <div className="mb-6 rounded-3xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900 sm:p-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <span className="grid h-10 w-10 place-items-center rounded-2xl bg-leaf-50 text-leaf-700 dark:bg-leaf-950/50 dark:text-leaf-300">
              <Cpu size={20} />
            </span>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100">
                  {language === 'vi' ? 'Cấu hình Mô hình AI & Suy luận' : 'AI Model & Inference Settings'}
                </h3>
                <span className="rounded-full bg-leaf-100 px-2.5 py-0.5 text-[11px] font-extrabold text-leaf-800 dark:bg-leaf-900/60 dark:text-leaf-300">
                  {strategy === 'ensemble' ? 'Ensemble' : modelType}
                </span>
              </div>
              <p className="mt-0.5 text-xs text-slate-400">
                {strategy === 'ensemble'
                  ? (language === 'vi' ? `Chế độ: ${mode.toUpperCase()} (Đa mô hình soft-voting + OOD)` : `Mode: ${mode.toUpperCase()} (Multi-model soft-voting + OOD)`)
                  : (language === 'vi' ? `Đơn mô hình: ${modelType}` : `Single model: ${modelType}`)}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => setShowModelConfig((prev) => !prev)}
            className="inline-flex items-center gap-1.5 self-start rounded-xl border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:border-leaf-300 hover:bg-leaf-50 hover:text-leaf-700 dark:border-slate-700 dark:text-slate-300 sm:self-auto"
          >
            <Sliders size={14} />
            {showModelConfig ? (language === 'vi' ? 'Thu gọn' : 'Collapse') : (language === 'vi' ? 'Tùy chỉnh model' : 'Configure')}
            {showModelConfig ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        </div>

        {showModelConfig && (
          <div className="mt-4 grid gap-4 border-t border-slate-100 pt-4 dark:border-slate-800 sm:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                {language === 'vi' ? 'Chiến lược suy luận (Strategy)' : 'Inference Strategy'}
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setStrategy('ensemble')}
                  className={`rounded-xl border p-2.5 text-left text-xs font-bold transition ${
                    strategy === 'ensemble'
                      ? 'border-leaf-600 bg-leaf-50 text-leaf-800 dark:border-leaf-500 dark:bg-leaf-950/60 dark:text-leaf-200'
                      : 'border-slate-200 text-slate-600 hover:bg-slate-50 dark:border-slate-800 dark:text-slate-400'
                  }`}
                >
                  <span className="block font-extrabold">Ensemble</span>
                  <span className="text-[10px] font-normal text-slate-400">{language === 'vi' ? 'Đa mô hình (Khuyến nghị)' : 'Multi-model'}</span>
                </button>
                <button
                  type="button"
                  onClick={() => setStrategy('single')}
                  className={`rounded-xl border p-2.5 text-left text-xs font-bold transition ${
                    strategy === 'single'
                      ? 'border-leaf-600 bg-leaf-50 text-leaf-800 dark:border-leaf-500 dark:bg-leaf-950/60 dark:text-leaf-200'
                      : 'border-slate-200 text-slate-600 hover:bg-slate-50 dark:border-slate-800 dark:text-slate-400'
                  }`}
                >
                  <span className="block font-extrabold">Single Model</span>
                  <span className="text-[10px] font-normal text-slate-400">{language === 'vi' ? 'Đơn mô hình cụ thể' : 'Specific model'}</span>
                </button>
              </div>
            </div>

            {strategy === 'ensemble' ? (
              <div>
                <label className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  {language === 'vi' ? 'Cấp độ Ensemble (Mode)' : 'Ensemble Mode'}
                </label>
                <select
                  className="input-control"
                  value={mode}
                  onChange={(e) => setMode(e.target.value)}
                >
                  <option value="auto">{language === 'vi' ? 'Tự động (Auto - Tối ưu theo quyền)' : 'Auto (Optimized by role)'}</option>
                  {(capabilities?.allowed_modes || ['basic', 'standard']).includes('basic') && (
                    <option value="basic">Basic (1 model: EfficientNet-B0)</option>
                  )}
                  {(capabilities?.allowed_modes || ['standard']).includes('standard') && (
                    <option value="standard">Standard (2 models: EfficientNet + MobileNetV2)</option>
                  )}
                  {(capabilities?.allowed_modes || []).includes('advanced') && (
                    <option value="advanced">Advanced (3 models: + ResNet50)</option>
                  )}
                </select>
              </div>
            ) : (
              <div>
                <label className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  {language === 'vi' ? 'Chọn mô hình mạng (Model Architecture)' : 'Select Model Architecture'}
                </label>
                <select
                  className="input-control"
                  value={modelType}
                  onChange={(e) => setModelType(e.target.value)}
                >
                  {(capabilities?.allowed_model_types || ['efficientnet_b0', 'mobilenet_v2']).includes('efficientnet_b0') && (
                    <option value="efficientnet_b0">EfficientNet-B0 (Độ chính xác cao)</option>
                  )}
                  {(capabilities?.allowed_model_types || ['mobilenet_v2']).includes('mobilenet_v2') && (
                    <option value="mobilenet_v2">MobileNetV2 (Gốc nhẹ, tốc độ cao)</option>
                  )}
                  {(capabilities?.allowed_model_types || []).includes('resnet50') && (
                    <option value="resnet50">ResNet50 (Mạng sâu 50 tầng)</option>
                  )}
                </select>
              </div>
            )}
          </div>
        )}
      </div>
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
