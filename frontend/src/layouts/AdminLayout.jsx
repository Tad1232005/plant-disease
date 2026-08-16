import { Activity, Bell, Database, LayoutDashboard, Leaf, LogOut, Menu, ShieldCheck, Sprout, UserCog, X } from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import Brand from '../components/common/Brand.jsx'
import { useAuth } from '../contexts/AuthContext.jsx'

const items = [
  { to: '/admin', label: 'Tổng quan hệ thống', icon: LayoutDashboard, end: true },
  { to: '/admin/users', label: 'Quản lý người dùng', icon: UserCog },
  { to: '/admin/farms', label: 'Dữ liệu trang trại', icon: Sprout },
  { to: '/admin/diseases', label: 'Nội dung bệnh cây', icon: Leaf },
  { to: '/admin/models', label: 'Phiên bản mô hình', icon: Database },
  { to: '/admin/system', label: 'Theo dõi hệ thống', icon: Activity },
]

function AdminSidebar({ onClose, logout, user }) {
  return (
    <div className="flex h-full flex-col bg-leaf-900 text-white">
      <div className="flex h-20 items-center justify-between border-b border-white/10 px-6">
        <Brand to="/admin" light />
        {onClose && <button className="rounded-xl p-2 text-white/60 lg:hidden" onClick={onClose}><X size={20} /></button>}
      </div>
      <div className="mx-4 mt-5 flex items-center gap-2 rounded-xl border border-leaf-600/30 bg-leaf-800/60 px-3 py-2 text-xs font-semibold text-leaf-100">
        <ShieldCheck size={16} /> Khu vực quản trị
      </div>
      <nav className="flex-1 space-y-1 overflow-y-auto px-4 py-5">
        {items.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={onClose}
            className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold transition ${isActive ? 'bg-white text-leaf-800 shadow-sm' : 'text-leaf-100/70 hover:bg-white/10 hover:text-white'}`}
          >
            <Icon size={19} /> {label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-white/10 p-4">
        <p className="truncate px-3 text-sm font-bold">{user.full_name || user.username}</p>
        <p className="mb-3 truncate px-3 text-xs text-leaf-200/60">{user.email}</p>
        <button onClick={logout} className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold text-leaf-100/70 transition hover:bg-white/10 hover:text-white">
          <LogOut size={18} /> Đăng xuất
        </button>
      </div>
    </div>
  )
}

export default function AdminLayout() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen bg-slate-50">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-72 lg:block"><AdminSidebar user={user} logout={logout} /></aside>
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button className="absolute inset-0 bg-slate-950/40" onClick={() => setMobileOpen(false)} aria-label="Đóng menu" />
          <aside className="relative h-full w-[85%] max-w-72"><AdminSidebar user={user} logout={logout} onClose={() => setMobileOpen(false)} /></aside>
        </div>
      )}
      <div className="lg:pl-72">
        <header className="sticky top-0 z-20 flex h-20 items-center justify-between border-b border-slate-200 bg-white/90 px-4 backdrop-blur-xl sm:px-7">
          <div className="flex items-center gap-3">
            <button className="rounded-xl border border-slate-200 p-2.5 lg:hidden" onClick={() => setMobileOpen(true)} aria-label="Mở menu"><Menu size={20} /></button>
            <div>
              <p className="text-xs font-medium text-slate-400">PlantCare Control Center</p>
              <p className="text-sm font-bold text-slate-800">Bảng điều khiển quản trị</p>
            </div>
          </div>
          <button className="relative rounded-xl border border-slate-200 p-2.5 text-slate-500" aria-label="Thông báo"><Bell size={19} /><span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-rose-500" /></button>
        </header>
        <main className="p-4 sm:p-7 lg:p-8"><Outlet /></main>
      </div>
    </div>
  )
}
