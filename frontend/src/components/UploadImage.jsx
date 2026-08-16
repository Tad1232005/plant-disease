import { Camera, ImagePlus, RefreshCcw, UploadCloud, X } from 'lucide-react'
import { useRef, useState } from 'react'

export default function UploadImage({ onFileSelect, previewUrl, fileName, validationError, onClear }) {
  const [dragActive, setDragActive] = useState(false)
  const inputRef = useRef(null)

  function selectFile(file) {
    if (file) onFileSelect(file)
  }

  function handleDrop(event) {
    event.preventDefault()
    setDragActive(false)
    selectFile(event.dataTransfer.files?.[0])
  }

  if (previewUrl) {
    return (
      <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-soft">
        <div className="relative min-h-[340px] bg-slate-100">
          <img src={previewUrl} alt="Ảnh lá cây đã chọn" className="h-[420px] w-full object-contain" />
          <button onClick={onClear} className="absolute right-4 top-4 rounded-xl bg-slate-900/65 p-2.5 text-white backdrop-blur-sm transition hover:bg-slate-900" aria-label="Xóa ảnh"><X size={18} /></button>
          <span className="absolute bottom-4 left-4 max-w-[80%] truncate rounded-xl bg-white/90 px-3 py-2 text-xs font-semibold text-slate-600 shadow-sm backdrop-blur-sm">{fileName}</span>
        </div>
        <div className="flex flex-col items-start justify-between gap-3 border-t border-slate-100 p-4 sm:flex-row sm:items-center">
          <p className="text-xs text-slate-500">Kiểm tra ảnh rõ nét và phần lá chiếm phần lớn khung hình.</p>
          <button className="btn-secondary shrink-0" onClick={() => inputRef.current?.click()}><RefreshCcw size={16} /> Chọn ảnh khác</button>
          <input ref={inputRef} type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={(event) => selectFile(event.target.files?.[0])} />
        </div>
      </div>
    )
  }

  return (
    <div>
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        onDragOver={(event) => { event.preventDefault(); setDragActive(true) }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        className={`group flex min-h-[390px] w-full flex-col items-center justify-center rounded-3xl border-2 border-dashed px-6 py-14 text-center transition ${dragActive ? 'border-leaf-500 bg-leaf-50' : validationError ? 'border-rose-300 bg-rose-50/30' : 'border-slate-200 bg-white hover:border-leaf-400 hover:bg-leaf-50/40'}`}
      >
        <span className="relative grid h-20 w-20 place-items-center rounded-3xl bg-leaf-50 text-leaf-700 transition group-hover:scale-105">
          <UploadCloud size={34} />
          <span className="absolute -right-2 -top-2 grid h-8 w-8 place-items-center rounded-xl bg-white text-leaf-500 shadow-sm"><ImagePlus size={16} /></span>
        </span>
        <h3 className="mt-6 text-lg font-extrabold text-slate-900">Kéo thả ảnh lá cây vào đây</h3>
        <p className="mt-2 max-w-sm text-sm leading-6 text-slate-500">Hoặc nhấn để chọn ảnh từ thiết bị. Hỗ trợ JPG, PNG, WEBP tối đa 8 MB.</p>
        <span className="btn-primary mt-6"><Camera size={17} /> Chọn ảnh</span>
      </button>
      <input ref={inputRef} type="file" accept="image/jpeg,image/png,image/webp" className="hidden" onChange={(event) => selectFile(event.target.files?.[0])} />
      {validationError && <p className="mt-3 text-sm font-medium text-rose-600">{validationError}</p>}
    </div>
  )
}
