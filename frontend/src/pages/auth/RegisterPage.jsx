import { zodResolver } from '@hookform/resolvers/zod'
import { ArrowLeft, ArrowRight, CheckCircle2 } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { z } from 'zod'
import Brand from '../../components/common/Brand.jsx'
import { useAuth } from '../../contexts/AuthContext.jsx'
import { getHomeForRole } from '../../utils/roles.js'

const schema = z.object({
  full_name: z.string().trim().min(2, 'Vui lòng nhập họ tên'),
  username: z.string().trim().min(3, 'Tên đăng nhập cần ít nhất 3 ký tự').max(50),
  email: z.string().email('Email chưa đúng định dạng'),
  password: z.string().min(6, 'Mật khẩu cần ít nhất 6 ký tự'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, { message: 'Mật khẩu nhập lại chưa khớp', path: ['confirmPassword'] })

export default function RegisterPage() {
  const [serverError, setServerError] = useState('')
  const { register: createAccount, user, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({ resolver: zodResolver(schema) })

  if (isAuthenticated) return <Navigate to={getHomeForRole(user.role)} replace />

  async function onSubmit({ confirmPassword: _, ...payload }) {
    setServerError('')
    try {
      const profile = await createAccount(payload)
      navigate(getHomeForRole(profile.role), { replace: true })
    } catch (error) {
      setServerError(error.message)
    }
  }

  const fields = [
    { name: 'full_name', label: 'Họ và tên', placeholder: 'Nguyễn Văn An' },
    { name: 'username', label: 'Tên đăng nhập', placeholder: 'nguyenvanan' },
    { name: 'email', label: 'Email', placeholder: 'ban@example.com', type: 'email' },
    { name: 'password', label: 'Mật khẩu', placeholder: 'Tối thiểu 6 ký tự', type: 'password' },
    { name: 'confirmPassword', label: 'Nhập lại mật khẩu', placeholder: 'Nhập lại mật khẩu', type: 'password' },
  ]

  return (
    <div className="min-h-screen bg-hero-glow py-8 sm:py-12">
      <div className="page-container">
        <div className="mb-8 flex items-center justify-between"><Brand /><Link to="/" className="inline-flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-leaf-700"><ArrowLeft size={17} /> Trang chủ</Link></div>
        <div className="mx-auto grid max-w-5xl overflow-hidden rounded-[2rem] border border-white bg-white shadow-soft lg:grid-cols-[.9fr_1.1fr]">
          <aside className="bg-leaf-800 p-8 text-white sm:p-10">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-leaf-200">Tạo tài khoản</p>
            <h1 className="mt-4 text-3xl font-black leading-tight">Bắt đầu quản lý sức khỏe cây trồng hôm nay.</h1>
            <p className="mt-4 text-sm leading-7 text-leaf-100/70">Tài khoản mới mặc định là vai trò Nông dân. Quản trị viên có thể thay đổi vai trò sau.</p>
            <div className="mt-8 space-y-4">
              {['Chẩn đoán ảnh lá cây', 'Lưu lịch sử từng lần quét', 'Quản lý khu vực trồng'].map((item) => <p key={item} className="flex items-center gap-3 text-sm font-semibold text-leaf-50"><CheckCircle2 size={18} className="text-leaf-300" />{item}</p>)}
            </div>
          </aside>
          <main className="p-7 sm:p-10">
            <h2 className="text-2xl font-black text-slate-900">Thông tin tài khoản</h2>
            <p className="mt-2 text-sm text-slate-500">Điền thông tin để kết nối với API đăng ký của hệ thống.</p>
            <form onSubmit={handleSubmit(onSubmit)} className="mt-7 space-y-4" noValidate>
              {fields.map((field) => (
                <label key={field.name} className="block">
                  <span className="mb-2 block text-sm font-semibold text-slate-700">{field.label}</span>
                  <input type={field.type || 'text'} className="input-control" placeholder={field.placeholder} {...register(field.name)} />
                  {errors[field.name] && <span className="mt-1.5 block text-xs font-medium text-rose-600">{errors[field.name].message}</span>}
                </label>
              ))}
              {serverError && <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{serverError}</p>}
              <button className="btn-primary mt-2 w-full !py-3.5" disabled={isSubmitting}>{isSubmitting ? 'Đang tạo tài khoản...' : 'Tạo tài khoản'} <ArrowRight size={17} /></button>
            </form>
            <p className="mt-6 text-center text-sm text-slate-500">Đã có tài khoản? <Link to="/login" className="font-bold text-leaf-700">Đăng nhập</Link></p>
          </main>
        </div>
      </div>
    </div>
  )
}
