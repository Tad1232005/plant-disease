import { BrainCircuit, LoaderCircle, ScanSearch } from 'lucide-react'
import { usePreferences } from '../contexts/PreferencesContext.jsx'

export default function GradCamPanel({ previewUrl, explanation, loading, onExplain }) {
  const { t } = usePreferences()
  const imageUrl = explanation?.gradcam_url || explanation?.image_url
  if (!explanation) {
    return (
      <div className="mt-6 rounded-2xl border border-sky-100 bg-sky-50 p-4">
        <div className="flex items-start gap-3"><BrainCircuit className="mt-0.5 shrink-0 text-sky-600" size={20} /><div><p className="text-sm font-extrabold text-sky-900">{t('gradcam.title')}</p><p className="mt-1 text-xs leading-5 text-sky-700">{t('gradcam.text')}</p></div></div>
        <button type="button" className="btn-secondary mt-4 w-full" disabled={loading} onClick={onExplain}>{loading ? <LoaderCircle className="animate-spin" size={16} /> : <ScanSearch size={16} />}{loading ? t('gradcam.loading') : t('gradcam.create')}</button>
      </div>
    )
  }

  return (
    <div className="mt-6 overflow-hidden rounded-2xl border border-sky-100 bg-slate-950 p-3">
      <div className="relative overflow-hidden rounded-xl bg-slate-900">
        {(imageUrl || previewUrl) && <img src={imageUrl || previewUrl} alt={t('gradcam.alt')} className="h-64 w-full object-contain" />}
        {!imageUrl && previewUrl && <div className="pointer-events-none absolute inset-0 opacity-70 mix-blend-screen" style={{ background: 'radial-gradient(circle at 62% 42%, rgba(239,68,68,.95) 0 10%, rgba(251,146,60,.75) 18%, rgba(250,204,21,.35) 30%, transparent 48%), radial-gradient(circle at 35% 68%, rgba(239,68,68,.65), transparent 32%)' }} />}
        <span className="absolute left-3 top-3 rounded-lg bg-slate-950/75 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-white">Grad-CAM overlay</span>
      </div>
      <p className="px-1 pb-1 pt-3 text-xs leading-5 text-slate-300">{t('gradcam.explain')}</p>
    </div>
  )
}
