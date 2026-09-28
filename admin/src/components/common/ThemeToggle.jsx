import { Moon, Sun } from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext.jsx'

export default function ThemeToggle({ className = '' }) {
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={`rounded-xl border border-slate-200 bg-white p-2.5 text-slate-600 transition hover:border-leaf-300 hover:text-leaf-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:border-leaf-600 dark:hover:text-leaf-300 ${className}`}
      aria-label={isDark ? 'Chuyển sang giao diện sáng' : 'Chuyển sang giao diện tối'}
      title={isDark ? 'Chế độ sáng' : 'Chế độ tối'}
    >
      {isDark ? <Sun size={19} className="text-amber-400" /> : <Moon size={19} />}
    </button>
  )
}
