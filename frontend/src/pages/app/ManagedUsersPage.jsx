import { AlertCircle, CheckCircle2, KeyRound, Link2, Link2Off, Lock, Plus, Unlock, UsersRound } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { getApiError } from '../../api/client.js'
import { farmsApi } from '../../api/farms.js'
import { farmMembersApi, managedUsersApi } from '../../api/managedUsers.js'
import ConfirmDialog from '../../components/common/ConfirmDialog.jsx'
import CrudForm from '../../components/common/CrudForm.jsx'
import DataTable from '../../components/common/DataTable.jsx'
import Modal from '../../components/common/Modal.jsx'
import PageHeader from '../../components/common/PageHeader.jsx'
import StatCard from '../../components/common/StatCard.jsx'
import StatusBadge from '../../components/common/StatusBadge.jsx'
import { initialFarms, initialManagedUsers } from '../../data/demoData.js'
import { getRoleLabel } from '../../utils/roles.js'
import { loadCollection, saveCollection } from '../../utils/storage.js'
import { usePreferences } from '../../contexts/PreferencesContext.jsx'

const STORAGE_KEY = 'plantcare_managed_users'

function unwrapList(payload) {
  if (Array.isArray(payload)) return payload
  return payload?.items || payload?.users || payload?.data || []
}

function normalizeUser(user, farms, language = 'vi') {
  const farmId = user.farm_id ?? user.farm?.id ?? user.farmId ?? ''
  const farm = farms.find((item) => String(item.id) === String(farmId))
  return {
    ...user,
    id: user.id ?? user.user_id,
    full_name: user.full_name || user.name || user.username,
    farmId: farmId ? String(farmId) : '',
    farmName: user.farm_name || user.farm?.name || farm?.name || (language === 'vi' ? 'Chưa phân công' : 'Unassigned'),
    status: user.status || 'active',
  }
}

