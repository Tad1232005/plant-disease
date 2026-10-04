import { Activity, Bell, Database, FileCheck2, LayoutDashboard, Leaf, LogOut, Menu, ShieldCheck, Sprout, UserCog, X } from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext.jsx'
import { useLanguage } from '../contexts/LanguageContext.jsx'
import Brand from './common/Brand.jsx'
import ConfirmDialog from './common/ConfirmDialog.jsx'
import LanguageToggle from './common/LanguageToggle.jsx'
import ThemeToggle from './common/ThemeToggle.jsx'

const navKeys = [
  { to: '/', labelKey: 'nav.dashboard', icon: LayoutDashboard, end: true },
  { to: '/users', labelKey: 'nav.users', icon: UserCog },
  { to: '/farms', labelKey: 'nav.farms', icon: Sprout },
  { to: '/diseases', labelKey: 'nav.diseases', icon: Leaf },
  { to: '/proposals', labelKey: 'nav.proposals', icon: FileCheck2 },
  { to: '/models', labelKey: 'nav.models', icon: Database },
  { to: '/system', labelKey: 'nav.system', icon: Activity },
]

function AdminSidebar({ onClose, onRequestLogout, user }) {
  const { t } = useLanguage()

  return (
    <div className="flex h-full flex-col bg-leaf-900 dark:bg-slate-950 text-white border-r border-white/10 dark:border-slate-800 transition-colors duration-200">
      <div className="flex h-20 items-center justify-between border-b border-white/10 dark:border-slate-800 px-6">
        <Brand to="/" light />
        {onClose && <button className="rounded-xl p-2 text-white/60 hover:text-white lg:hidden" onClick={onClose}><X size={20} /></button>}
      </div>
      <div className="mx-4 mt-5 flex items-center gap-2 rounded-xl border border-leaf-600/30 dark:border-slate-800 bg-leaf-800/60 dark:bg-slate-900/90 px-3 py-2 text-xs font-semibold text-leaf-100 dark:text-slate-300">
        <ShieldCheck size={16} /> {t('nav.badge_admin')}
      </div>
      <nav className="flex-1 space-y-1 overflow-y-auto px-4 py-5">
        {navKeys.map(({ to, labelKey, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={onClose}
            className={({ isActive }) =>
              `group relative flex items-center gap-3 rounded-xl px-3.5 py-3 text-sm font-semibold transition-all duration-200 ${
                isActive
                  ? 'bg-white text-leaf-900 shadow-sm dark:bg-slate-900 dark:text-emerald-400 dark:ring-1 dark:ring-slate-700 dark:shadow-md'
                  : 'text-leaf-100/70 hover:bg-white/10 hover:text-white dark:text-slate-400 dark:hover:bg-slate-900/80 dark:hover:text-slate-100'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <span
                  className={`absolute left-0 top-2 bottom-2 w-1 rounded-r-full transition-all duration-200 ${
                    isActive ? 'bg-leaf-600 dark:bg-emerald-500 opacity-100' : 'bg-transparent opacity-0'
                  }`}
                />
                <Icon
                  size={19}
                  className={`transition-colors duration-200 ${
                    isActive
                      ? 'text-leaf-700 dark:text-emerald-400'
                      : 'text-leaf-100/60 group-hover:text-leaf-100 dark:text-slate-500 dark:group-hover:text-slate-200'
                  }`}
                />
                <span className="truncate">{t(labelKey)}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-white/10 dark:border-slate-800 p-4">
        <p className="truncate px-3 text-sm font-bold text-white dark:text-slate-100">{user.full_name || user.username}</p>
        <p className="mb-3 truncate px-3 text-xs text-leaf-200/60 dark:text-slate-500">{user.email}</p>
        <button
          onClick={onRequestLogout}
          className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold text-leaf-100/70 transition hover:bg-white/10 hover:text-white dark:text-slate-400 dark:hover:bg-slate-900 dark:hover:text-rose-400"
        >
          <LogOut size={18} /> {t('nav.logout')}
        </button>
      </div>
    </div>
  )
}

export default function AdminLayout() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [logoutConfirm, setLogoutConfirm] = useState(false)
  const { user, logout } = useAuth()
  const { t } = useLanguage()

  // Đăng xuất là thao tác "đóng phiên" — xác nhận trước để tránh bấm nhầm làm mất form đang nhập.
  function confirmLogout() {
    setLogoutConfirm(false)
    setMobileOpen(false)
    logout()
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-72 lg:block"><AdminSidebar user={user} onRequestLogout={() => setLogoutConfirm(true)} /></aside>
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button className="absolute inset-0 bg-slate-950/40" onClick={() => setMobileOpen(false)} aria-label="Đóng menu" />
          <aside className="relative h-full w-[85%] max-w-72"><AdminSidebar user={user} onRequestLogout={() => setLogoutConfirm(true)} onClose={() => setMobileOpen(false)} /></aside>
        </div>
      )}
      <div className="lg:pl-72">
        <header className="sticky top-0 z-20 flex h-20 items-center justify-between border-b border-slate-200 bg-white/90 px-4 backdrop-blur-xl dark:border-slate-800 dark:bg-slate-950/90 sm:px-7">
          <div className="flex items-center gap-3">
            <button className="rounded-xl border border-slate-200 p-2.5 dark:border-slate-700 dark:text-slate-200 lg:hidden" onClick={() => setMobileOpen(true)} aria-label="Mở menu"><Menu size={20} /></button>
            <div>
              <p className="text-xs font-medium text-slate-400 dark:text-slate-500">{t('nav.header_sub')}</p>
              <p className="text-sm font-bold text-slate-800 dark:text-slate-100">{t('nav.header_title')}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <LanguageToggle />
            <ThemeToggle />
            <button className="relative rounded-xl border border-slate-200 p-2.5 text-slate-500 transition hover:border-leaf-300 hover:text-leaf-700 dark:border-slate-700 dark:text-slate-300 dark:hover:border-leaf-600 dark:hover:text-leaf-300" aria-label={t('nav.notifications')} title={t('nav.notifications')}><Bell size={19} /><span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-rose-500" /></button>
          </div>
        </header>
        <main className="p-4 sm:p-7 lg:p-8"><Outlet /></main>
      </div>

      <ConfirmDialog
        open={logoutConfirm}
        onClose={() => setLogoutConfirm(false)}
        onConfirm={confirmLogout}
        title="nav.logout_confirm_title"
        message="nav.logout_confirm_msg"
        confirmLabel="nav.logout"
        tone="danger"
      />
    </div>
  )
}
