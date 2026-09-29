import { useEffect, useState } from 'react'
import DataTable from '../components/common/DataTable.jsx'
import PageHeader from '../components/common/PageHeader.jsx'
import StatusBadge from '../components/common/StatusBadge.jsx'
import { useLanguage } from '../contexts/LanguageContext.jsx'
import { adminUsersApi } from '../services/auth.js'

function unwrapList(payload) {
  if (Array.isArray(payload)) return payload
  return payload?.items || payload?.users || payload?.data || []
}

export default function UsersPage() {
  const { t } = useLanguage()
  const [users, setUsers] = useState([])
  const [message, setMessage] = useState('')

  useEffect(() => {
    let active = true
    adminUsersApi.list()
      .then((payload) => { if (active) setUsers(unwrapList(payload)) })
      .catch((error) => { if (active) setMessage(error?.response?.data?.detail || 'Không thể tải danh sách người dùng.') })
    return () => { active = false }
  }, [])

  const columns = [
    { key: 'full_name', label: t('users.col_user'), sortable: true, render: (value, row) => <div><p className="font-bold text-slate-800 dark:text-slate-100">{value || row.username}</p><p className="mt-0.5 text-xs text-slate-400 dark:text-slate-500">@{row.username}</p></div> },
    { key: 'email', label: t('users.col_email'), sortable: true },
    { key: 'role', label: t('users.col_role'), sortable: true, render: (value) => <span className="rounded-full bg-sky-50 px-2.5 py-1 text-xs font-semibold text-sky-700 dark:bg-sky-900/40 dark:text-sky-300">{t(`roles.${value}`)}</span> },
    { key: 'status', label: t('users.col_status'), render: (value) => <StatusBadge value={value} /> },
  ]
  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader eyebrow={t('users.eyebrow')} title={t('users.title')} description={t('users.desc')} />
      {message && <p className="mb-5 rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">{t(message)}</p>}
      <DataTable columns={columns} data={users} searchPlaceholder={t('users.search_placeholder')} />
    </div>
  )
}

