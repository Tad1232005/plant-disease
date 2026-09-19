import { zodResolver } from '@hookform/resolvers/zod'
import { ArrowLeft, ArrowRight, Eye, EyeOff, ShieldCheck } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { z } from 'zod'
import Brand from '../components/common/Brand.jsx'
import { useAuth } from '../contexts/AuthContext.jsx'
import { demoUsers } from '../data/demoData.js'

const FRONTEND_URL = import.meta.env.VITE_FRONTEND_URL || 'http://localhost:5173'
const schema = z.object({
  username: z.string().trim().min(3, 'Tên đăng nhập cần ít nhất 3 ký tự'),
  password: z.string().min(6, 'Mật khẩu cần ít nhất 6 ký tự'),
})

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false)
  const [serverError, setServerError] = useState('')
  const { login, isAuthenticated } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const { register, handleSubmit, setValue, formState: { errors, isSubmitting } } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { username: '', password: '' },
  })

  if (isAuthenticated) return <Navigate to="/" replace />

  async function onSubmit(values) {
    setServerError('')
    try {
      await login(values)
      navigate(location.state?.from?.pathname || '/', { replace: true })
    } catch (error) {
      setServerError(error.message)
    }
  }

  function useDemoAdmin() {
    setValue('username', demoUsers.admin.username, { shouldValidate: true })
    setValue('password', demoUsers.admin.password, { shouldValidate: true })
  }

  return (
    <div className="grid min-h-screen bg-[#f8fbf9] lg:grid-cols-[.9fr_1.1fr]">
      <aside className="relative hidden overflow-hidden bg-leaf-900 p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <Brand light />
        <div className="relative max-w-lg">
          <span className="grid h-14 w-14 place-items-center rounded-2xl bg-white/10 text-leaf-200"><ShieldCheck size={28} /></span>
          <h1 className="mt-7 text-4xl font-black leading-tight">PlantCare<br />Control Center</h1>
          <p className="mt-5 max-w-md leading-8 text-leaf-100/65">Ứng dụng quản trị độc lập dành cho quản trị viên hệ thống.</p>
        </div>
        <p className="relative text-xs text-leaf-200/40">PlantCare AI • Admin Panel</p>
      </aside>

      <main className="flex items-center justify-center p-5 sm:p-10">
        <div className="w-full max-w-md">
          <a href={FRONTEND_URL} className="mb-7 inline-flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-leaf-700"><ArrowLeft size={17} /> Về trang người dùng</a>
          <h2 className="text-3xl font-black tracking-tight text-slate-900">Đăng nhập quản trị</h2>
          <p className="mt-2 text-sm leading-6 text-slate-500">Chỉ tài khoản có role <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs">admin</code> được phép truy cập.</p>

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
                <button type="button" className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-slate-400" onClick={() => setShowPassword((value) => !value)} aria-label="Hiện hoặc ẩn mật khẩu">{showPassword ? <EyeOff size={18} /> : <Eye size={18} />}</button>
              </span>
              {errors.password && <span className="mt-1.5 block text-xs font-medium text-rose-600">{errors.password.message}</span>}
            </label>
            {serverError && <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{serverError}</p>}
            <button className="btn-primary w-full !py-3.5" disabled={isSubmitting}>{isSubmitting ? 'Đang kiểm tra...' : 'Đăng nhập Admin'} <ArrowRight size={17} /></button>
          </form>

          <button type="button" onClick={useDemoAdmin} className="mt-5 w-full rounded-2xl border border-slate-200 bg-white p-4 text-left transition hover:border-leaf-300 hover:bg-leaf-50">
            <p className="text-sm font-bold text-slate-800">Dùng tài khoản Admin demo</p>
            <p className="mt-1 text-xs text-slate-400">admin / 123456</p>
          </button>
        </div>
      </main>
    </div>
  )
}
