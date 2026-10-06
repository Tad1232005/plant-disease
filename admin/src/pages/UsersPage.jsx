import { Ban, Eye, Lock, Plus, RotateCcw, Unlock, UserCheck, UserPlus, UserX, Users } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import CrudForm from '../components/common/CrudForm.jsx'
import DataTable from '../components/common/DataTable.jsx'
import Modal from '../components/common/Modal.jsx'
import PageHeader from '../components/common/PageHeader.jsx'
import StatCard from '../components/common/StatCard.jsx'
import StatusBadge from '../components/common/StatusBadge.jsx'
import { useAuth } from '../contexts/AuthContext.jsx'
import { useLanguage } from '../contexts/LanguageContext.jsx'
import { adminUsersApi } from '../services/auth.js'
import { getApiError } from '../services/client.js'

function unwrapList(payload) {
  if (Array.isArray(payload)) return payload
  return payload?.items || payload?.users || payload?.data || []
}

export default function UsersPage() {
  const { t, language } = useLanguage()
  const { user: currentUser } = useAuth()
  const isVi = language === 'vi'

  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [formOpen, setFormOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const [roleFilter, setRoleFilter] = useState('all')
  const [statusTarget, setStatusTarget] = useState(null)
  const [reason, setReason] = useState('')
  const [statusSaving, setStatusSaving] = useState(false)
  const [detailTarget, setDetailTarget] = useState(null)
  const [detailUser, setDetailUser] = useState(null)
  // Backend chỉ trả created_by dạng số id; khi mở detail sẽ resolve thêm thông tin người tạo.
  const [detailCreator, setDetailCreator] = useState(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    let active = true
    setLoading(true)
    adminUsersApi.list(roleFilter === 'all' ? undefined : { role: roleFilter })
      .then((payload) => { if (active) setUsers(unwrapList(payload)) })
      .catch((error) => { if (active) setMessage(getApiError(error, t('users.err_load'))) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [roleFilter, t])

  // Admin chỉ được cấp Technician hoặc Manager — BE từ chối role khác bằng 403/422.
  const createFields = [
    { name: 'username', label: t('users.field_username'), placeholder: t('users.ph_username'), minLength: 3 },
    { name: 'email', label: t('users.field_email'), placeholder: t('users.ph_email'), type: 'email', required: false, hint: t('users.hint_email') },
    { name: 'password', label: t('users.field_password'), placeholder: t('users.ph_password'), type: 'password', minLength: 8, hint: t('users.hint_password') },
    { name: 'full_name', label: t('users.field_full_name'), placeholder: t('users.ph_full_name'), required: false, fullWidth: true },
    { name: 'role', label: t('users.field_role'), type: 'select', options: [{ value: 'technician', label: t('roles.technician') }, { value: 'manager', label: t('roles.manager') }] },
  ]

  async function saveUser(values) {
    setSaving(true)
    try {
      const created = await adminUsersApi.create({
        username: values.username.trim(),
        email: values.email?.trim() ? values.email.trim() : null,
        password: values.password,
        full_name: values.full_name?.trim() ? values.full_name.trim() : null,
        role: values.role,
      })
      setUsers((items) => [created, ...items])
      setFormOpen(false)
      setMessage(t('users.msg_created', { name: created.username }))
    } catch (error) {
      setMessage(getApiError(error, t('users.err_create')))
    } finally {
      setSaving(false)
    }
  }

  function openStatus(row) {
    setStatusTarget(row)
    setReason('')
    setMessage('')
  }

  async function confirmStatus() {
    if (!statusTarget || !reason.trim() || statusSaving) return
    const nextStatus = statusTarget.status === 'active' ? 'suspended' : 'active'
    setStatusSaving(true)
    try {
      const updated = await adminUsersApi.setStatus(statusTarget.id, { status: nextStatus, reason: reason.trim() })
      setUsers((items) => items.map((item) => item.id === updated.id ? updated : item))
      setStatusTarget(null)
      setReason('')
      setMessage(t(nextStatus === 'suspended' ? 'users.msg_suspended' : 'users.msg_activated', { name: updated.username }))
    } catch (error) {
      setMessage(getApiError(error, t('users.err_status')))
    } finally {
      setStatusSaving(false)
    }
  }

  async function openDetail(row) {
    setDetailTarget(row)
    setDetailUser(row)
    setDetailCreator(null)
    setDetailLoading(true)
    setMessage('')
    try {
      const fresh = await adminUsersApi.get(row.id)
      setDetailUser(fresh)
      setUsers((items) => items.map((item) => item.id === fresh.id ? fresh : item))
      // Resolve người tạo: "Tên (Role)" thay vì hiển thị số id.
      if (fresh.created_by != null) {
        try {
          const creator = await adminUsersApi.get(fresh.created_by)
          setDetailCreator(creator)
        } catch {
          // Người tạo có thể đã bị xóa/đổi quyền — giữ id làm fallback, không chặn modal.
          setDetailCreator(null)
        }
      }
    } catch (error) {
      setMessage(getApiError(error, t('users.err_detail')))
    } finally {
      setDetailLoading(false)
    }
  }

  function closeDetail() {
    setDetailTarget(null)
    setDetailUser(null)
    setDetailCreator(null)
    setDetailLoading(false)
  }

  const activeCount = users.filter((item) => item.status === 'active').length
  const suspendedCount = users.filter((item) => item.status === 'suspended').length
  const suspending = statusTarget?.status === 'active'

  // "Tên người tạo (Role)" — fallback về số id nếu không resolve được (vd: đã bị xóa).
  function formatCreatedBy(user, creator) {
    if (user.created_by == null) return '—'
    if (!creator) return `#${user.created_by}`
    const name = creator.full_name || creator.username
    return `${name} (${t(`roles.${creator.role}`)})`
  }

  const columns = [
    { key: 'full_name', label: t('users.col_user'), sortable: true, render: (value, row) => <div><p className="font-bold text-slate-800 dark:text-slate-100">{value || row.username}</p><p className="mt-0.5 text-xs text-slate-400 dark:text-slate-500">@{row.username}</p></div> },
    { key: 'email', label: t('users.col_email'), sortable: true, render: (value) => value || '—' },
    { key: 'role', label: t('users.col_role'), sortable: true, render: (value) => <span className="rounded-full bg-sky-50 px-2.5 py-1 text-xs font-semibold text-sky-700 dark:bg-sky-900/40 dark:text-sky-300">{t(`roles.${value}`)}</span> },
    { key: 'status', label: t('users.col_status'), render: (value) => <StatusBadge value={value} /> },
  ]

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader
        eyebrow={t('users.eyebrow')}
        title={t('users.title')}
        description={t('users.desc')}
        action={<button className="btn-primary" onClick={() => { setMessage(''); setFormOpen(true) }}><Plus size={18} /> {t('users.add_btn')}</button>}
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <StatCard icon={Users} label={t('users.stat_total')} value={loading ? '—' : users.length} tone="blue" />
        <StatCard icon={UserCheck} label={t('users.stat_active')} value={loading ? '—' : activeCount} />
        <StatCard icon={UserX} label={t('users.stat_suspended')} value={loading ? '—' : suspendedCount} tone="amber" />
      </div>

      {loading && <p className="mb-5 text-sm text-slate-500 dark:text-slate-400">{t('common.loading')}</p>}
      {message && <p className="mb-5 rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">{t(message)}</p>}

      <div className="mb-4 flex items-center gap-3">
        <label className="text-sm font-semibold text-slate-600 dark:text-slate-300" htmlFor="user-role-filter">{t('users.filter_role')}</label>
        <select
          id="user-role-filter"
          className="input-control max-w-[220px]"
          value={roleFilter}
          onChange={(event) => setRoleFilter(event.target.value)}
        >
          <option value="all">{t('users.filter_all')}</option>
          <option value="admin">{t('roles.admin')}</option>
          <option value="manager">{t('roles.manager')}</option>
          <option value="technician">{t('roles.technician')}</option>
          <option value="user">{t('roles.user')}</option>
        </select>
      </div>

      {message && <p className="mb-5 rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">{message}</p>}
      <DataTable
        columns={columns}
        data={users}
        searchPlaceholder={t('users.search_placeholder')}
        actions={(row) => {
          const isSelf = row.id === currentUser?.id
          const locking = row.status === 'active'
          const selfLock = isSelf && locking
          return (
            <span className="inline-flex gap-1">
              <button
                type="button"
                onClick={() => openDetail(row)}
                className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200"
                aria-label={t('users.action_view')}
                title={t('users.action_view')}
              >
                <Eye size={17} />
              </button>
              <button
                type="button"
                disabled={saving || statusSaving || selfLock}
                onClick={() => openStatus(row)}
                className={`rounded-lg p-2 disabled:opacity-30 ${locking
                  ? 'text-slate-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/40 dark:hover:text-rose-400'
                  : 'text-slate-400 hover:bg-leaf-50 hover:text-leaf-700 dark:hover:bg-slate-800 dark:hover:text-leaf-300'}`}
                aria-label={locking ? t('users.action_lock') : t('users.action_unlock')}
                title={selfLock ? t('users.self_disable') : (locking ? t('users.action_lock') : t('users.action_unlock'))}
              >
                {locking ? <Ban size={17} /> : <RotateCcw size={17} />}
              </button>
            </span>
          )
        }}
      />

      <Modal open={formOpen} onClose={() => setFormOpen(false)} title={t('users.modal_create')} description={t('users.modal_desc')} size="xl">
        <CrudForm fields={createFields} defaultValues={{ role: 'technician' }} onSubmit={saveUser} onCancel={() => setFormOpen(false)} submitLabel={t('users.save_btn')} loading={saving} />
      </Modal>

      <Modal
        open={Boolean(statusTarget)}
        onClose={() => { setStatusTarget(null); setReason('') }}
        title={t(suspending ? 'users.status_suspend_title' : 'users.status_activate_title')}
        description={t(suspending ? 'users.status_suspend_desc' : 'users.status_activate_desc')}
        size="sm"
      >
        <label className="block">
          <span className="mb-2 block text-sm font-semibold text-slate-700 dark:text-slate-200">
            {t('users.field_reason')} <span className="text-rose-500">*</span>
          </span>
          <textarea
            rows={3}
            className="input-control resize-y"
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            placeholder={t('users.ph_reason')}
          />
        </label>
        <div className="mt-5 flex justify-end gap-3">
          <button className="btn-secondary" onClick={() => { setStatusTarget(null); setReason('') }}>{t('common.cancel')}</button>
          <button
            type="button"
            disabled={!reason.trim() || statusSaving}
            onClick={confirmStatus}
            className={`inline-flex items-center rounded-xl px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50 ${suspending ? 'bg-rose-600 hover:bg-rose-700' : 'bg-leaf-600 hover:bg-leaf-700'}`}
          >
            {statusSaving ? t('common.saving') : t(suspending ? 'users.suspend_btn' : 'users.unsuspend_btn')}
          </button>
        </div>
      </Modal>

      <Modal
        open={Boolean(detailTarget)}
        onClose={closeDetail}
        title={t('users.detail_title')}
        description={t('users.detail_desc')}
        size="sm"
      >
        {detailLoading && <p className="mb-4 text-sm text-slate-500 dark:text-slate-400">{t('common.loading')}</p>}
        {detailUser && (
          <dl className="grid grid-cols-[120px_1fr] gap-x-4 gap-y-3 text-sm">
            <dt className="font-semibold text-slate-500 dark:text-slate-400">{t('users.detail_id')}</dt>
            <dd className="font-mono text-slate-800 dark:text-slate-100">#{detailUser.id}</dd>
            <dt className="font-semibold text-slate-500 dark:text-slate-400">{t('users.col_user')}</dt>
            <dd className="text-slate-800 dark:text-slate-100">{detailUser.full_name || detailUser.username} <span className="text-slate-400 dark:text-slate-500">@{detailUser.username}</span></dd>
            <dt className="font-semibold text-slate-500 dark:text-slate-400">{t('users.col_email')}</dt>
            <dd className="text-slate-800 dark:text-slate-100">{detailUser.email || '—'}</dd>
            <dt className="font-semibold text-slate-500 dark:text-slate-400">{t('users.col_role')}</dt>
            <dd><span className="rounded-full bg-sky-50 px-2.5 py-1 text-xs font-semibold text-sky-700 dark:bg-sky-900/40 dark:text-sky-300">{t(`roles.${detailUser.role}`)}</span></dd>
            <dt className="font-semibold text-slate-500 dark:text-slate-400">{t('users.col_status')}</dt>
            <dd><StatusBadge value={detailUser.status} /></dd>
            <dt className="font-semibold text-slate-500 dark:text-slate-400">{t('users.detail_created_by')}</dt>
            <dd className="text-slate-800 dark:text-slate-100">
              {/* Chưa resolve xong người tạo thì hiển thị "…" thay vì số id để khỏi nháy. */}
              {detailLoading && detailUser.created_by != null ? '…' : formatCreatedBy(detailUser, detailCreator)}
            </dd>
          </dl>
        )}
        <div className="mt-6 flex justify-end">
          <button className="btn-secondary" onClick={closeDetail}>{t('users.detail_close')}</button>
        </div>
      </Modal>
    </div>
  )
}

