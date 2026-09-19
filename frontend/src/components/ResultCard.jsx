import { AlertCircle, CheckCircle2, LoaderCircle, ShieldCheck, Sparkles } from 'lucide-react'

function friendlyLabel(label = '') {
  return label.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

export default function ResultCard({ result, loading, error, onUseDemo }) {
  if (loading) {
    return <div className="card flex min-h-72 flex-col items-center justify-center p-8 text-center"><span className="grid h-16 w-16 place-items-center rounded-3xl bg-leaf-50 text-leaf-700"><LoaderCircle className="animate-spin" size={30} /></span><h3 className="mt-5 text-lg font-extrabold text-slate-900">AI đang phân tích ảnh</h3><p className="mt-2 text-sm text-slate-500">Đang kiểm tra đặc trưng trên lá và xếp hạng kết quả...</p></div>
  }

  if (error) {
    return <div className="card min-h-72 p-6"><span className="grid h-12 w-12 place-items-center rounded-2xl bg-rose-50 text-rose-600"><AlertCircle size={23} /></span><h3 className="mt-5 text-lg font-extrabold text-slate-900">Chưa thể phân tích ảnh</h3><p className="mt-2 text-sm leading-6 text-rose-700">{error}</p>{onUseDemo && <button className="btn-secondary mt-5" onClick={onUseDemo}><Sparkles size={16} /> Xem kết quả mẫu</button>}</div>
  }

  if (!result) {
    return <div className="card flex min-h-72 flex-col items-center justify-center p-8 text-center"><span className="grid h-16 w-16 place-items-center rounded-3xl bg-slate-100 text-slate-400"><ShieldCheck size={28} /></span><h3 className="mt-5 font-extrabold text-slate-800">Kết quả sẽ hiển thị tại đây</h3><p className="mt-2 max-w-sm text-sm leading-6 text-slate-500">Chọn một ảnh rõ nét, sau đó nhấn “Phân tích bệnh” để bắt đầu.</p></div>
  }

  const confidence = Number(result.confidence || 0) * 100
  const topK = result.top_k?.length ? result.top_k : [{ label: result.label, confidence: result.confidence, rank: 1 }]

  return (
    <div className="card overflow-hidden">
      <div className="bg-gradient-to-r from-leaf-700 to-leaf-600 p-6 text-white">
        <div className="flex items-start justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-wider text-leaf-100/70">Kết quả dự đoán</p><h3 className="mt-2 text-2xl font-black">{friendlyLabel(result.label)}</h3></div><span className="grid h-12 w-12 place-items-center rounded-2xl bg-white/15"><CheckCircle2 size={24} /></span></div>
        <div className="mt-6 flex items-end justify-between"><span className="text-sm text-leaf-50/75">Độ tin cậy</span><strong className="text-3xl">{confidence.toFixed(1)}%</strong></div>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-black/15"><div className="h-full rounded-full bg-white transition-all" style={{ width: `${Math.min(confidence, 100)}%` }} /></div>
      </div>
      <div className="p-6">
        <h4 className="text-sm font-extrabold text-slate-800">Top kết quả mô hình</h4>
        <div className="mt-4 space-y-3">
          {topK.slice(0, 3).map((item, index) => {
            const percent = Number(item.confidence || 0) * 100
            return <div key={`${item.label}-${index}`}><div className="mb-1.5 flex items-center justify-between gap-3 text-xs"><span className="truncate font-semibold text-slate-600">{index + 1}. {friendlyLabel(item.label)}</span><span className="font-bold text-slate-700">{percent.toFixed(1)}%</span></div><div className="h-1.5 overflow-hidden rounded-full bg-slate-100"><div className={`h-full rounded-full ${index === 0 ? 'bg-leaf-500' : 'bg-slate-300'}`} style={{ width: `${Math.min(percent, 100)}%` }} /></div></div>
          })}
        </div>
        <div className="mt-6 rounded-2xl bg-amber-50 p-4"><p className="text-xs font-extrabold uppercase tracking-wider text-amber-700">Khuyến nghị</p><p className="mt-2 text-sm leading-6 text-amber-900/75">Kết quả AI chỉ mang tính hỗ trợ. Với bệnh có mức độ nghiêm trọng, nên đối chiếu triệu chứng và hỏi kỹ thuật viên nông nghiệp.</p></div>
      </div>
    </div>
  )
}
