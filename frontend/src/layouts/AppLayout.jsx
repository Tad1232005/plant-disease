import { Bell, BookOpen, History, LayoutDashboard, LogOut, Menu, ScanLine, Sprout, X } from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import Brand from '../components/common/Brand.jsx'
import { useAuth } from '../contexts/AuthContext.jsx'
import { getRoleLabel } from '../utils/roles.js'

const navItems = [
  { to: '/app/dashboard', label: 'Tổng quan', icon: LayoutDashboard, roles: ['user', 'technician', 'manager'] },
  { to: '/app/scan', label: 'Chẩn đoán mới', icon: ScanLine, roles: ['user', 'technician', 'manager'] },
  { to: '/app/history', label: 'Lịch sử chẩn đoán', icon: History, roles: ['user', 'technician', 'manager'] },
  { to: '/app/farms', label: 'Quản lý trang trại', icon: Sprout, roles: ['user', 'manager'] },
  { to: '/app/diseases', label: 'Thư viện bệnh', icon: BookOpen, roles: ['user', 'technician', 'manager'] },
]

function Sidebar({ user, onClose, logout }) {
  return (
    <div className="flex h-full flex-col bg-white">
      <div className="flex h-20 items-center justify-between border-b border-slate-100 px-6">
        <Brand to="/app/dashboard" />
        {onClose && <button className="rounded-xl p-2 text-slate-400 lg:hidden" onClick={onClose}><X size={20} /></button>}
      </div>
      <nav className="flex-1 space-y-1 overflow-y-auto px-4 py-6">
        <p className="mb-3 px-3 text-[11px] font-bold uppercase tracking-[0.18em] text-slate-400">Không gian làm việc</p>
        {navItems.filter((item) => item.roles.includes(user.role)).map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onClose}
            className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold transition ${isActive ? 'bg-leaf-50 text-leaf-700' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800'}`}
          >
            <Icon size={19} /> {label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-slate-100 p-4">
        <div className="mb-3 flex items-center gap-3 rounded-2xl bg-slate-50 p-3">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-leaf-100 font-bold text-leaf-700">
            {(user.full_name || user.username).charAt(0).toUpperCase()}
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-bold text-slate-800">{user.full_name || user.username}</p>
            <p className="truncate text-xs text-slate-400">{getRoleLabel(user.role)}</p>
          </div>
        </div>
        <button onClick={logout} className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold text-slate-500 transition hover:bg-rose-50 hover:text-rose-600">
          <LogOut size={18} /> Đăng xuất
        </button>
      </div>
    </div>
  )
}

export default function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen bg-[#f7faf8]">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-72 border-r border-slate-100 lg:block">
        <Sidebar user={user} logout={logout} />
      </aside>
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button className="absolute inset-0 bg-slate-950/35" onClick={() => setMobileOpen(false)} aria-label="Đóng menu" />
          <aside className="relative h-full w-[85%] max-w-72 shadow-2xl">
            <Sidebar user={user} logout={logout} onClose={() => setMobileOpen(false)} />
          </aside>
        </div>
      )}

      <div className="lg:pl-72">
        <header className="sticky top-0 z-20 flex h-20 items-center justify-between border-b border-slate-100 bg-white/90 px-4 backdrop-blur-xl sm:px-7">
          <div className="flex items-center gap-3">
            <button className="rounded-xl border border-slate-200 bg-white p-2.5 text-slate-600 lg:hidden" onClick={() => setMobileOpen(true)} aria-label="Mở menu"><Menu size={20} /></button>
            <div>
              <p className="text-xs font-medium text-slate-400">Xin chào,</p>
              <p className="text-sm font-bold text-slate-800">{user.full_name || user.username} 👋</p>
            </div>
          </div>
          <button className="relative rounded-xl border border-slate-200 bg-white p-2.5 text-slate-500 transition hover:bg-leaf-50 hover:text-leaf-700" aria-label="Thông báo">
            <Bell size={19} />
            <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-rose-500 ring-2 ring-white" />
          </button>
        </header>
        <main className="p-4 sm:p-7 lg:p-8"><Outlet /></main>
      </div>
    </div>
  )
}
