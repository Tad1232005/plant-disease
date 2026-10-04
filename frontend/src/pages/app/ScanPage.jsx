import { History, LogIn, ScanLine, ShieldCheck } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getApiError } from '../../api/client.js'
import { explainPrediction, predictImage } from '../../api/predict.js'
import ResultCard from '../../components/ResultCard.jsx'
import UploadImage from '../../components/UploadImage.jsx'
import PageHeader from '../../components/common/PageHeader.jsx'
import { initialFarms } from '../../data/demoData.js'
import { useAuth } from '../../contexts/AuthContext.jsx'
import { usePreferences } from '../../contexts/PreferencesContext.jsx'
import { loadCollection, saveCollection } from '../../utils/storage.js'

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
  const [error, setError] = useState('')
  const [farmId, setFarmId] = useState('')
  const farms = loadCollection('plantcare_farms', initialFarms)

  useEffect(() => () => { if (previewUrl) URL.revokeObjectURL(previewUrl) }, [previewUrl])

  function handleFileSelect(nextFile) {
    setValidationError(''); setError(''); setResult(null); setResultMeta(null); setExplanation(null)
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(nextFile.type)) { setValidationError(language === 'vi' ? 'Ảnh không hợp lệ. Vui lòng chọn file JPG, PNG hoặc WEBP.' : 'Invalid image. Choose a JPG, PNG, or WEBP file.'); return }
    if (nextFile.size > 8 * 1024 * 1024) { setValidationError(language === 'vi' ? 'Dung lượng ảnh vượt quá 8 MB.' : 'The image exceeds the 8 MB limit.'); return }
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    setFile(nextFile); setPreviewUrl(URL.createObjectURL(nextFile))
  }

  function clearFile() {
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    setFile(null); setPreviewUrl(''); setResult(null); setResultMeta(null); setExplanation(null); setError(''); setValidationError('')
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
    try { showResult(await predictImage(file, { farmId })) }
    catch (requestError) { setError(getApiError(requestError, language === 'vi' ? 'Không thể phân tích ảnh.' : 'Unable to analyze the image.')) }
    finally { setLoading(false) }
  }

  async function explain() {
    if (!file) return
    setExplainLoading(true)
    try { setExplanation(await explainPrediction(file)) }
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
      <div className="grid items-start gap-6 xl:grid-cols-[1.15fr_.85fr]">
        <div><UploadImage onFileSelect={handleFileSelect} previewUrl={previewUrl} fileName={file?.name} validationError={validationError} onClear={clearFile} /><button className="btn-primary mt-4 w-full !py-3.5" disabled={!file || loading} onClick={analyze}><ScanLine size={19} />{loading ? t('scan.analyzing') : t('scan.analyze')}</button></div>
        <ResultCard result={result} loading={loading} error={error} meta={resultMeta} onReset={clearFile} onUseDemo={() => { setError(''); showResult(DEMO_RESULT) }} previewUrl={previewUrl} showGradCam={!guestMode && user?.role === 'technician'} explanation={explanation} explainLoading={explainLoading} onExplain={explain} />
      </div>
    </div>
  )
}
