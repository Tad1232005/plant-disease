import { ChevronDown, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, ChevronsUpDown, Search } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useLanguage } from '../../contexts/LanguageContext.jsx'

function getCellValue(row, key) {
  return key.split('.').reduce((value, part) => value?.[part], row)
}

function getPageNumbers(currentPage, totalPages) {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, i) => i + 1)
  }
  const pages = [1]
  if (currentPage > 3) pages.push('...')
  const start = Math.max(2, currentPage - 1)
  const end = Math.min(totalPages - 1, currentPage + 1)
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  if (currentPage < totalPages - 2) pages.push('...')
  pages.push(totalPages)
  return pages
}

export default function DataTable({
  columns,
  data,
  rowKey = 'id',
  searchPlaceholder,
  searchable = true,
  pageSize = 10,
  pageSizeOptions = [10, 25, 50, 100],
  actions,
  emptyTitle,
  emptyDescription,
}) {
  const { t, language } = useLanguage()
  const isVi = language === 'vi'
  const [query, setQuery] = useState('')
  const [sort, setSort] = useState({ key: '', direction: 'asc' })
  const [page, setPage] = useState(1)
  const [currentPageSize, setCurrentPageSize] = useState(pageSize)

  const resolvedSearchPlaceholder = searchPlaceholder || t('common.search')
  const resolvedEmptyTitle = emptyTitle || t('common.no_data')
  const resolvedEmptyDesc = emptyDescription || t('common.no_data_desc')

  const filteredRows = useMemo(() => {
    const normalizedQuery = query.trim().toLocaleLowerCase(language || 'vi')
    const rows = normalizedQuery
      ? data.filter((row) => columns.some((column) => {
          if (column.searchable === false) return false
          return String(getCellValue(row, column.key) ?? '').toLocaleLowerCase(language || 'vi').includes(normalizedQuery)
        }))
      : data

    if (!sort.key) return rows
    return [...rows].sort((a, b) => {
      const left = getCellValue(a, sort.key)
      const right = getCellValue(b, sort.key)
      const result = String(left ?? '').localeCompare(String(right ?? ''), language || 'vi', { numeric: true })
      return sort.direction === 'asc' ? result : -result
    })
  }, [columns, data, language, query, sort])

  const totalPages = Math.max(1, Math.ceil(filteredRows.length / currentPageSize))
  const startIndex = (page - 1) * currentPageSize
  const endIndex = Math.min(startIndex + currentPageSize, filteredRows.length)
  const visibleRows = filteredRows.slice(startIndex, endIndex)

  useEffect(() => {
    if (page > totalPages) setPage(totalPages)
  }, [page, totalPages])

  function toggleSort(key) {
    setPage(1)
    setSort((current) => current.key === key
      ? { key, direction: current.direction === 'asc' ? 'desc' : 'asc' }
      : { key, direction: 'asc' })
  }

  const pageNumbers = getPageNumbers(page, totalPages)

  return (
    <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-soft dark:border-slate-800 dark:bg-slate-900">
      {searchable && (
        <div className="flex flex-col gap-3 border-b border-slate-100 p-4 dark:border-slate-800 sm:flex-row sm:items-center sm:justify-between sm:p-5">
          <label className="relative w-full max-w-sm">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500" size={18} />
            <input
              value={query}
              onChange={(event) => { setQuery(event.target.value); setPage(1) }}
              className="input-control pl-10"
              placeholder={resolvedSearchPlaceholder}
              aria-label={resolvedSearchPlaceholder}
            />
          </label>
          <div className="flex items-center gap-3 self-end sm:self-auto">
            <span className="text-xs text-slate-500 dark:text-slate-400">
              {isVi ? 'Hiển thị:' : 'Show:'}
            </span>
            <select
              value={currentPageSize}
              onChange={(e) => {
                setCurrentPageSize(Number(e.target.value))
                setPage(1)
              }}
              className="rounded-xl border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs font-semibold text-slate-700 outline-none transition focus:border-leaf-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
            >
              {pageSizeOptions.map((opt) => (
                <option key={opt} value={opt}>
                  {opt} {isVi ? 'dòng' : 'rows'}
                </option>
              ))}
            </select>
            <span className="hidden text-xs text-slate-400 dark:text-slate-500 sm:inline">
              ({filteredRows.length} {t('common.results') || ''})
            </span>
          </div>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] border-collapse text-left">
          <thead>
            <tr className="bg-slate-50/80 dark:bg-slate-800/60">
              {columns.map((column) => (
                <th key={column.key} className={`px-5 py-3.5 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 ${column.className || ''}`}>
                  {column.sortable ? (
                    <button className="inline-flex items-center gap-1.5 hover:text-leaf-700 dark:hover:text-leaf-400" onClick={() => toggleSort(column.key)}>
                      {column.label}
                      {sort.key === column.key ? <ChevronDown className={sort.direction === 'asc' ? 'rotate-180' : ''} size={14} /> : <ChevronsUpDown size={14} />}
                    </button>
                  ) : column.label}
                </th>
              ))}
              {actions && <th className="px-5 py-3.5 text-right text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">{t('common.actions')}</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {visibleRows.map((row) => (
              <tr key={getCellValue(row, rowKey)} className="transition hover:bg-leaf-50/40 dark:hover:bg-slate-800/60">
                {columns.map((column) => {
                  const value = getCellValue(row, column.key)
                  return (
                    <td key={column.key} className={`whitespace-nowrap px-5 py-4 text-sm text-slate-600 dark:text-slate-300 ${column.cellClassName || ''}`}>
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
          <div className="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-slate-100 text-2xl dark:bg-slate-800">🌱</div>
          <p className="font-bold text-slate-800 dark:text-slate-100">{resolvedEmptyTitle}</p>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{resolvedEmptyDesc}</p>
        </div>
      )}

      {filteredRows.length > 0 && (
        <div className="flex flex-col gap-3 border-t border-slate-100 px-4 py-3 dark:border-slate-800 sm:flex-row sm:items-center sm:justify-between sm:px-5">
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {isVi ? (
              <>
                Hiển thị <strong className="text-slate-700 dark:text-slate-200">{filteredRows.length > 0 ? startIndex + 1 : 0} – {endIndex}</strong> trên <strong className="text-slate-700 dark:text-slate-200">{filteredRows.length}</strong> bản ghi
              </>
            ) : (
              <>
                Showing <strong className="text-slate-700 dark:text-slate-200">{filteredRows.length > 0 ? startIndex + 1 : 0} – {endIndex}</strong> of <strong className="text-slate-700 dark:text-slate-200">{filteredRows.length}</strong> items
              </>
            )}
          </p>

          <div className="flex items-center gap-1.5 self-end sm:self-auto">
            {/* Nút Về đầu */}
            <button
              className="rounded-lg p-1.5 text-slate-500 transition hover:bg-slate-100 hover:text-slate-800 disabled:opacity-30 disabled:hover:bg-transparent dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
              disabled={page === 1}
              onClick={() => setPage(1)}
              title={isVi ? 'Trang đầu' : 'First page'}
            >
              <ChevronsLeft size={16} />
            </button>

            {/* Nút Lùi 1 trang */}
            <button
              className="rounded-lg p-1.5 text-slate-500 transition hover:bg-slate-100 hover:text-slate-800 disabled:opacity-30 disabled:hover:bg-transparent dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
              disabled={page === 1}
              onClick={() => setPage((v) => Math.max(1, v - 1))}
              title={isVi ? 'Trang trước' : 'Previous page'}
            >
              <ChevronLeft size={16} />
            </button>

            {/* Dải số trang */}
            <div className="flex items-center gap-1">
              {pageNumbers.map((p, idx) => {
                if (p === '...') {
                  return <span key={`ellipsis-${idx}`} className="px-1 text-xs text-slate-400 dark:text-slate-500">...</span>
                }
                const isActive = p === page
                return (
                  <button
                    key={`page-${p}`}
                    onClick={() => setPage(p)}
                    className={`h-7 min-w-7 rounded-lg px-1.5 text-xs font-bold transition ${
                      isActive
                        ? 'bg-leaf-600 text-white shadow-sm'
                        : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white'
                    }`}
                  >
                    {p}
                  </button>
                )
              })}
            </div>

            {/* Nút Tiến 1 trang */}
            <button
              className="rounded-lg p-1.5 text-slate-500 transition hover:bg-slate-100 hover:text-slate-800 disabled:opacity-30 disabled:hover:bg-transparent dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
              disabled={page === totalPages}
              onClick={() => setPage((v) => Math.min(totalPages, v + 1))}
              title={isVi ? 'Trang sau' : 'Next page'}
            >
              <ChevronRight size={16} />
            </button>

            {/* Nút Tới trang cuối */}
            <button
              className="rounded-lg p-1.5 text-slate-500 transition hover:bg-slate-100 hover:text-slate-800 disabled:opacity-30 disabled:hover:bg-transparent dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
              disabled={page === totalPages}
              onClick={() => setPage(totalPages)}
              title={isVi ? 'Trang cuối' : 'Last page'}
            >
              <ChevronsRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
