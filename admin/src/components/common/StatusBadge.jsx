import { useLanguage } from '../../contexts/LanguageContext.jsx'

const variants = {
  healthy: 'bg-emerald-50 text-emerald-700 ring-emerald-600/15 dark:bg-emerald-900/30 dark:text-emerald-300 dark:ring-emerald-400/20',
  active: 'bg-emerald-50 text-emerald-700 ring-emerald-600/15 dark:bg-emerald-900/30 dark:text-emerald-300 dark:ring-emerald-400/20',
  low: 'bg-emerald-50 text-emerald-700 ring-emerald-600/15 dark:bg-emerald-900/30 dark:text-emerald-300 dark:ring-emerald-400/20',
  attention: 'bg-amber-50 text-amber-700 ring-amber-600/15 dark:bg-amber-900/30 dark:text-amber-300 dark:ring-amber-400/20',
  medium: 'bg-amber-50 text-amber-700 ring-amber-600/15 dark:bg-amber-900/30 dark:text-amber-300 dark:ring-amber-400/20',
  risk: 'bg-rose-50 text-rose-700 ring-rose-600/15 dark:bg-rose-900/30 dark:text-rose-300 dark:ring-rose-400/20',
  high: 'bg-rose-50 text-rose-700 ring-rose-600/15 dark:bg-rose-900/30 dark:text-rose-300 dark:ring-rose-400/20',
  inactive: 'bg-slate-100 text-slate-600 ring-slate-500/15 dark:bg-slate-800 dark:text-slate-300 dark:ring-slate-400/20',
  pending: 'bg-amber-50 text-amber-700 ring-amber-600/15 dark:bg-amber-900/30 dark:text-amber-300 dark:ring-amber-400/20',
  approved: 'bg-emerald-50 text-emerald-700 ring-emerald-600/15 dark:bg-emerald-900/30 dark:text-emerald-300 dark:ring-emerald-400/20',
  rejected: 'bg-rose-50 text-rose-700 ring-rose-600/15 dark:bg-rose-900/30 dark:text-rose-300 dark:ring-rose-400/20',
  production: 'bg-emerald-50 text-emerald-700 ring-emerald-600/15 dark:bg-emerald-900/30 dark:text-emerald-300 dark:ring-emerald-400/20',
  staging: 'bg-sky-50 text-sky-700 ring-sky-600/15 dark:bg-sky-900/30 dark:text-sky-300 dark:ring-sky-400/20',
  archived: 'bg-slate-100 text-slate-600 ring-slate-500/15 dark:bg-slate-800 dark:text-slate-300 dark:ring-slate-400/20',
}

export default function StatusBadge({ value, children }) {
  const { t } = useLanguage()
  const translated = t(`common.${value}`)
  const displayLabel = children || (translated !== `common.${value}` ? translated : value)

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${variants[value] || variants.inactive}`}>
      {displayLabel}
    </span>
  )
}

