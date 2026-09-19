export default function MiniBarChart({ values = [], labels = [], color = 'bg-leaf-500', height = 'h-52' }) {
  const maximum = Math.max(...values, 1)
  return (
    <div className={`flex ${height} items-end gap-2 border-b border-slate-100 px-1 pt-6`} role="img" aria-label={`Biểu đồ gồm ${values.length} cột`}>
      {values.map((value, index) => (
        <div key={`${labels[index] || index}-${value}`} className="group flex h-full flex-1 flex-col items-center justify-end gap-2">
          <span className="text-[10px] font-bold text-slate-400 opacity-0 transition group-hover:opacity-100">{value}</span>
          <div className={`w-full max-w-10 rounded-t-lg ${color} transition hover:brightness-90`} style={{ height: `${Math.max((value / maximum) * 82, 6)}%` }} />
          <span className="text-[10px] font-medium text-slate-400">{labels[index] || `T${index + 2}`}</span>
        </div>
      ))}
    </div>
  )
}
