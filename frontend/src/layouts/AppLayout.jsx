import { BarChart3, Bell, BookOpen, FileCheck2, History, LayoutDashboard, LogOut, Menu, ScanLine, Sprout, UsersRound, X } from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import Brand from '../components/common/Brand.jsx'
import PreferenceControls from '../components/common/PreferenceControls.jsx'
import { useAuth } from '../contexts/AuthContext.jsx'
import { usePreferences } from '../contexts/PreferencesContext.jsx'

const navItems = [
  { to: '/app/dashboard', labelKey: 'nav.dashboard', icon: LayoutDashboard, roles: ['user', 'technician', 'manager'] },
  { to: '/app/scan', labelKey: 'nav.scan', icon: ScanLine, roles: ['user', 'technician', 'manager'] },
  { to: '/app/history', labelKey: 'nav.history', icon: History, roles: ['user', 'technician', 'manager'] },
  { to: '/app/farms', labelKey: 'nav.farms', icon: Sprout, roles: ['manager'] },
  { to: '/app/managed-users', labelKey: 'nav.people', icon: UsersRound, roles: ['manager'] },
  { to: '/app/farm-dashboard', labelKey: 'nav.farmDashboard', icon: BarChart3, roles: ['manager'] },
  { to: '/app/proposals', labelKey: 'nav.proposals', icon: FileCheck2, roles: ['technician'] },
  { to: '/app/diseases', labelKey: 'nav.diseases', icon: BookOpen, roles: ['user', 'technician', 'manager'] },
]

function roleLabel(role, language) {
  const labels = {
    user: { vi: 'Nông dân', en: 'Farmer' },
    technician: { vi: 'Kỹ thuật viên', en: 'Technician' },
    manager: { vi: 'Quản lý trang trại', en: 'Farm Manager' },
  }
  return labels[role]?.[language] || role
}

function Sidebar({ user, onClose, logout, t, language }) {
  return (
    <div className="flex h-full flex-col bg-white">
      <div className="flex h-20 items-center justify-between border-b border-slate-100 px-6">
        <Brand to="/app/dashboard" />
        {onClose && <button className="rounded-xl p-2 text-slate-400 lg:hidden" onClick={onClose} aria-label={t('header.menu')}><X size={20} /></button>}
      </div>
      <nav className="flex-1 space-y-1 overflow-y-auto px-4 py-6">
        <p className="mb-3 px-3 text-[11px] font-bold uppercase tracking-[0.18em] text-slate-400">{t('nav.workspace')}</p>
        {navItems.filter((item) => item.roles.includes(user.role)).map(({ to, labelKey, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onClose}
            className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold transition ${isActive ? 'bg-leaf-50 text-leaf-700' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800'}`}
          >
            <Icon size={19} /> {t(labelKey)}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-slate-100 p-4">
        <NavLink to="/app/profile" onClick={onClose} className="mb-3 flex items-center gap-3 rounded-2xl bg-slate-50 p-3 hover:bg-leaf-50/70 transition">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-leaf-100 font-bold text-leaf-700">
            {(user.full_name || user.username).charAt(0).toUpperCase()}
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-bold text-slate-800">{user.full_name || user.username}</p>
            <p className="truncate text-xs text-slate-400">{roleLabel(user.role, language)}</p>
          </div>
        </NavLink>
        <button onClick={logout} className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold text-slate-500 transition hover:bg-rose-50 hover:text-rose-600">
          <LogOut size={18} /> {t('common.logout')}
        </button>
      </div>
    </div>
  )
}

export default function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const { user, logout } = useAuth()
  const { language, t } = usePreferences()
  const visibleNavItems = navItems.filter((item) => item.roles.includes(user.role))

  return (
    <div className="min-h-screen bg-[#f7faf8]">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-72 border-r border-slate-100 lg:block">
        <Sidebar user={user} logout={logout} t={t} language={language} />
      </aside>
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button className="absolute inset-0 bg-slate-950/35" onClick={() => setMobileOpen(false)} aria-label={t('header.menu')} />
          <aside className="relative h-full w-[85%] max-w-72 shadow-2xl">
            <Sidebar user={user} logout={logout} onClose={() => setMobileOpen(false)} t={t} language={language} />
          </aside>
        </div>
      )}

      <div className="lg:pl-72">
        <header className="sticky top-0 z-20 flex h-20 items-center justify-between border-b border-slate-100 bg-white/90 px-4 backdrop-blur-xl sm:px-7">
          <div className="flex items-center gap-3">
            <button className="rounded-xl border border-slate-200 bg-white p-2.5 text-slate-600 lg:hidden" onClick={() => setMobileOpen(true)} aria-label={t('header.menu')}><Menu size={20} /></button>
            <div>
              <p className="text-xs font-medium text-slate-400">{t('header.hello')}</p>
              <p className="text-sm font-bold text-slate-800">{user.full_name || user.username} 👋</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <PreferenceControls compact />
            <button className="relative hidden rounded-xl border border-slate-200 bg-white p-2.5 text-slate-500 transition hover:bg-leaf-50 hover:text-leaf-700 sm:block" aria-label={t('header.notifications')}>
              <Bell size={19} />
              <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-rose-500 ring-2 ring-white" />
            </button>
          </div>
        </header>
        <main className="p-4 pb-28 sm:p-7 sm:pb-28 lg:p-8"><Outlet /></main>
      </div>

      <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-slate-200 bg-white/95 pb-[max(.5rem,env(safe-area-inset-bottom))] pt-2 backdrop-blur-xl dark:border-slate-800 dark:bg-slate-950/95 lg:hidden" aria-label={t('nav.workspace')}>
        <div className="flex gap-1 overflow-x-auto px-2 scrollbar-thin">
          {visibleNavItems.map(({ to, labelKey, icon: Icon }) => (
            <NavLink key={to} to={to} className={({ isActive }) => `flex min-w-[4.6rem] flex-1 flex-col items-center gap-1 rounded-xl px-2 py-2 text-center text-[10px] font-bold leading-tight transition ${isActive ? 'bg-leaf-50 text-leaf-700 dark:bg-leaf-950/50 dark:text-leaf-300' : 'text-slate-500 dark:text-slate-400'}`}>
              <Icon size={19} />
              <span>{t(labelKey)}</span>
            </NavLink>
          ))}
        </div>
      </nav>
    </div>
  )
}
