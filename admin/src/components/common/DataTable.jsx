import { ChevronDown, ChevronLeft, ChevronRight, ChevronsUpDown, Search } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'

function getCellValue(row, key) {
  return key.split('.').reduce((value, part) => value?.[part], row)
}

export default function DataTable({
  columns,
  data,
  rowKey = 'id',
  searchPlaceholder = 'Tìm kiếm...',
  searchable = true,
  pageSize = 6,
  actions,
  emptyTitle = 'Chưa có dữ liệu',
  emptyDescription = 'Dữ liệu mới sẽ xuất hiện tại đây.',
}) {
  const [query, setQuery] = useState('')
  const [sort, setSort] = useState({ key: '', direction: 'asc' })
  const [page, setPage] = useState(1)

  const filteredRows = useMemo(() => {
    const normalizedQuery = query.trim().toLocaleLowerCase('vi')
    const rows = normalizedQuery
      ? data.filter((row) => columns.some((column) => {
          if (column.searchable === false) return false
          return String(getCellValue(row, column.key) ?? '').toLocaleLowerCase('vi').includes(normalizedQuery)
        }))
      : data

    if (!sort.key) return rows
    return [...rows].sort((a, b) => {
      const left = getCellValue(a, sort.key)
      const right = getCellValue(b, sort.key)
      const result = String(left ?? '').localeCompare(String(right ?? ''), 'vi', { numeric: true })
      return sort.direction === 'asc' ? result : -result
    })
  }, [columns, data, query, sort])

  const totalPages = Math.max(1, Math.ceil(filteredRows.length / pageSize))
  const visibleRows = filteredRows.slice((page - 1) * pageSize, page * pageSize)

  useEffect(() => {
    if (page > totalPages) setPage(totalPages)
  }, [page, totalPages])

  function toggleSort(key) {
    setPage(1)
    setSort((current) => current.key === key
      ? { key, direction: current.direction === 'asc' ? 'desc' : 'asc' }
      : { key, direction: 'asc' })
  }

  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-soft">
      {searchable && (
        <div className="flex items-center justify-between border-b border-slate-100 p-4 sm:p-5">
          <label className="relative w-full max-w-sm">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input
              value={query}
              onChange={(event) => { setQuery(event.target.value); setPage(1) }}
              className="input-control pl-10"
              placeholder={searchPlaceholder}
              aria-label={searchPlaceholder}
            />
          </label>
          <span className="ml-4 hidden text-sm text-slate-400 sm:block">{filteredRows.length} kết quả</span>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] border-collapse text-left">
          <thead>
            <tr className="bg-slate-50/80">
              {columns.map((column) => (
                <th key={column.key} className={`px-5 py-3.5 text-xs font-bold uppercase tracking-wider text-slate-500 ${column.className || ''}`}>
                  {column.sortable ? (
                    <button className="inline-flex items-center gap-1.5 hover:text-leaf-700" onClick={() => toggleSort(column.key)}>
                      {column.label}
                      {sort.key === column.key ? <ChevronDown className={sort.direction === 'asc' ? 'rotate-180' : ''} size={14} /> : <ChevronsUpDown size={14} />}
                    </button>
                  ) : column.label}
                </th>
              ))}
              {actions && <th className="px-5 py-3.5 text-right text-xs font-bold uppercase tracking-wider text-slate-500">Thao tác</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {visibleRows.map((row) => (
              <tr key={getCellValue(row, rowKey)} className="transition hover:bg-leaf-50/40">
                {columns.map((column) => {
                  const value = getCellValue(row, column.key)
                  return (
                    <td key={column.key} className={`whitespace-nowrap px-5 py-4 text-sm text-slate-600 ${column.cellClassName || ''}`}>
                      {column.render ? column.render(value, row) : value}
                    </td>
                  )
                })}
                {actions && <td className="whitespace-nowrap px-5 py-4 text-right">{actions(row)}</td>}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {!visibleRows.length && (
        <div className="px-5 py-16 text-center">
          <div className="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-slate-100 text-2xl">🌱</div>
          <p className="font-bold text-slate-800">{emptyTitle}</p>
          <p className="mt-1 text-sm text-slate-500">{emptyDescription}</p>
        </div>
      )}

      {filteredRows.length > 0 && (
        <div className="flex items-center justify-between border-t border-slate-100 px-4 py-3 sm:px-5">
          <p className="text-xs text-slate-500">
            Trang <strong className="text-slate-700">{page}</strong> / {totalPages}
          </p>
          <div className="flex gap-2">
            <button className="btn-secondary !p-2" disabled={page === 1} onClick={() => setPage((value) => value - 1)} aria-label="Trang trước">
              <ChevronLeft size={17} />
            </button>
            <button className="btn-secondary !p-2" disabled={page === totalPages} onClick={() => setPage((value) => value + 1)} aria-label="Trang sau">
              <ChevronRight size={17} />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
