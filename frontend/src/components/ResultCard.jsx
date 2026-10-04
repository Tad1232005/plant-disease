import { AlertCircle, CalendarClock, CheckCircle2, Leaf, LoaderCircle, MapPin, RotateCcw, ShieldAlert, ShieldCheck, Sparkles } from 'lucide-react'
import GradCamPanel from './GradCamPanel.jsx'
import { usePreferences } from '../contexts/PreferencesContext.jsx'

function friendlyLabel(label = '') {
  return String(label).replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function toPercent(value) {
  const number = Number(value || 0)
  return number <= 1 ? number * 100 : number
}

const treatmentByLabel = {
  tomato_late_blight: 'Loại bỏ lá bị bệnh, giữ vườn thông thoáng và tham khảo kỹ thuật viên trước khi xử lý.',
  tomato_early_blight: 'Vệ sinh tàn dư cây bệnh, luân canh và cân đối dinh dưỡng cho cây.',
  corn_common_rust: 'Theo dõi mật độ bệnh, ưu tiên giống kháng và xử lý theo khuyến cáo địa phương.',
}

export default function ResultCard({ result, loading, error, onUseDemo, meta, onReset, previewUrl, showGradCam = false, explanation, explainLoading, onExplain }) {
  const { language, t } = usePreferences()
  if (loading) {
    return <div className="card flex min-h-72 flex-col items-center justify-center p-8 text-center"><span className="grid h-16 w-16 place-items-center rounded-3xl bg-leaf-50 text-leaf-700"><LoaderCircle className="animate-spin" size={30} /></span><h3 className="mt-5 text-lg font-extrabold text-slate-900">{t('result.loadingTitle')}</h3><p className="mt-2 text-sm text-slate-500">{t('result.loadingText')}</p></div>
  }

  if (error) {
    return <div className="card min-h-72 p-6"><span className="grid h-12 w-12 place-items-center rounded-2xl bg-rose-50 text-rose-600"><AlertCircle size={23} /></span><h3 className="mt-5 text-lg font-extrabold text-slate-900">{t('result.failed')}</h3><p className="mt-2 text-sm leading-6 text-rose-700">{error}</p>{onUseDemo && <button className="btn-secondary mt-5" onClick={onUseDemo}><Sparkles size={16} />{t('result.demo')}</button>}</div>
  }

  if (!result) {
    return <div className="card flex min-h-72 flex-col items-center justify-center p-8 text-center"><span className="grid h-16 w-16 place-items-center rounded-3xl bg-slate-100 text-slate-400"><ShieldCheck size={28} /></span><h3 className="mt-5 font-extrabold text-slate-800">{t('result.waitTitle')}</h3><p className="mt-2 max-w-sm text-sm leading-6 text-slate-500">{t('result.waitText')}</p></div>
  }

  const confidence = toPercent(result.confidence)
  const isValidLeaf = result.is_valid_leaf ?? result.isValidLeaf ?? true
  const topK = result.top_k?.length ? result.top_k : [{ label: result.label, confidence: result.confidence, rank: 1 }]
  const treatment = result.treatment || result.recommendation || treatmentByLabel[result.label] || (language === 'vi'
    ? (isValidLeaf ? 'Theo dõi cây trong 3–5 ngày và liên hệ kỹ thuật viên nếu triệu chứng lan rộng.' : 'Chụp lại một lá cây rõ nét, đủ sáng và chiếm phần lớn khung hình.')
    : (isValidLeaf ? 'Monitor the plant for 3–5 days and contact a technician if symptoms spread.' : 'Retake a clear, well-lit photo with one leaf filling most of the frame.'))

  return (
    <div className="card overflow-hidden">
      <div className={`bg-gradient-to-r p-6 text-white ${isValidLeaf ? 'from-leaf-700 to-leaf-600' : 'from-amber-700 to-orange-600'}`}>
        <div className="flex items-start justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-wider text-white/65">{isValidLeaf ? t('result.prediction') : t('result.ood')}</p><h3 className="mt-2 text-2xl font-black">{isValidLeaf ? friendlyLabel(result.label) : t('result.invalid')}</h3></div><span className="grid h-12 w-12 place-items-center rounded-2xl bg-white/15">{isValidLeaf ? <CheckCircle2 size={24} /> : <ShieldAlert size={24} />}</span></div>
        <div className="mt-6 flex items-end justify-between"><span className="text-sm text-white/70">{t('result.confidence')}</span><strong className="text-3xl">{confidence.toFixed(1)}%</strong></div>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-black/15"><div className="h-full rounded-full bg-white transition-all" style={{ width: `${Math.min(confidence, 100)}%` }} /></div>
        {result.ood_score !== undefined && <p className="mt-3 text-xs text-white/70">OOD score: {toPercent(result.ood_score).toFixed(1)}%</p>}
      </div>
      <div className="p-6">
        {meta && <div className="mb-6 grid gap-3 rounded-2xl bg-slate-50 p-4 text-xs text-slate-600 sm:grid-cols-2"><span className="flex items-center gap-2"><MapPin size={15} className="text-leaf-600" />{meta.farmName}</span><span className="flex items-center gap-2"><CalendarClock size={15} className="text-leaf-600" />{meta.date}</span></div>}
        {!isValidLeaf && <div className="mb-5 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-900"><strong>{t('result.invalidTitle')}</strong> {t('result.invalidText')}</div>}
        {isValidLeaf && <><h4 className="text-sm font-extrabold text-slate-800">{t('result.top')}</h4><div className="mt-4 space-y-3">{topK.slice(0, 3).map((item, index) => { const percent = toPercent(item.confidence); return <div key={`${item.label}-${index}`}><div className="mb-1.5 flex items-center justify-between gap-3 text-xs"><span className="truncate font-semibold text-slate-600">{index + 1}. {friendlyLabel(item.label)}</span><span className="font-bold text-slate-700">{percent.toFixed(1)}%</span></div><div className="h-1.5 overflow-hidden rounded-full bg-slate-100"><div className={`h-full rounded-full ${index === 0 ? 'bg-leaf-500' : 'bg-slate-300'}`} style={{ width: `${Math.min(percent, 100)}%` }} /></div></div> })}</div></>}
        <div className={`mt-6 rounded-2xl p-4 ${isValidLeaf ? 'bg-emerald-50' : 'bg-amber-50'}`}><div className="flex items-center gap-2"><Leaf size={16} className={isValidLeaf ? 'text-emerald-700' : 'text-amber-700'} /><p className={`text-xs font-extrabold uppercase tracking-wider ${isValidLeaf ? 'text-emerald-700' : 'text-amber-700'}`}>{t('result.treatment')}</p></div><p className={`mt-2 text-sm leading-6 ${isValidLeaf ? 'text-emerald-900/75' : 'text-amber-900/75'}`}>{treatment}</p></div>
        {showGradCam && isValidLeaf && <GradCamPanel previewUrl={previewUrl} explanation={explanation} loading={explainLoading} onExplain={onExplain} />}
        <p className="mt-5 text-xs leading-5 text-slate-400">{t('result.disclaimer')}</p>
        {onReset && <button type="button" className="btn-secondary mt-5 w-full" onClick={onReset}><RotateCcw size={16} />{t('result.reset')}</button>}
      </div>
    </div>
  )
}
