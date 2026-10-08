import { AlertCircle, CalendarClock, CheckCircle2, ExternalLink, Leaf, LoaderCircle, MapPin, RotateCcw, ShieldAlert, ShieldCheck, Sparkles } from 'lucide-react'
import { Link } from 'react-router-dom'
import GradCamPanel from './GradCamPanel.jsx'
import { usePreferences } from '../contexts/PreferencesContext.jsx'

function friendlyLabel(label = '') {
  return String(label).replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function formatModelType(type = '') {
  if (type.includes('efficientnet')) return 'EfficientNet-B0'
  if (type.includes('mobilenet')) return 'MobileNet-V2'
  if (type.includes('resnet')) return 'ResNet-50'
  return type
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
  const primaryModelType = result.decision_details?.primary_model || result.selected_model_type || result.model_version
  const treatment = result.treatment || result.recommendation || treatmentByLabel[result.label] || (language === 'vi'
    ? (isValidLeaf ? 'Theo dõi cây trong 3–5 ngày và liên hệ kỹ thuật viên nếu triệu chứng lan rộng.' : 'Chụp lại một lá cây rõ nét, đủ sáng và chiếm phần lớn khung hình.')
    : (isValidLeaf ? 'Monitor the plant for 3–5 days and contact a technician if symptoms spread.' : 'Retake a clear, well-lit photo with one leaf filling most of the frame.'))

  return (
    <div className="card overflow-hidden">
      <div className={`bg-gradient-to-r p-6 text-white ${isValidLeaf ? 'from-leaf-700 to-leaf-600' : 'from-amber-700 to-orange-600'}`}>
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <p className="text-xs font-bold uppercase tracking-wider text-white/65">
                {isValidLeaf ? t('result.prediction') : t('result.ood')}
              </p>
              {primaryModelType && isValidLeaf && (
                <span className="rounded-full bg-white/20 px-2 py-0.5 text-[10px] font-semibold text-white">
                  {formatModelType(primaryModelType)}
                </span>
              )}
            </div>
            <h3 className="mt-2 text-2xl font-black">{isValidLeaf ? friendlyLabel(result.label) : t('result.invalid')}</h3>
          </div>
          <span className="grid h-12 w-12 place-items-center rounded-2xl bg-white/15">
            {isValidLeaf ? <CheckCircle2 size={24} /> : <ShieldAlert size={24} />}
          </span>
        </div>
        <div className="mt-6 flex items-end justify-between">
          <span className="text-sm text-white/70">
            {primaryModelType ? `${formatModelType(primaryModelType)}: ` : ''}{t('result.confidence')}
          </span>
          <strong className="text-3xl">{confidence.toFixed(1)}%</strong>
        </div>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-black/15">
          <div className="h-full rounded-full bg-white transition-all" style={{ width: `${Math.min(confidence, 100)}%` }} />
        </div>
        {result.ood_score !== undefined && <p className="mt-3 text-xs text-white/70">OOD score: {toPercent(result.ood_score).toFixed(1)}%</p>}
      </div>
      <div className="p-6">
        {meta && <div className="mb-6 grid gap-3 rounded-2xl bg-slate-50 p-4 text-xs text-slate-600 sm:grid-cols-2"><span className="flex items-center gap-2"><MapPin size={15} className="text-leaf-600" />{meta.farmName}</span><span className="flex items-center gap-2"><CalendarClock size={15} className="text-leaf-600" />{meta.date}</span></div>}
        {!isValidLeaf && <div className="mb-5 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-900"><strong>{t('result.invalidTitle')}</strong> {t('result.invalidText')}</div>}
        
        {isValidLeaf && (
          <>
            <h4 className="text-sm font-extrabold text-slate-800">{t('result.top')}</h4>
            <div className="mt-4 space-y-3">
              {topK.slice(0, 3).map((item, index) => {
                const percent = toPercent(item.confidence)
                return (
                  <div key={`${item.label}-${index}`}>
                    <div className="mb-1.5 flex items-center justify-between gap-3 text-xs">
                      <span className="truncate font-semibold text-slate-600">{index + 1}. {friendlyLabel(item.label)}</span>
                      <span className="font-bold text-slate-700">{percent.toFixed(1)}%</span>
                    </div>
                    <div className="h-1.5 overflow-hidden rounded-full bg-slate-100">
                      <div className={`h-full rounded-full ${index === 0 ? 'bg-leaf-500' : 'bg-slate-300'}`} style={{ width: `${Math.min(percent, 100)}%` }} />
                    </div>
                  </div>
                )
              })}
            </div>
          </>
        )}

        {/* Khối kiểm định 2 tầng & đối chiếu các mô hình */}
        {isValidLeaf && Array.isArray(result.model_results) && result.model_results.length > 1 && (
          <div className="mt-6 rounded-2xl border border-leaf-200/80 bg-leaf-50/50 p-4 dark:border-leaf-800 dark:bg-leaf-950/40">
            <div className="flex items-center justify-between gap-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-leaf-800 dark:text-leaf-200">
                {language === 'vi' ? 'Đối chiếu kiểm định 2 tầng' : 'Two-Tier Model Breakdown'}
              </h4>
              <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                {result.agreement_status === 'agreed'
                  ? (language === 'vi' ? `Đồng thuận ${result.agreement_count || result.models_succeeded}/${result.models_succeeded} model` : `Agreed ${result.agreement_count}/${result.models_succeeded}`)
                  : (language === 'vi' ? 'Có độ phân vân' : 'Disagreed')}
              </span>
            </div>
            <div className="mt-3 space-y-2.5">
              {result.model_results.map((mRes) => {
                const mConf = toPercent(mRes.confidence)
                const isPrimary = mRes.model_type === primaryModelType
                return (
                  <div key={mRes.model_version_id || mRes.model_type} className="rounded-xl border border-slate-200/70 bg-white p-2.5 shadow-sm dark:border-slate-800 dark:bg-slate-900/60">
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-1.5">
                        <span className="font-bold text-slate-800 dark:text-slate-200">{formatModelType(mRes.model_type)}</span>
                        {isPrimary && (
                          <span className="rounded bg-leaf-100 px-1.5 py-0.5 text-[9px] font-bold text-leaf-700 dark:bg-leaf-900/70 dark:text-leaf-300">
                            {language === 'vi' ? 'Bạn chọn' : 'Selected'}
                          </span>
                        )}
                      </div>
                      <strong className="text-slate-700 dark:text-slate-300">{mConf.toFixed(1)}%</strong>
                    </div>
                    <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                      <div
                        className={`h-full rounded-full transition-all ${isPrimary ? 'bg-leaf-600' : 'bg-slate-400'}`}
                        style={{ width: `${Math.min(mConf, 100)}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
            {result.ensemble_confidence !== undefined && (
              <div className="mt-3 flex items-center justify-between border-t border-leaf-100 pt-2 text-[11px] text-slate-600 dark:border-leaf-900/60 dark:text-slate-400">
                <span>{language === 'vi' ? 'Độ tin cậy tổng hợp (Ensemble):' : 'Combined Ensemble Score:'}</span>
                <strong className="font-bold text-leaf-700 dark:text-leaf-300">
                  {toPercent(result.ensemble_confidence).toFixed(1)}%
                </strong>
              </div>
            )}
          </div>
        )}

        <div className={`mt-6 rounded-2xl p-4 ${isValidLeaf ? 'bg-emerald-50' : 'bg-amber-50'}`}><div className="flex items-center gap-2"><Leaf size={16} className={isValidLeaf ? 'text-emerald-700' : 'text-amber-700'} /><p className={`text-xs font-extrabold uppercase tracking-wider ${isValidLeaf ? 'text-emerald-700' : 'text-amber-700'}`}>{t('result.treatment')}</p></div><p className={`mt-2 text-sm leading-6 ${isValidLeaf ? 'text-emerald-900/75' : 'text-amber-900/75'}`}>{treatment}</p></div>
        {showGradCam && isValidLeaf && <GradCamPanel previewUrl={previewUrl} explanation={explanation} loading={explainLoading} onExplain={onExplain} />}
        
        {result?.scan_id && (
          <Link
            to={`/app/scans/${result.scan_id}`}
            className="btn-primary mt-4 flex w-full items-center justify-center gap-2 !py-2.5 text-xs font-bold"
          >
            <ExternalLink size={15} />
            {language === 'vi' ? 'Xem trang chi tiết ca quét (Bản in & Grad-CAM)' : 'View Full Scan Details & Grad-CAM'}
          </Link>
        )}

        <p className="mt-5 text-xs leading-5 text-slate-400">{t('result.disclaimer')}</p>
        {onReset && <button type="button" className="btn-secondary mt-5 w-full" onClick={onReset}><RotateCcw size={16} />{t('result.reset')}</button>}
      </div>
    </div>
  )
}
