import { LockKeyhole, UserCog } from 'lucide-react'
import DataTable from '../components/common/DataTable.jsx'
import PageHeader from '../components/common/PageHeader.jsx'
import StatusBadge from '../components/common/StatusBadge.jsx'
import { useLanguage } from '../contexts/LanguageContext.jsx'
import { demoUsers } from '../data/demoData.js'

export default function UsersPage() {
  const { t } = useLanguage()
  const rows = Object.values(demoUsers).map(({ password: _, ...user }, index) => ({ ...user, status: index === 3 ? 'active' : 'active' }))
  const columns = [
    { key: 'full_name', label: t('users.col_user'), sortable: true, render: (value, row) => <div><p className="font-bold text-slate-800 dark:text-slate-100">{value}</p><p className="mt-0.5 text-xs text-slate-400 dark:text-slate-500">@{row.username}</p></div> },
    { key: 'email', label: t('users.col_email'), sortable: true },
    { key: 'role', label: t('users.col_role'), sortable: true, render: (value) => <span className="rounded-full bg-sky-50 px-2.5 py-1 text-xs font-semibold text-sky-700 dark:bg-sky-900/40 dark:text-sky-300">{t(`roles.${value}`)}</span> },
    { key: 'status', label: t('users.col_status'), render: (value) => <StatusBadge value={value} /> },
  ]
  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader eyebrow={t('users.eyebrow')} title={t('users.title')} description={t('users.desc')} />
      <DataTable columns={columns} data={rows} searchPlaceholder={t('users.search_placeholder')} actions={() => <button className="rounded-lg p-2 text-slate-400 hover:bg-leaf-50 hover:text-leaf-700 dark:hover:bg-slate-800 dark:hover:text-leaf-300" aria-label={t('common.edit')}><UserCog size={17} /></button>} />
      <div className="mt-5 flex gap-3 rounded-2xl border border-amber-100 bg-amber-50 p-4 text-sm text-amber-800 dark:border-amber-900/40 dark:bg-amber-950/40 dark:text-amber-200">
        <LockKeyhole className="mt-0.5 shrink-0" size={18} />
        <p>{t('users.notice')}</p>
      </div>
    </div>
  )
}

