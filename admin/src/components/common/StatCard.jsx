import { ArrowUpRight } from 'lucide-react'

export default function StatCard({ label, value, note, icon: Icon, tone = 'green' }) {
  const tones = {
    green: 'bg-leaf-50 text-leaf-700 dark:bg-leaf-900/40 dark:text-leaf-300',
    blue: 'bg-sky-50 text-sky-700 dark:bg-sky-900/40 dark:text-sky-300',
    amber: 'bg-amber-50 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
    purple: 'bg-violet-50 text-violet-700 dark:bg-violet-900/40 dark:text-violet-300',
  }

  return (
    <div className="card p-5">
      <div className="flex items-start justify-between gap-4">
        <span className={`grid h-11 w-11 place-items-center rounded-2xl ${tones[tone] || tones.green}`}>
          <Icon size={21} />
        </span>
        {note && <span className="inline-flex items-center gap-1 text-xs font-semibold text-leaf-600 dark:text-leaf-400"><ArrowUpRight size={13} />{note}</span>}
      </div>
      <p className="mt-5 text-2xl font-extrabold text-slate-900 dark:text-slate-50">{value}</p>
      <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{label}</p>
    </div>
  )
}
