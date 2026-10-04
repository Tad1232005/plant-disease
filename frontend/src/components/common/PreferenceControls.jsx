import { Languages, Moon, Sun } from 'lucide-react'
import { usePreferences } from '../../contexts/PreferencesContext.jsx'

export default function PreferenceControls({ compact = false }) {
  const { language, setLanguage, theme, toggleTheme, t } = usePreferences()
  return (
    <div className="flex items-center gap-1.5">
      <button type="button" onClick={() => setLanguage(language === 'vi' ? 'en' : 'vi')} className="inline-flex h-10 items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-2.5 text-xs font-bold text-slate-600 transition hover:border-leaf-300 hover:text-leaf-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200" aria-label={t('preferences.language')} title={t('preferences.language')}>
        <Languages size={17} /><span className={compact ? 'hidden sm:inline' : ''}>{language === 'vi' ? 'VI' : 'EN'}</span>
      </button>
      <button type="button" onClick={toggleTheme} className="grid h-10 w-10 place-items-center rounded-xl border border-slate-200 bg-white text-slate-600 transition hover:border-leaf-300 hover:text-leaf-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200" aria-label={theme === 'dark' ? t('preferences.light') : t('preferences.dark')} title={theme === 'dark' ? t('preferences.light') : t('preferences.dark')}>
        {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
      </button>
    </div>
  )
}
