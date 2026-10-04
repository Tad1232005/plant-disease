import { History, LogIn, ShieldCheck } from 'lucide-react'
import { Link } from 'react-router-dom'
import Brand from '../components/common/Brand.jsx'
import PreferenceControls from '../components/common/PreferenceControls.jsx'
import { usePreferences } from '../contexts/PreferencesContext.jsx'

export default function GuestLayout({ children }) {
  const { t } = usePreferences()

  return (
    <div className="min-h-screen bg-[#f7faf8] dark:bg-slate-950">
      <header className="sticky top-0 z-30 border-b border-slate-100 bg-white/90 backdrop-blur-xl dark:border-slate-800 dark:bg-slate-950/90">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-3 px-4 sm:h-20 sm:px-6">
          <Brand to="/" />
          <div className="flex items-center gap-2">
            <PreferenceControls compact />
            <Link to="/login" className="btn-secondary hidden sm:inline-flex"><LogIn size={16} />{t('common.login')}</Link>
            <Link to="/register" className="btn-primary hidden md:inline-flex">{t('common.register')}</Link>
          </div>
        </div>
      </header>

      <main className="px-4 py-6 pb-28 sm:px-6 sm:py-8">
        {children}
      </main>

      <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-slate-200 bg-white/95 px-3 pb-[max(.75rem,env(safe-area-inset-bottom))] pt-2 backdrop-blur-xl dark:border-slate-800 dark:bg-slate-950/95 sm:hidden">
        <div className="mx-auto grid max-w-md grid-cols-2 gap-2">
          <div className="flex items-center justify-center gap-2 rounded-xl bg-leaf-50 px-3 py-2.5 text-xs font-bold text-leaf-700 dark:bg-leaf-950/40 dark:text-leaf-300">
            <ShieldCheck size={17} />{t('landing.guestTitle')}
          </div>
          <Link to="/login" className="flex items-center justify-center gap-2 rounded-xl border border-slate-200 px-3 py-2.5 text-xs font-bold text-slate-700 dark:border-slate-700 dark:text-slate-200">
            <History size={17} />{t('guest.saveHistory')}
          </Link>
        </div>
      </nav>
    </div>
  )
}