export default function ManagedUsersPage() {
  const { language, t } = usePreferences()
  const copy = language === 'vi' ? {
    success: 'Đã tạo Managed User và gán vào trang trại thành công.',
    failure: 'Không thể tạo Managed User. Vui lòng kiểm tra API Manager.',
    removed: 'Đã gỡ Managed User khỏi trang trại.',
    removeFailure: 'Không thể gỡ thành viên khỏi trang trại.',
    assignedSuccess: 'Đã phân công trang trại thành công.',
    assignFailure: 'Không thể phân công trang trại. Vui lòng thử lại.',
    assignFarm: 'Phân công vào trang trại',
    reassignFarm: 'Đổi trang trại',
    noFarms: 'Chưa có trang trại nào. Hãy tạo trang trại trước.',
    person: 'Nông dân (Managed User)',
    role: 'Vai trò',
    farm: 'Trang trại',
    unassigned: 'Chưa phân công',
    loading: 'Đang kết nối API quản lý Managed User...',
    api: 'Đã kết nối API /manager/users.',
    demo: 'Backend Tuần 4 chưa phản hồi nên trang đang dùng dữ liệu demo localStorage.',
    search: 'Tìm theo tên, email hoặc trang trại...',
    remove: 'Gỡ khỏi trang trại',
    empty: 'Chưa có Managed User',
    emptyText: 'Nhấn Thêm Managed User để tạo tài khoản và phân công vào trang trại.',
    removeTitle: 'Gỡ khỏi trang trại',
    removeQuestion: 'Gỡ',
    accountKept: 'Tài khoản vẫn được giữ lại.',
    status: 'Trạng thái',
    resetPw: 'Đặt lại mật khẩu',
    lockTitle: 'Khóa tài khoản',
    unlockTitle: 'Mở khóa tài khoản',
  } : {
    success: 'Managed User created and assigned successfully.',
    failure: 'Unable to create the Managed User. Check the Manager API.',
    removed: 'Managed User removed from the farm.',
    removeFailure: 'Unable to remove the member from the farm.',
    assignedSuccess: 'Farm assigned successfully.',
    assignFailure: 'Failed to assign farm. Please try again.',
    assignFarm: 'Assign to farm',
    reassignFarm: 'Change farm',
    noFarms: 'No farms available. Please create a farm first.',
    person: 'Farmer (Managed User)',
    role: 'Role',
    farm: 'Farm',
    unassigned: 'Unassigned',
    loading: 'Connecting to the Managed User API...',
    api: 'Connected to /manager/users.',
    demo: 'The Week 4 backend is unavailable, so local demo data is shown.',
    search: 'Search by name, email, or farm...',
    remove: 'Remove from farm',
    empty: 'No Managed Users yet',
    emptyText: 'Select Add Managed User to create and assign an account.',
    removeTitle: 'Remove from farm',
    removeQuestion: 'Remove',
    accountKept: 'The account will be kept.',
    status: 'Status',
    resetPw: 'Reset Password',
    lockTitle: 'Suspend Account',
    unlockTitle: 'Activate Account',
  }
  const [farms, setFarms] = useState(() => loadCollection('plantcare_farms', initialFarms))
  const [users, setUsers] = useState(() => loadCollection(STORAGE_KEY, initialManagedUsers.filter((item) => item.role === 'user')))
  const [mode, setMode] = useState('loading')
  const [formOpen, setFormOpen] = useState(false)
  const [formError, setFormError] = useState('')
  const [removing, setRemoving] = useState(null)
  const [assigningUser, setAssigningUser] = useState(null)
  const [selectedFarmId, setSelectedFarmId] = useState('')
  const [assignError, setAssignError] = useState('')
  const [resettingUser, setResettingUser] = useState(null)
  const [newPassword, setNewPassword] = useState('')
  const [resetError, setResetError] = useState('')
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [messageType, setMessageType] = useState('success')

  useEffect(() => {
    let active = true

    async function loadData() {
      try {
        const [farmList, userPayload] = await Promise.all([
          farmsApi.list().catch(() => []),
          managedUsersApi.list(),
        ])
        if (!active) return

        const validFarms = Array.isArray(farmList) ? farmList : []
        if (validFarms.length > 0) {
          setFarms(validFarms)
        }

        const farmByUser = {}
        if (validFarms.length > 0) {
          const membershipsList = await Promise.all(
            validFarms.map((farm) => farmMembersApi.list(farm.id).catch(() => []))
          )
          if (!active) return
          membershipsList.forEach((members, index) => {
            const currentFarm = validFarms[index]
            if (Array.isArray(members)) {
              members.forEach((m) => {
                const uId = m.user_id ?? m.user?.id
                if (uId) {
                  farmByUser[uId] = { farmId: currentFarm.id, farmName: currentFarm.name }
                }
              })
            }
          })
        }

        const rawUsers = unwrapList(userPayload)
        const rows = rawUsers.map((item) => {
          const assigned = farmByUser[item.id]
          return normalizeUser(
            {
              ...item,
              farm_id: assigned ? assigned.farmId : (item.farm_id ?? ''),
              farm_name: assigned ? assigned.farmName : (item.farm_name ?? ''),
            },
            validFarms.length > 0 ? validFarms : farms,
            language
          )
        })

        setUsers(rows)
        setMode('api')
      } catch (err) {
        if (active) setMode('demo')
      }
    }

    loadData()
    return () => { active = false }
  }, [language])

  useEffect(() => {
    if (mode !== 'loading') saveCollection(STORAGE_KEY, users)
  }, [mode, users])

  const fields = useMemo(() => [
    { name: 'full_name', label: t('register.fullName'), placeholder: language === 'vi' ? 'Nguyễn Văn Bình' : 'Alex Nguyen', fullWidth: true, required: false },
    { name: 'username', label: t('login.username'), placeholder: 'managed.user', minLength: 3, required: true },
    { name: 'email', label: 'Email', type: 'email', placeholder: 'user@example.com', required: false },
    {
      name: 'password',
      label: t('managed.initialPassword'),
      type: 'password',
      placeholder: language === 'vi' ? 'Tối thiểu 8 ký tự (hoa, thường, số)' : 'Min 8 chars (uppercase, lowercase, number)',
      minLength: 8,
      pattern: {
        regex: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/,
        message: language === 'vi'
          ? 'Mật khẩu phải chứa ít nhất 1 chữ hoa, 1 chữ thường và 1 chữ số'
          : 'Password must contain at least 1 uppercase letter, 1 lowercase letter, and 1 number',
      },
      required: true,
    },
    {
      name: 'farm_id',
      label: t('managed.farm'),
      type: 'select',
      options: [
        { value: '', label: copy.unassigned },
        ...farms.map((farm) => ({ value: String(farm.id), label: farm.name })),
      ],
      required: false,
    },
  ], [farms, language, t, copy.unassigned])

  async function createManagedUser(values) {
    setSaving(true)
    setFormError('')
    setMessage('')
    const farm = farms.find((item) => String(item.id) === String(values.farm_id))
    const payload = {
      username: values.username.trim(),
      password: values.password,
    }
    if (values.full_name?.trim()) {
      payload.full_name = values.full_name.trim()
    }
    if (values.email?.trim()) {
      payload.email = values.email.trim()
    }

    try {
      if (mode === 'api') {
        const created = await managedUsersApi.create(payload)
        const userId = created.id ?? created.user_id
        let assignedFarm = null
        if (values.farm_id && userId) {
          try {
            await farmMembersApi.add(Number(values.farm_id), Number(userId))
            assignedFarm = farm
          } catch (assignError) {
            console.warn('Lỗi gán thành viên vào Farm:', assignError)
          }
        }
        setUsers((items) => [
          normalizeUser(
            {
              ...created,
              farm_id: assignedFarm ? values.farm_id : undefined,
              farm_name: assignedFarm?.name,
            },
            farms,
            language
          ),
          ...items,
        ])
      } else {
        setUsers((items) => [{
          ...payload,
          password: undefined,
          id: Date.now(),
          farmId: values.farm_id,
          farmName: farm?.name || copy.unassigned,
          status: 'active',
        }, ...items])
      }
      setFormOpen(false)
      setMessageType('success')
      setMessage(copy.success)
    } catch (error) {
      const errText = getApiError(error, copy.failure)
      setFormError(errText)
      setMessageType('error')
      setMessage(errText)
    } finally {
      setSaving(false)
    }
  }

  async function toggleStatus(row) {
    const nextStatus = row.status === 'active' ? 'suspended' : 'active'
    const reason = nextStatus === 'suspended' ? 'Manager tạm đình chỉ vụ mùa' : 'Manager kích hoạt lại tài khoản'
    try {
      if (mode === 'api') {
        await managedUsersApi.changeStatus(row.id, { status: nextStatus, reason })
      }
      setUsers((prev) => prev.map((u) => u.id === row.id ? { ...u, status: nextStatus } : u))
      setMessageType('success')
      setMessage(language === 'vi' ? `Đã cập nhật trạng thái của ${row.full_name} thành: ${nextStatus}` : `Status updated to ${nextStatus}`)
    } catch (err) {
      setMessageType('error')
      setMessage(getApiError(err, language === 'vi' ? 'Không thể cập nhật trạng thái.' : 'Failed to update status.'))
    }
  }

  async function handleResetPassword(e) {
    e.preventDefault()
    if (!resettingUser || !newPassword) return
    setSaving(true)
    setResetError('')
    try {
      if (mode === 'api') {
        await managedUsersApi.resetPassword(resettingUser.id, newPassword)
      }
      setResettingUser(null)
      setNewPassword('')
      setMessageType('success')
      setMessage(language === 'vi' ? `Đã đặt lại mật khẩu cho tài khoản @${resettingUser.username} thành công.` : `Password reset for @${resettingUser.username}`)
    } catch (err) {
      const errText = getApiError(err, language === 'vi' ? 'Không thể đặt lại mật khẩu.' : 'Failed to reset password.')
      setResetError(errText)
      setMessageType('error')
      setMessage(errText)
    } finally {
      setSaving(false)
    }
  }

  async function removeFromFarm() {
    if (!removing) return
    setSaving(true)
    setMessage('')
    try {
      if (mode === 'api' && removing.farmId) await farmMembersApi.remove(removing.farmId, removing.id)
      setUsers((items) => items.map((item) => item.id === removing.id ? { ...item, farmId: '', farmName: copy.unassigned } : item))
      setMessageType('success')
      setMessage(copy.removed)
      setRemoving(null)
    } catch (error) {
      setMessageType('error')
      setMessage(getApiError(error, copy.removeFailure))
    } finally {
      setSaving(false)
    }
  }

  async function handleAssignFarm(e) {
    e.preventDefault()
    if (!assigningUser || !selectedFarmId) return
    setSaving(true)
    setAssignError('')
    setMessage('')
    const targetFarm = farms.find((f) => String(f.id) === String(selectedFarmId))
    const previousFarmId = assigningUser.farmId

    if (previousFarmId && String(previousFarmId) === String(selectedFarmId)) {
      setAssigningUser(null)
      setSaving(false)
      return
    }

    try {
      if (mode === 'api') {
        if (previousFarmId) {
          try {
            await farmMembersApi.remove(Number(previousFarmId), Number(assigningUser.id))
          } catch (removeErr) {
            console.warn('Lỗi gỡ khỏi farm cũ trước khi đổi:', removeErr)
          }
        }
        await farmMembersApi.add(Number(selectedFarmId), Number(assigningUser.id))
      }

      setUsers((items) => items.map((item) => {
        if (item.id === assigningUser.id) {
          return {
            ...item,
            farmId: String(selectedFarmId),
            farmName: targetFarm?.name || copy.unassigned,
          }
        }
        return item
      }))

      setMessageType('success')
      setMessage(
        language === 'vi'
          ? `Đã phân công @${assigningUser.username} vào trang trại “${targetFarm?.name}” thành công.`
          : `Assigned @${assigningUser.username} to farm “${targetFarm?.name}” successfully.`
      )
      setAssigningUser(null)
      setSelectedFarmId('')
    } catch (err) {
      const errText = getApiError(err, copy.assignFailure)
      setAssignError(errText)
      setMessageType('error')
      setMessage(errText)
    } finally {
      setSaving(false)
    }
  }

  const columns = [
    { key: 'full_name', label: copy.person, sortable: true, render: (value, row) => <div><p className="font-bold text-slate-800">{value}</p><p className="mt-0.5 text-xs text-slate-400">@{row.username}</p></div> },
    { key: 'email', label: 'Email', sortable: true },
    { key: 'role', label: copy.role, sortable: true, render: (value) => <span className="rounded-full bg-sky-50 px-2.5 py-1 text-xs font-semibold text-sky-700">{language === 'vi' ? getRoleLabel(value) : 'User'}</span> },
    {
      key: 'farmName',
      label: copy.farm,
      sortable: true,
      render: (value, row) => (
        <div className="flex items-center gap-2">
          {row.farmId ? (
            <span className="font-semibold text-leaf-700">{value}</span>
          ) : (
            <button
              type="button"
              onClick={() => {
                setAssigningUser(row)
                setSelectedFarmId(farms[0]?.id ? String(farms[0].id) : '')
              }}
              className="inline-flex items-center gap-1 rounded-full border border-dashed border-amber-300 bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-700 transition hover:border-emerald-400 hover:bg-emerald-50 hover:text-emerald-800"
              title={copy.assignFarm}
            >
              <Link2 size={12} />
              {value}
            </button>
          )}
        </div>
      ),
    },
    { key: 'status', label: copy.status, sortable: true, render: (value) => <StatusBadge value={value} /> },
  ]

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader
        eyebrow={t('managed.eyebrow')}
        title={t('managed.title')}
        description={t('managed.description')}
        action={<button className="btn-primary" onClick={() => { setMessage(''); setFormError(''); setFormOpen(true) }}><Plus size={18} />{t('managed.add')}</button>}
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <StatCard icon={UsersRound} label={t('managed.total')} value={String(users.length).padStart(2, '0')} />
        <StatCard icon={UsersRound} label={t('managed.assigned')} value={users.filter((item) => item.farmId).length} tone="blue" />
        <StatCard icon={UsersRound} label={t('managed.unassigned')} value={users.filter((item) => !item.farmId).length} tone="amber" />
      </div>

      <div className={`mb-5 rounded-2xl border p-4 text-sm ${mode === 'api' ? 'border-emerald-100 bg-emerald-50 text-emerald-800' : 'border-amber-100 bg-amber-50 text-amber-800'}`}>
        {mode === 'loading' ? copy.loading : mode === 'api' ? copy.api : copy.demo}
      </div>
      {message && (
        <div className={`mb-5 flex items-center justify-between gap-3 rounded-2xl border p-4 text-sm ${
          messageType === 'error'
            ? 'border-rose-200 bg-rose-50 text-rose-800'
            : 'border-emerald-200 bg-emerald-50 text-emerald-800'
        }`}>
          <div className="flex items-center gap-2.5">
            {messageType === 'error' ? (
              <AlertCircle size={18} className="shrink-0 text-rose-600" />
            ) : (
              <CheckCircle2 size={18} className="shrink-0 text-emerald-600" />
            )}
            <span>{message}</span>
          </div>
          <button
            type="button"
            onClick={() => setMessage('')}
            className="rounded-lg p-1 text-slate-400 transition hover:bg-black/5 hover:text-slate-600"
            title="Đóng"
          >
            ✕
          </button>
        </div>
      )}

      <DataTable
        columns={columns}
        data={users}
        searchPlaceholder={copy.search}
        actions={(row) => (
          <div className="flex items-center justify-end gap-1">
            <button
              onClick={() => {
                setAssigningUser(row)
                setSelectedFarmId(row.farmId ? String(row.farmId) : (farms[0]?.id ? String(farms[0].id) : ''))
              }}
              className="rounded-lg p-2 text-slate-400 transition hover:bg-emerald-50 hover:text-emerald-700"
              title={row.farmId ? copy.reassignFarm : copy.assignFarm}
            >
              <Link2 size={17} />
            </button>
            <button
              onClick={() => { setResettingUser(row); setNewPassword('') }}
              className="rounded-lg p-2 text-slate-400 transition hover:bg-amber-50 hover:text-amber-600"
              title={copy.resetPw}
            >
              <KeyRound size={17} />
            </button>
            <button
              onClick={() => toggleStatus(row)}
              className={`rounded-lg p-2 transition ${row.status === 'active' ? 'text-slate-400 hover:bg-rose-50 hover:text-rose-600' : 'text-emerald-500 hover:bg-emerald-50 hover:text-emerald-700'}`}
              title={row.status === 'active' ? copy.lockTitle : copy.unlockTitle}
            >
              {row.status === 'active' ? <Lock size={17} /> : <Unlock size={17} />}
            </button>
            <button
              disabled={!row.farmId}
              onClick={() => setRemoving(row)}
              className="rounded-lg p-2 text-slate-400 transition hover:bg-rose-50 hover:text-rose-600 disabled:cursor-not-allowed disabled:opacity-30"
              title={copy.remove}
            >
              <Link2Off size={17} />
            </button>
          </div>
        )}
        emptyTitle={copy.empty}
        emptyDescription={copy.emptyText}
      />

      <Modal open={formOpen} onClose={() => { setFormOpen(false); setFormError('') }} title={t('managed.createTitle')} description={t('managed.createText')} size="xl">
        <CrudForm
          fields={fields}
          defaultValues={{ farm_id: '' }}
          onSubmit={createManagedUser}
          onCancel={() => { setFormOpen(false); setFormError('') }}
          submitLabel={t('managed.create')}
          loading={saving}
          error={formError}
        />
      </Modal>

      <Modal
        open={Boolean(assigningUser)}
        onClose={() => { setAssigningUser(null); setAssignError('') }}
        title={assigningUser?.farmId ? copy.reassignFarm : copy.assignFarm}
        description={assigningUser ? `${assigningUser.full_name} (@${assigningUser.username})` : ''}
        size="md"
      >
        <form onSubmit={handleAssignFarm} className="space-y-4">
          {assignError && (
            <div className="flex items-start gap-2.5 rounded-xl border border-rose-200 bg-rose-50 p-3.5 text-sm font-medium text-rose-800">
              <AlertCircle size={18} className="mt-0.5 shrink-0 text-rose-600" />
              <div className="flex-1 leading-relaxed">{assignError}</div>
            </div>
          )}
          <div>
            <label className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-slate-600">
              {copy.farm}
            </label>
            {farms.length === 0 ? (
              <p className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                {copy.noFarms}
              </p>
            ) : (
              <select
                value={selectedFarmId}
                onChange={(e) => setSelectedFarmId(e.target.value)}
                required
                className="input-control"
              >
                <option value="">{language === 'vi' ? '-- Chọn trang trại phân công --' : '-- Select farm --'}</option>
                {farms.map((f) => (
                  <option key={f.id} value={String(f.id)}>
                    {f.name} {f.location_text || f.location ? `(${f.location_text || f.location})` : ''}
                  </option>
                ))}
              </select>
            )}
            {assigningUser?.farmName && assigningUser.farmId && (
              <p className="mt-2 text-xs text-slate-500">
                {language === 'vi' ? 'Trang trại hiện tại: ' : 'Current farm: '}
                <span className="font-semibold text-leaf-700">{assigningUser.farmName}</span>
              </p>
            )}
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => { setAssigningUser(null); setAssignError('') }} className="btn-secondary">
              {language === 'vi' ? 'Hủy' : 'Cancel'}
            </button>
            <button
              type="submit"
              disabled={saving || !selectedFarmId || farms.length === 0}
              className="btn-primary"
            >
              {saving ? (language === 'vi' ? 'Đang lưu...' : 'Saving...') : (language === 'vi' ? 'Xác nhận phân công' : 'Confirm Assignment')}
            </button>
          </div>
        </form>
      </Modal>

      <Modal open={Boolean(resettingUser)} onClose={() => { setResettingUser(null); setResetError('') }} title={copy.resetPw} description={resettingUser ? `Đặt lại mật khẩu cho tài khoản @${resettingUser.username}` : ''} size="md">
        <form onSubmit={handleResetPassword} className="space-y-4">
          {resetError && (
            <div className="flex items-start gap-2.5 rounded-xl border border-rose-200 bg-rose-50 p-3.5 text-sm font-medium text-rose-800">
              <AlertCircle size={18} className="mt-0.5 shrink-0 text-rose-600" />
              <div className="flex-1 leading-relaxed">{resetError}</div>
            </div>
          )}
          <div>
            <label className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-slate-600">
              {language === 'vi' ? 'Mật khẩu mới (tối thiểu 8 ký tự)' : 'New Password (min 8 chars)'}
            </label>
            <input
              type="password"
              required
              minLength={8}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="••••••••"
              className="input-control"
            />
            <p className="mt-1 text-xs text-slate-400">
              {language === 'vi' ? 'Mật khẩu phải chứa ít nhất chữ hoa, chữ thường và chữ số.' : 'Must include uppercase, lowercase, and digit.'}
            </p>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => { setResettingUser(null); setResetError('') }} className="btn-secondary">
              {language === 'vi' ? 'Hủy' : 'Cancel'}
            </button>
            <button type="submit" disabled={saving || newPassword.length < 8} className="btn-primary">
              {saving ? (language === 'vi' ? 'Đang lưu...' : 'Saving...') : (language === 'vi' ? 'Xác nhận đặt lại' : 'Confirm Reset')}
            </button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog open={Boolean(removing)} onClose={() => setRemoving(null)} onConfirm={removeFromFarm} title={copy.removeTitle} message={removing ? `${copy.removeQuestion} “${removing.full_name}” — “${removing.farmName}”? ${copy.accountKept}` : ''} />
    </div>
  )
}
