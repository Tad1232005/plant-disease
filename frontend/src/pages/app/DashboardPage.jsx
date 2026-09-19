import { AlertTriangle, ArrowRight, CheckCircle2, Clock3, Leaf, ScanLine, Sprout, TrendingUp } from 'lucide-react'
import { Link } from 'react-router-dom'
import StatCard from '../../components/common/StatCard.jsx'
import StatusBadge from '../../components/common/StatusBadge.jsx'
import { useAuth } from '../../contexts/AuthContext.jsx'
import { scanHistory } from '../../data/demoData.js'

const roleContent = {
  user: {
    eyebrow: 'Không gian nông dân',
    title: 'Tổng quan vườn cây',
    description: 'Theo dõi nhanh sức khỏe cây trồng và bắt đầu một lần chẩn đoán mới.',
  },
  technician: {
    eyebrow: 'Không gian chuyên môn',
    title: 'Trung tâm chẩn đoán',
    description: 'Kiểm tra kết quả, độ tin cậy và các mẫu cần chuyên gia xác minh.',
  },
  manager: {
    eyebrow: 'Không gian quản lý',
    title: 'Tổng quan trang trại',
    description: 'Nắm tình hình nhiều khu vực và ưu tiên nơi cần xử lý trước.',
  },
}

export default function DashboardPage() {
  const { user } = useAuth()
  const content = roleContent[user.role] || roleContent.user
  const chart = [45, 68, 54, 82, 64, 92, 76]

  return (
    <div className="mx-auto max-w-7xl">
      <section className="relative overflow-hidden rounded-[2rem] bg-leaf-800 p-6 text-white sm:p-8">
        <div className="absolute -right-16 -top-24 h-64 w-64 rounded-full border-[55px] border-white/5" />
        <div className="relative flex flex-col justify-between gap-7 md:flex-row md:items-center">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-leaf-200">{content.eyebrow}</p>
            <h1 className="mt-3 text-3xl font-black tracking-tight sm:text-4xl">{content.title}</h1>
            <p className="mt-3 max-w-xl text-sm leading-7 text-leaf-50/70">{content.description}</p>
          </div>
          <Link to="/app/scan" className="inline-flex shrink-0 items-center justify-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-bold text-leaf-800 shadow-lg shadow-leaf-950/20 hover:bg-leaf-50">
            <ScanLine size={18} /> Chẩn đoán ảnh mới
          </Link>
        </div>
      </section>

      <section className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard icon={ScanLine} label="Lượt chẩn đoán tháng này" value="128" note="12.5%" tone="green" />
        <StatCard icon={CheckCircle2} label="Mẫu cây khỏe mạnh" value="84" note="8.2%" tone="blue" />
        <StatCard icon={AlertTriangle} label="Mẫu cần chú ý" value="11" tone="amber" />
        <StatCard icon={Sprout} label={user.role === 'manager' ? 'Khu vực đang quản lý' : 'Khu vực của tôi'} value="04" tone="purple" />
      </section>

      <section className="mt-6 grid gap-6 xl:grid-cols-[1.25fr_.75fr]">
        <div className="card p-5 sm:p-6">
          <div className="flex items-start justify-between gap-3">
            <div><h2 className="text-lg font-extrabold text-slate-900">Hoạt động chẩn đoán</h2><p className="mt-1 text-sm text-slate-400">7 ngày gần nhất</p></div>
            <span className="inline-flex items-center gap-1 rounded-full bg-leaf-50 px-3 py-1 text-xs font-bold text-leaf-700"><TrendingUp size={14} /> +18%</span>
          </div>
          <div className="mt-8 flex h-52 items-end justify-between gap-3 border-b border-slate-100 px-2">
            {chart.map((height, index) => (
              <div key={index} className="flex h-full flex-1 flex-col items-center justify-end gap-2">
                <div className="group relative flex w-full justify-center">
                  <div className="w-full max-w-10 rounded-t-xl bg-gradient-to-t from-leaf-600 to-leaf-300 transition hover:from-leaf-700" style={{ height: `${height}%` }} />
                </div>
                <span className="text-[11px] font-medium text-slate-400">T{index + 2}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card p-5 sm:p-6">
          <div className="flex items-center justify-between">
            <div><h2 className="text-lg font-extrabold text-slate-900">Cảnh báo gần đây</h2><p className="mt-1 text-sm text-slate-400">Cần kiểm tra sớm</p></div>
            <span className="grid h-10 w-10 place-items-center rounded-xl bg-amber-50 text-amber-600"><AlertTriangle size={20} /></span>
          </div>
          <div className="mt-5 space-y-3">
            <div className="rounded-2xl border border-rose-100 bg-rose-50/60 p-4"><div className="flex items-center justify-between gap-3"><p className="font-bold text-slate-800">Ruộng ngô C3</p><StatusBadge value="high" /></div><p className="mt-2 text-sm text-slate-500">Phát hiện dấu hiệu gỉ sắt trên 3 mẫu gần nhất.</p></div>
            <div className="rounded-2xl border border-amber-100 bg-amber-50/60 p-4"><div className="flex items-center justify-between gap-3"><p className="font-bold text-slate-800">Khu khoai tây B2</p><StatusBadge value="medium" /></div><p className="mt-2 text-sm text-slate-500">Tỷ lệ mẫu nghi ngờ tăng trong 2 ngày.</p></div>
          </div>
        </div>
      </section>

      <section className="card mt-6 overflow-hidden">
        <div className="flex items-center justify-between border-b border-slate-100 p-5 sm:p-6"><div><h2 className="text-lg font-extrabold text-slate-900">Chẩn đoán gần nhất</h2><p className="mt-1 text-sm text-slate-400">Cập nhật từ lịch sử quét</p></div><Link to="/app/history" className="inline-flex items-center gap-1.5 text-sm font-bold text-leaf-700">Xem tất cả <ArrowRight size={16} /></Link></div>
        <div className="divide-y divide-slate-100">
          {scanHistory.slice(0, 3).map((item) => (
            <div key={item.id} className="flex flex-col justify-between gap-3 px-5 py-4 transition hover:bg-slate-50 sm:flex-row sm:items-center sm:px-6">
              <div className="flex items-center gap-3"><span className="grid h-10 w-10 place-items-center rounded-xl bg-leaf-50 text-leaf-700"><Leaf size={18} /></span><div><p className="text-sm font-bold text-slate-800">{item.result}</p><p className="mt-0.5 text-xs text-slate-400">{item.farm}</p></div></div>
              <div className="flex items-center justify-between gap-5 sm:justify-end"><StatusBadge value={item.severity} /><span className="text-sm font-extrabold text-slate-700">{item.confidence}%</span><span className="inline-flex items-center gap-1 text-xs text-slate-400"><Clock3 size={13} />{item.date.split(' ')[0]}</span></div>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
