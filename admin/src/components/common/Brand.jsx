import { Leaf } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function Brand({ to = '/', light = false, compact = false }) {
  return (
    <Link to={to} className="inline-flex items-center gap-3">
      <span className={`grid h-10 w-10 place-items-center rounded-2xl ${light ? 'bg-white/15 text-white' : 'bg-leaf-600 text-white'} shadow-sm`}>
        <Leaf size={21} strokeWidth={2.4} />
      </span>
      {!compact && (
        <span>
          <span className={`block text-base font-extrabold tracking-tight ${light ? 'text-white' : 'text-slate-900'}`}>
            PlantCare <span className={light ? 'text-leaf-200' : 'text-leaf-600'}>AI</span>
          </span>
          <span className={`block text-[10px] font-medium tracking-[0.16em] ${light ? 'text-white/65' : 'text-slate-400'}`}>
            SMART PLANT HEALTH
          </span>
        </span>
      )}
    </Link>
  )
}
