import { Globe } from 'lucide-react'
import { useLanguage } from '../../contexts/LanguageContext.jsx'

export default function LanguageToggle({ className = '' }) {
  const { language, toggleLanguage } = useLanguage()

  return (
    <button
      type="button"
      onClick={toggleLanguage}
      className={`inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-2.5 py-2 text-xs font-bold text-slate-700 transition hover:border-leaf-300 hover:text-leaf-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-leaf-600 dark:hover:text-leaf-300 ${className}`}
      aria-label={language === 'vi' ? 'Chuyển sang tiếng Anh (Switch to English)' : 'Chuyển sang tiếng Việt'}
      title={language === 'vi' ? 'Chuyển sang Tiếng Anh' : 'Switch to Vietnamese'}
    >
      <Globe size={16} className="text-leaf-600 dark:text-emerald-400" />
      <span className="tracking-wide">{language === 'vi' ? 'VI' : 'EN'}</span>
    </button>
  )
}
