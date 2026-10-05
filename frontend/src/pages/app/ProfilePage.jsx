import { CheckCircle2, KeyRound, LoaderCircle, Shield, User, UserCheck } from 'lucide-react'
import { useState } from 'react'
import PageHeader from '../../components/common/PageHeader.jsx'
import { useAuth } from '../../contexts/AuthContext.jsx'
import { usePreferences } from '../../contexts/PreferencesContext.jsx'
import { authApi } from '../../api/auth.js'

export default function ProfilePage() {
  const { user, logout } = useAuth()
  const { language } = usePreferences()

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState({ type: '', text: '' })

  const isVi = language === 'vi'

  const roleLabels = {
    user: isVi ? 'Nông dân' : 'Farmer',
    manager: isVi ? 'Quản lý nông trại' : 'Farm Manager',
    technician: isVi ? 'Kỹ thuật viên' : 'Technician',
    admin: isVi ? 'Quản trị viên' : 'Administrator',
  }

  async function handleChangePassword(e) {
    e.preventDefault()
    setMessage({ type: '', text: '' })

    if (newPassword.length < 6) {
      setMessage({
        type: 'error',
        text: isVi ? 'Mật khẩu mới phải có ít nhất 6 ký tự.' : 'New password must be at least 6 characters.',
      })
      return
    }

    if (newPassword !== confirmPassword) {
      setMessage({
        type: 'error',
        text: isVi ? 'Xác nhận mật khẩu mới không khớp.' : 'Password confirmation does not match.',
      })
      return
    }

    setLoading(true)
    try {
      const isDemoSession = localStorage.getItem('plantcare_access_token') === 'plantcare_demo_session'
      if (!isDemoSession) {
        await authApi.changePassword({
          current_password: currentPassword,
          new_password: newPassword,
        })
      } else {
        if (currentPassword !== '123456') {
          setMessage({
            type: 'error',
            text: isVi ? 'Mật khẩu hiện tại không đúng (mật khẩu demo là 123456).' : 'Current password is incorrect (demo password is 123456).',
          })
          return
        }
      }
      setMessage({
        type: 'success',
        text: isVi
          ? 'Đổi mật khẩu thành công! Vui lòng sử dụng mật khẩu mới cho lần đăng nhập sau.'
          : 'Password changed successfully! Please use your new password next time.',
      })
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    } catch (err) {
      const detail = err?.response?.data?.detail
      setMessage({
        type: 'error',
        text: detail || (isVi ? 'Không thể đổi mật khẩu. Vui lòng kiểm tra lại mật khẩu hiện tại.' : 'Failed to change password. Please check your current password.'),
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-4xl">
      <PageHeader
        eyebrow={isVi ? 'Tài khoản & Bảo mật' : 'Account & Security'}
        title={isVi ? 'Hồ sơ người dùng' : 'User Profile'}
        description={isVi ? 'Xem thông tin tài khoản và quản lý mật khẩu bảo mật.' : 'View account details and manage password security.'}
      />

      <div className="grid gap-6 md:grid-cols-[1fr_1.3fr]">
        {/* Card thông tin tài khoản */}
        <div className="card p-6">
          <div className="flex items-center gap-4 border-b border-slate-100 pb-5">
            <span className="grid h-14 w-14 place-items-center rounded-2xl bg-leaf-50 text-leaf-700">
              <User size={28} />
            </span>
            <div>
              <h2 className="text-lg font-black text-slate-800">{user?.full_name || user?.username}</h2>
              <p className="text-xs text-slate-400">@{user?.username}</p>
            </div>
          </div>

          <div className="mt-5 space-y-4 text-sm">
            <div>
              <span className="block text-xs font-semibold uppercase text-slate-400">{isVi ? 'Email liên hệ' : 'Email'}</span>
              <p className="mt-1 font-bold text-slate-700">{user?.email || (isVi ? 'Chưa cập nhật' : 'Not updated')}</p>
            </div>

            <div>
              <span className="block text-xs font-semibold uppercase text-slate-400">{isVi ? 'Vai trò hệ thống' : 'System Role'}</span>
              <div className="mt-1 inline-flex items-center gap-1.5 rounded-lg bg-leaf-50 px-2.5 py-1 text-xs font-bold text-leaf-800">
                <Shield size={14} />
                {roleLabels[user?.role] || user?.role}
              </div>
            </div>

            <div>
              <span className="block text-xs font-semibold uppercase text-slate-400">{isVi ? 'Trạng thái tài khoản' : 'Status'}</span>
              <div className="mt-1 inline-flex items-center gap-1.5 text-xs font-bold text-emerald-600">
                <UserCheck size={14} />
                {isVi ? 'Đang hoạt động' : 'Active'}
              </div>
            </div>
          </div>
        </div>

        {/* Card đổi mật khẩu */}
        <div className="card p-6">
          <div className="flex items-center gap-3 border-b border-slate-100 pb-4">
            <span className="grid h-10 w-10 place-items-center rounded-xl bg-amber-50 text-amber-600">
              <KeyRound size={20} />
            </span>
            <div>
              <h3 className="text-base font-extrabold text-slate-800">{isVi ? 'Đổi mật khẩu' : 'Change Password'}</h3>
              <p className="text-xs text-slate-400">{isVi ? 'Cập nhật mật khẩu để bảo vệ tài khoản' : 'Update password to secure your account'}</p>
            </div>
          </div>

          {message.text && (
            <div
              className={`mt-4 rounded-xl p-3.5 text-xs font-semibold ${
                message.type === 'success'
                  ? 'border border-emerald-200 bg-emerald-50 text-emerald-800'
                  : 'border border-rose-200 bg-rose-50 text-rose-800'
              }`}
            >
              {message.text}
            </div>
          )}

          <form onSubmit={handleChangePassword} className="mt-5 space-y-4">
            <div>
              <label className="mb-1.5 block text-xs font-bold text-slate-700">
                {isVi ? 'Mật khẩu hiện tại' : 'Current Password'}
              </label>
              <input
                type="password"
                required
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="input-control"
                placeholder="••••••••"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-xs font-bold text-slate-700">
                {isVi ? 'Mật khẩu mới' : 'New Password'}
              </label>
              <input
                type="password"
                required
                minLength={6}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="input-control"
                placeholder="••••••••"
              />
            </div>

            <div>
              <label className="mb-1.5 block text-xs font-bold text-slate-700">
                {isVi ? 'Xác nhận mật khẩu mới' : 'Confirm New Password'}
              </label>
              <input
                type="password"
                required
                minLength={6}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="input-control"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary mt-3 w-full justify-center !py-3"
            >
              {loading ? (
                <>
                  <LoaderCircle className="animate-spin" size={17} />
                  {isVi ? 'Đang cập nhật...' : 'Updating...'}
                </>
              ) : (
                <>
                  <CheckCircle2 size={17} />
                  {isVi ? 'Cập nhật mật khẩu' : 'Update Password'}
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
