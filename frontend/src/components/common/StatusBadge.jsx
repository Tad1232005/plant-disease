const variants = {
  healthy: 'bg-emerald-50 text-emerald-700 ring-emerald-600/15',
  active: 'bg-emerald-50 text-emerald-700 ring-emerald-600/15',
  low: 'bg-emerald-50 text-emerald-700 ring-emerald-600/15',
  attention: 'bg-amber-50 text-amber-700 ring-amber-600/15',
  medium: 'bg-amber-50 text-amber-700 ring-amber-600/15',
  risk: 'bg-rose-50 text-rose-700 ring-rose-600/15',
  high: 'bg-rose-50 text-rose-700 ring-rose-600/15',
  inactive: 'bg-slate-100 text-slate-600 ring-slate-500/15',
  pending: 'bg-amber-50 text-amber-700 ring-amber-600/15',
  approved: 'bg-emerald-50 text-emerald-700 ring-emerald-600/15',
  rejected: 'bg-rose-50 text-rose-700 ring-rose-600/15',
  valid: 'bg-emerald-50 text-emerald-700 ring-emerald-600/15',
  invalid: 'bg-amber-50 text-amber-700 ring-amber-600/15',
}

import { usePreferences } from '../../contexts/PreferencesContext.jsx'

const labels = { vi: {
  healthy: 'Khỏe mạnh',
  active: 'Đang hoạt động',
  low: 'Thấp',
  attention: 'Cần chú ý',
  medium: 'Trung bình',
  risk: 'Nguy cơ cao',
  high: 'Cao',
  inactive: 'Tạm khóa',
  pending: 'Chờ duyệt',
  approved: 'Đã duyệt',
  rejected: 'Từ chối',
  valid: 'Lá hợp lệ',
  invalid: 'Ảnh OOD',
}, en: {
  healthy: 'Healthy', active: 'Active', low: 'Low', attention: 'Needs attention', medium: 'Medium', risk: 'High risk', high: 'High', inactive: 'Inactive', pending: 'Pending', approved: 'Approved', rejected: 'Rejected', valid: 'Valid leaf', invalid: 'OOD image',
} }

export default function StatusBadge({ value, children }) {
  const { language } = usePreferences()
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${variants[value] || variants.inactive}`}>
      {children || labels[language]?.[value] || value}
    </span>
  )
}
