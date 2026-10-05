import { Lock, Plus, Unlock, UserCheck, UserPlus, UserX } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import CrudForm from '../components/common/CrudForm.jsx'
import DataTable from '../components/common/DataTable.jsx'
import Modal from '../components/common/Modal.jsx'
import PageHeader from '../components/common/PageHeader.jsx'
import StatusBadge from '../components/common/StatusBadge.jsx'
import { useLanguage } from '../contexts/LanguageContext.jsx'
import { adminUsersApi } from '../services/auth.js'

function unwrapList(payload) {
  if (Array.isArray(payload)) return payload
  return payload?.items || payload?.users || payload?.data || []
}

export default function UsersPage() {
  const { t, language } = useLanguage()
  const isVi = language === 'vi'

  const [users, setUsers] = useState([])
  const [message, setMessage] = useState('')
  const [formOpen, setFormOpen] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    let active = true
    adminUsersApi.list()
      .then((payload) => { if (active) setUsers(unwrapList(payload)) })
      .catch((error) => { if (active) setMessage(error?.response?.data?.detail || 'Không thể tải danh sách người dùng.') })
    return () => { active = false }
  }, [])

  const userFields = useMemo(() => [
    { name: 'full_name', label: isVi ? 'Họ và tên' : 'Full Name', placeholder: isVi ? 'Nguyễn Văn A' : 'John Doe', fullWidth: true },
    { name: 'username', label: isVi ? 'Tên đăng nhập' : 'Username', placeholder: 'tech.tran', required: true },
    { name: 'email', label: 'Email', type: 'email', placeholder: 'user@plantcare.vn', required: true },
    { name: 'password', label: isVi ? 'Mật khẩu khởi tạo' : 'Password', type: 'password', placeholder: '••••••••', minLength: 8, required: true },
    {
      name: 'role',
      label: isVi ? 'Vai trò quản trị' : 'Role',
      type: 'select',
      options: [
        { value: 'manager', label: isVi ? 'Quản lý nông trại (Manager)' : 'Farm Manager' },
        { value: 'technician', label: isVi ? 'Kỹ thuật viên (Technician)' : 'Technician' },
      ],
      required: true,
    },
  ], [isVi])

  async function handleCreateUser(values) {
    setLoading(true)
    setMessage('')
    try {
      const created = await adminUsersApi.create(values)
      setUsers((prev) => [created, ...prev])
      setFormOpen(false)
      setMessage(isVi ? 'Đã tạo tài khoản thành công.' : 'User created successfully.')
    } catch (err) {
      setMessage(err?.response?.data?.detail || (isVi ? 'Không thể tạo tài khoản.' : 'Failed to create user.'))
    } finally {
      setLoading(false)
    }
  }

  async function toggleStatus(row) {
    const nextStatus = row.status === 'active' ? 'suspended' : 'active'
    const reason = nextStatus === 'suspended' ? 'Tạm khóa bởi Admin' : 'Kích hoạt lại bởi Admin'
    try {
      const updated = await adminUsersApi.changeStatus(row.id, { status: nextStatus, reason })
      setUsers((prev) => prev.map((u) => u.id === row.id ? { ...u, status: nextStatus } : u))
      setMessage(isVi ? `Đã cập nhật trạng thái người dùng thành: ${nextStatus}` : `User status updated to: ${nextStatus}`)
    } catch (err) {
      setMessage(err?.response?.data?.detail || (isVi ? 'Không thể cập nhật trạng thái.' : 'Failed to change status.'))
    }
  }

  const columns = [
    { key: 'full_name', label: t('users.col_user'), sortable: true, render: (value, row) => <div><p className="font-bold text-slate-800 dark:text-slate-100">{value || row.username}</p><p className="mt-0.5 text-xs text-slate-400 dark:text-slate-500">@{row.username}</p></div> },
    { key: 'email', label: t('users.col_email'), sortable: true },
    { key: 'role', label: t('users.col_role'), sortable: true, render: (value) => <span className="rounded-full bg-sky-50 px-2.5 py-1 text-xs font-semibold text-sky-700 dark:bg-sky-900/40 dark:text-sky-300">{t(`roles.${value}`) || value}</span> },
    { key: 'status', label: t('users.col_status'), render: (value) => <StatusBadge value={value} /> },
  ]

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader
        eyebrow={t('users.eyebrow')}
        title={t('users.title')}
        description={t('users.desc')}
        action={
          <button className="btn-primary" onClick={() => setFormOpen(true)}>
            <Plus size={18} /> {isVi ? 'Thêm tài khoản' : 'Add User'}
          </button>
        }
      />
      {message && <p className="mb-5 rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">{message}</p>}
      <DataTable
        columns={columns}
        data={users}
        searchPlaceholder={t('users.search_placeholder')}
        actions={(row) => (
          <button
            onClick={() => toggleStatus(row)}
            className={`rounded-lg p-2 text-xs font-semibold transition ${
              row.status === 'active'
                ? 'text-slate-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/40'
                : 'text-slate-400 hover:bg-emerald-50 hover:text-emerald-600 dark:hover:bg-emerald-950/40'
            }`}
            title={row.status === 'active' ? (isVi ? 'Khóa tài khoản' : 'Suspend account') : (isVi ? 'Mở khóa tài khoản' : 'Activate account')}
          >
            {row.status === 'active' ? <Lock size={17} /> : <Unlock size={17} />}
          </button>
        )}
      />

      <Modal open={formOpen} onClose={() => setFormOpen(false)} title={isVi ? 'Tạo tài khoản quản trị mới' : 'Create Admin/Manager User'}>
        <CrudForm
          fields={userFields}
          defaultValues={{ role: 'manager' }}
          onSubmit={handleCreateUser}
          onCancel={() => setFormOpen(false)}
          submitLabel={loading ? (isVi ? 'Đang tạo...' : 'Creating...') : (isVi ? 'Tạo tài khoản' : 'Create Account')}
        />
      </Modal>
    </div>
  )
}

