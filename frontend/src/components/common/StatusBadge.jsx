const variants = {
  healthy: 'bg-emerald-50 text-emerald-700 ring-emerald-600/15',
  active: 'bg-emerald-50 text-emerald-700 ring-emerald-600/15',
  low: 'bg-emerald-50 text-emerald-700 ring-emerald-600/15',
  attention: 'bg-amber-50 text-amber-700 ring-amber-600/15',
  medium: 'bg-amber-50 text-amber-700 ring-amber-600/15',
  risk: 'bg-rose-50 text-rose-700 ring-rose-600/15',
  high: 'bg-rose-50 text-rose-700 ring-rose-600/15',
  inactive: 'bg-slate-100 text-slate-600 ring-slate-500/15',
}

const labels = {
  healthy: 'Khỏe mạnh',
  active: 'Đang hoạt động',
  low: 'Thấp',
  attention: 'Cần chú ý',
  medium: 'Trung bình',
  risk: 'Nguy cơ cao',
  high: 'Cao',
  inactive: 'Tạm khóa',
}

export default function StatusBadge({ value, children }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${variants[value] || variants.inactive}`}>
      {children || labels[value] || value}
    </span>
  )
}
