import { zodResolver } from '@hookform/resolvers/zod'
import { ArrowLeft, ArrowRight, Eye, EyeOff, Leaf, ShieldCheck } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { z } from 'zod'
import Brand from '../../components/common/Brand.jsx'
import { useAuth } from '../../contexts/AuthContext.jsx'
import { demoUsers } from '../../data/demoData.js'
import { getHomeForRole, getRoleLabel } from '../../utils/roles.js'

const schema = z.object({
  username: z.string().trim().min(3, 'Tên đăng nhập cần ít nhất 3 ký tự'),
  password: z.string().min(6, 'Mật khẩu cần ít nhất 6 ký tự'),
})

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false)
  const [serverError, setServerError] = useState('')
  const { login, user, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const { register, handleSubmit, setValue, formState: { errors, isSubmitting } } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { username: '', password: '' },
  })

  if (isAuthenticated) return <Navigate to={getHomeForRole(user.role)} replace />

  async function onSubmit(values) {
    setServerError('')
    try {
      const profile = await login(values)
      const requested = location.state?.from?.pathname
      navigate(requested && !requested.startsWith('/admin') ? requested : getHomeForRole(profile.role), { replace: true })
    } catch (error) {
      setServerError(error.message)
    }
  }

  function useDemo(account) {
    setValue('username', account.username, { shouldValidate: true })
    setValue('password', account.password, { shouldValidate: true })
  }

  return (
    <div className="grid min-h-screen bg-[#f8fbf9] lg:grid-cols-[.92fr_1.08fr]">
      <aside className="relative hidden overflow-hidden bg-leaf-900 p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="absolute -right-24 -top-24 h-80 w-80 rounded-full border-[70px] border-white/5" />
        <div className="absolute -bottom-20 -left-20 h-72 w-72 rounded-full bg-leaf-500/10 blur-2xl" />
        <Brand light />
        <div className="relative max-w-lg">
          <span className="grid h-14 w-14 place-items-center rounded-2xl bg-white/10 text-leaf-200"><Leaf size={28} /></span>
          <h1 className="mt-7 text-4xl font-black leading-tight">Hiểu cây trồng.<br />Hành động đúng lúc.</h1>
          <p className="mt-5 max-w-md leading-8 text-leaf-100/65">Đăng nhập để chẩn đoán hình ảnh, xem lịch sử và quản lý sức khỏe cây trồng trên một giao diện duy nhất.</p>
          <div className="mt-9 flex items-center gap-3 text-sm text-leaf-100/70"><ShieldCheck size={20} className="text-leaf-300" /> Phân quyền riêng cho từng nhóm người dùng</div>
        </div>
        <p className="relative text-xs text-leaf-200/40">PlantCare AI • Hệ thống nhận diện bệnh lá cây</p>
      </aside>

      <main className="flex items-center justify-center p-5 sm:p-10">
        <div className="w-full max-w-lg">
          <div className="mb-8 flex items-center justify-between lg:hidden"><Brand /><Link to="/" className="text-sm font-semibold text-slate-500">Trang chủ</Link></div>
          <Link to="/" className="mb-7 hidden items-center gap-2 text-sm font-semibold text-slate-500 hover:text-leaf-700 lg:inline-flex"><ArrowLeft size={17} /> Về trang chủ</Link>
          <h2 className="text-3xl font-black tracking-tight text-slate-900">Chào mừng trở lại</h2>
          <p className="mt-2 text-sm leading-6 text-slate-500">Đăng nhập bằng tài khoản backend hoặc chọn nhanh một tài khoản demo.</p>

          <form onSubmit={handleSubmit(onSubmit)} className="mt-7 space-y-5" noValidate>
            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-slate-700">Tên đăng nhập</span>
              <input className="input-control !py-3" placeholder="Nhập tên đăng nhập" {...register('username')} />
              {errors.username && <span className="mt-1.5 block text-xs font-medium text-rose-600">{errors.username.message}</span>}
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-slate-700">Mật khẩu</span>
              <span className="relative block">
                <input type={showPassword ? 'text' : 'password'} className="input-control !py-3 pr-11" placeholder="Nhập mật khẩu" {...register('password')} />
                <button type="button" className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-700" onClick={() => setShowPassword((value) => !value)} aria-label="Hiện hoặc ẩn mật khẩu">
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </span>
              {errors.password && <span className="mt-1.5 block text-xs font-medium text-rose-600">{errors.password.message}</span>}
            </label>
            {serverError && <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{serverError}</p>}
            <button className="btn-primary w-full !py-3.5" disabled={isSubmitting}>{isSubmitting ? 'Đang đăng nhập...' : 'Đăng nhập'} <ArrowRight size={17} /></button>
          </form>

          <div className="my-7 flex items-center gap-4"><span className="h-px flex-1 bg-slate-200" /><span className="text-xs font-semibold text-slate-400">TÀI KHOẢN DEMO</span><span className="h-px flex-1 bg-slate-200" /></div>
          <div className="grid grid-cols-2 gap-2.5">
            {Object.values(demoUsers).map((account) => (
              <button key={account.username} type="button" onClick={() => useDemo(account)} className="rounded-2xl border border-slate-200 bg-white p-3 text-left transition hover:border-leaf-300 hover:bg-leaf-50">
                <p className="text-sm font-bold text-slate-800">{getRoleLabel(account.role)}</p>
                <p className="mt-0.5 text-xs text-slate-400">{account.username} / 123456</p>
              </button>
            ))}
          </div>
          <p className="mt-7 text-center text-sm text-slate-500">Chưa có tài khoản? <Link to="/register" className="font-bold text-leaf-700 hover:text-leaf-800">Đăng ký ngay</Link></p>
        </div>
      </main>
    </div>
  )
}
