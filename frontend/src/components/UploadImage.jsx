import { Camera, ImagePlus, Images, RefreshCcw, UploadCloud, X } from 'lucide-react'
import { useRef, useState } from 'react'
import { usePreferences } from '../contexts/PreferencesContext.jsx'

const ACCEPTED_IMAGES = 'image/jpeg,image/png,image/webp'

export default function UploadImage({ onFileSelect, previewUrl, fileName, validationError, onClear }) {
  const { t } = usePreferences()
  const [dragActive, setDragActive] = useState(false)
  const galleryInputRef = useRef(null)
  const cameraInputRef = useRef(null)

  function selectFile(file, input) {
    if (file) onFileSelect(file)
    if (input) input.value = ''
  }

  function handleDrop(event) {
    event.preventDefault()
    setDragActive(false)
    selectFile(event.dataTransfer.files?.[0])
  }

  const inputs = (
    <>
      <input ref={galleryInputRef} type="file" accept={ACCEPTED_IMAGES} className="hidden" onChange={(event) => selectFile(event.target.files?.[0], event.target)} />
      <input ref={cameraInputRef} type="file" accept="image/*" capture="environment" className="hidden" onChange={(event) => selectFile(event.target.files?.[0], event.target)} />
    </>
  )

  if (previewUrl) {
    return (
      <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-soft">
        <div className="relative min-h-[340px] bg-slate-100">
          <img src={previewUrl} alt={t('upload.previewAlt')} className="h-[min(420px,62vh)] min-h-72 w-full object-contain" />
          <button type="button" onClick={onClear} className="absolute right-4 top-4 rounded-xl bg-slate-900/65 p-2.5 text-white backdrop-blur-sm transition hover:bg-slate-900" aria-label={t('upload.remove')}><X size={18} /></button>
          <span className="absolute bottom-4 left-4 max-w-[80%] truncate rounded-xl bg-white/90 px-3 py-2 text-xs font-semibold text-slate-600 shadow-sm backdrop-blur-sm">{fileName}</span>
        </div>
        <div className="flex flex-col gap-3 border-t border-slate-100 p-4 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-xs text-slate-500">{t('upload.previewHelp')}</p>
          <div className="flex flex-wrap gap-2">
            <button type="button" className="btn-secondary shrink-0" onClick={() => galleryInputRef.current?.click()}><RefreshCcw size={16} />{t('upload.other')}</button>
            <button type="button" className="btn-primary shrink-0" onClick={() => cameraInputRef.current?.click()}><Camera size={16} />{t('upload.retake')}</button>
          </div>
          {inputs}
        </div>
      </div>
    )
  }

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        onClick={() => galleryInputRef.current?.click()}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault()
            galleryInputRef.current?.click()
          }
        }}
        onDragOver={(event) => { event.preventDefault(); setDragActive(true) }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        className={`group flex min-h-[330px] w-full cursor-pointer flex-col items-center justify-center rounded-3xl border-2 border-dashed px-5 py-10 text-center transition focus:outline-none focus:ring-4 focus:ring-leaf-100 sm:min-h-[390px] sm:px-6 sm:py-14 ${dragActive ? 'border-leaf-500 bg-leaf-50' : validationError ? 'border-rose-300 bg-rose-50/30' : 'border-slate-200 bg-white hover:border-leaf-400 hover:bg-leaf-50/40'}`}
      >
        <span className="relative grid h-20 w-20 place-items-center rounded-3xl bg-leaf-50 text-leaf-700 transition group-hover:scale-105">
          <UploadCloud size={34} />
          <span className="absolute -right-2 -top-2 grid h-8 w-8 place-items-center rounded-xl bg-white text-leaf-500 shadow-sm"><ImagePlus size={16} /></span>
        </span>
        <h3 className="mt-6 text-lg font-extrabold text-slate-900">{t('upload.drop')}</h3>
        <p className="mt-2 max-w-sm text-sm leading-6 text-slate-500">{t('upload.help')}</p>
        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <button type="button" className="btn-secondary" onClick={(event) => { event.stopPropagation(); galleryInputRef.current?.click() }}><Images size={17} />{t('upload.library')}</button>
          <button type="button" className="btn-primary" onClick={(event) => { event.stopPropagation(); cameraInputRef.current?.click() }}><Camera size={17} />{t('upload.camera')}</button>
        </div>
      </div>
      {inputs}
      {validationError && <p className="mt-3 text-sm font-medium text-rose-600">{validationError}</p>}
    </div>
  )
}
