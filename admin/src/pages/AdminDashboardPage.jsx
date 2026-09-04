import { Activity, Database, Leaf, ScanLine, Server, ShieldCheck, Sprout, Users } from 'lucide-react'
import StatCard from '../components/common/StatCard.jsx'
import StatusBadge from '../components/common/StatusBadge.jsx'

export default function AdminDashboardPage() {
  const services = [
    { name: 'FastAPI Backend', detail: 'http://localhost:8000', status: 'active' },
    { name: 'SQLite Database', detail: '6 bảng dữ liệu', status: 'active' },
    { name: 'Model phân loại', detail: 'plant_disease_v2.1.pt', status: 'active' },
  ]

  return (
    <div className="mx-auto max-w-7xl">
      <div className="mb-7"><p className="text-xs font-bold uppercase tracking-[0.2em] text-leaf-600">Ứng dụng Admin độc lập</p><h1 className="mt-2 text-3xl font-black tracking-tight text-slate-900">Tổng quan hệ thống</h1><p className="mt-2 text-sm text-slate-500">Trang quản trị chạy riêng trên cổng 5174 và được bảo vệ bởi role <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs">admin</code>.</p></div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={Users} label="Người dùng" value="248" note="9.4%" />
        <StatCard icon={ScanLine} label="Tổng lượt quét" value="1,842" note="14.2%" tone="blue" />
        <StatCard icon={Sprout} label="Trang trại" value="36" tone="amber" />
        <StatCard icon={Database} label="Model đang chạy" value="v2.1" tone="purple" />
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1.05fr_.95fr]">
        <section className="card p-6">
          <div className="flex items-center justify-between"><div><h2 className="text-lg font-extrabold text-slate-900">Trạng thái dịch vụ</h2><p className="mt-1 text-sm text-slate-400">Khung giám sát sẵn sàng nối API</p></div><span className="grid h-10 w-10 place-items-center rounded-xl bg-leaf-50 text-leaf-700"><Activity size={20} /></span></div>
          <div className="mt-5 divide-y divide-slate-100">
            {services.map((service) => <div key={service.name} className="flex items-center justify-between gap-3 py-4"><div className="flex items-center gap-3"><span className="grid h-10 w-10 place-items-center rounded-xl bg-slate-50 text-slate-500"><Server size={18} /></span><div><p className="text-sm font-bold text-slate-800">{service.name}</p><p className="mt-0.5 text-xs text-slate-400">{service.detail}</p></div></div><StatusBadge value={service.status} /></div>)}
          </div>
        </section>

        <section className="overflow-hidden rounded-3xl bg-leaf-900 p-6 text-white shadow-soft">
          <span className="grid h-12 w-12 place-items-center rounded-2xl bg-white/10 text-leaf-200"><ShieldCheck size={23} /></span>
          <h2 className="mt-5 text-2xl font-black">Admin Panel đã sẵn sàng</h2>
          <p className="mt-3 text-sm leading-7 text-leaf-100/65">Luồng duyệt đề xuất, thống kê toàn hệ thống và quản lý Model Version đã được hoàn thiện cho Tuần 6–7.</p>
          <div className="mt-6 grid grid-cols-2 gap-3"><div className="rounded-2xl bg-white/10 p-4"><Leaf size={18} className="text-leaf-200" /><p className="mt-3 text-2xl font-black">04</p><p className="mt-1 text-xs text-leaf-100/60">Nội dung bệnh</p></div><div className="rounded-2xl bg-white/10 p-4"><Activity size={18} className="text-leaf-200" /><p className="mt-3 text-2xl font-black">99.9%</p><p className="mt-1 text-xs text-leaf-100/60">Uptime mẫu</p></div></div>
        </section>
      </div>
    </div>
  )
}
