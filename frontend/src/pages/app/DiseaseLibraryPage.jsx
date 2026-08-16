import { AlertTriangle, BookOpen, Search, ShieldCheck } from 'lucide-react'
import { useMemo, useState } from 'react'
import PageHeader from '../../components/common/PageHeader.jsx'
import StatusBadge from '../../components/common/StatusBadge.jsx'
import { initialDiseases } from '../../data/demoData.js'
import { loadCollection } from '../../utils/storage.js'

export default function DiseaseLibraryPage() {
  const [query, setQuery] = useState('')
  const diseases = loadCollection('plantcare_diseases', initialDiseases)
  const filtered = useMemo(() => diseases.filter((item) => `${item.name} ${item.plant} ${item.symptoms}`.toLocaleLowerCase('vi').includes(query.toLocaleLowerCase('vi'))), [diseases, query])

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader eyebrow="Kiến thức cây trồng" title="Thư viện bệnh cây" description="Nội dung bệnh, triệu chứng và gợi ý xử lý do quản trị viên cập nhật." />
      <label className="relative mb-6 block max-w-md"><Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" size={18} /><input value={query} onChange={(event) => setQuery(event.target.value)} className="input-control pl-10" placeholder="Tìm tên bệnh hoặc cây trồng..." /></label>
      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {filtered.map((item) => (
          <article key={item.id} className="card overflow-hidden">
            <div className="flex items-center justify-between border-b border-slate-100 bg-gradient-to-r from-leaf-50 to-white p-5">
              <span className="grid h-11 w-11 place-items-center rounded-2xl bg-white text-leaf-700 shadow-sm"><BookOpen size={21} /></span>
              <StatusBadge value={item.severity} />
            </div>
            <div className="p-5"><p className="text-xs font-bold uppercase tracking-wider text-leaf-600">{item.plant}</p><h2 className="mt-2 text-lg font-extrabold text-slate-900">{item.name}</h2><p className="mt-3 text-sm leading-6 text-slate-500">{item.symptoms}</p><div className="mt-5 rounded-2xl bg-slate-50 p-4"><p className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-500"><ShieldCheck size={15} className="text-leaf-600" />Gợi ý xử lý</p><p className="mt-2 text-sm leading-6 text-slate-600">{item.treatment}</p></div></div>
          </article>
        ))}
      </div>
      {!filtered.length && <div className="card py-16 text-center"><AlertTriangle className="mx-auto text-slate-300" size={34} /><p className="mt-4 font-bold text-slate-700">Không tìm thấy nội dung phù hợp</p></div>}
    </div>
  )
}
