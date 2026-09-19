import { Construction } from 'lucide-react'
import PageHeader from '../../components/common/PageHeader.jsx'

export default function PlaceholderPage({ title, description }) {
  return <div className="mx-auto max-w-7xl"><PageHeader eyebrow="Khung Admin Panel" title={title} description={description} /><div className="card flex min-h-[420px] flex-col items-center justify-center p-8 text-center"><span className="grid h-16 w-16 place-items-center rounded-3xl bg-leaf-50 text-leaf-700"><Construction size={28} /></span><h2 className="mt-5 text-xl font-extrabold text-slate-800">Route và layout đã hoàn thành</h2><p className="mt-2 max-w-lg text-sm leading-6 text-slate-500">Trang này được dựng sẵn từ Tuần 2 theo roadmap. Dữ liệu và hành động API sẽ được nối ở giai đoạn chức năng quản trị tương ứng.</p></div></div>
}
