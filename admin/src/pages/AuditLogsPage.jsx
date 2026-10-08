import { History, User } from 'lucide-react'
import { useEffect, useState } from 'react'
import DataTable from '../components/common/DataTable.jsx'
import PageHeader from '../components/common/PageHeader.jsx'
import StatusBadge from '../components/common/StatusBadge.jsx'
import { useLanguage } from '../contexts/LanguageContext.jsx'
import { adminAuditApi } from '../services/audit.js'
import { getApiError } from '../services/client.js'

function formatTime(value, isVi) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return date.toLocaleString(isVi ? 'vi-VN' : 'en-US', { hour12: false })
}

function formatDetails(details) {
  if (!details || typeof details !== 'object') return '—'
  const entries = Object.entries(details)
  if (!entries.length) return '—'
  return entries.map(([key, value]) => `${key}: ${typeof value === 'object' ? JSON.stringify(value) : String(value)}`).join(' · ')
}

export default function AuditLogsPage() {
  const { t, language } = useLanguage()
  const isVi = language === 'vi'

  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')

  useEffect(() => {
    let active = true
    setLoading(true)
    adminAuditApi.list({ limit: 100 })
      .then((payload) => { if (active) setLogs(Array.isArray(payload) ? payload : []) })
      .catch((error) => { if (active) setMessage(getApiError(error, t('audit.err_load'))) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [t])

  const columns = [
    {
      key: 'created_at',
      label: isVi ? 'Thời gian' : 'Timestamp',
      sortable: true,
      render: (val) => <span className="font-mono text-xs text-slate-500">{formatTime(val, isVi)}</span>,
    },
    {
      key: 'actor_name',
      label: isVi ? 'Người thực hiện' : 'Actor',
      sortable: true,
      render: (val) => (
        <span className="inline-flex items-center gap-1.5 font-bold text-slate-700 dark:text-slate-200">
          <User size={14} className="text-leaf-600" /> @{val}
        </span>
      ),
    },
    {
      key: 'action',
      label: isVi ? 'Hành động' : 'Action',
      sortable: true,
      render: (val) => (
        <span className="rounded-lg bg-slate-100 dark:bg-slate-800 px-2.5 py-1 font-mono text-xs font-bold text-slate-800 dark:text-slate-200">
          {val}
        </span>
      ),
    },
    {
      key: 'resource_type',
      label: isVi ? 'Tài nguyên' : 'Resource',
      render: (val, row) => (
        <span className="text-xs text-slate-500">
          {val} #{row.resource_id}
        </span>
      ),
    },
    {
      key: 'details',
      label: isVi ? 'Chi tiết sự kiện' : 'Event Details',
      render: (val) => <span className="text-xs text-slate-600 dark:text-slate-300">{formatDetails(val)}</span>,
    },
    {
      key: 'outcome',
      label: isVi ? 'Trạng thái' : 'Status',
      render: (val) => <StatusBadge value={val === 'success' ? 'active' : 'pending'} />,
    },
  ]

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader
        eyebrow={isVi ? 'Bảo mật & Giám sát' : 'Security & Auditing'}
        title={isVi ? 'Nhật ký kiểm toán (Audit Logs)' : 'System Audit Logs'}
        description={
          isVi
            ? 'Theo dõi toàn bộ hoạt động nhạy cảm trong hệ thống: kích hoạt model, phê duyệt bệnh cây, thay đổi phân quyền.'
            : 'Track all sensitive activities in the system: model activation, proposal approvals, and permission changes.'
        }
      />
      {loading && <p className="mb-5 text-sm text-slate-500 dark:text-slate-400">{t('common.loading')}</p>}
      {message && <p className="mb-5 rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">{message}</p>}

      <div className="mt-6">
        <DataTable
          columns={columns}
          data={logs}
          searchPlaceholder={isVi ? 'Tìm theo hành động hoặc người thực hiện...' : 'Search by action or actor...'}
          emptyTitle={isVi ? 'Chưa có sự kiện nào' : 'No events yet'}
          emptyDescription={isVi ? 'Các thao tác quản trị sẽ được ghi lại tại đây.' : 'Admin actions will be recorded here.'}
        />
      </div>
    </div>
  )
}
