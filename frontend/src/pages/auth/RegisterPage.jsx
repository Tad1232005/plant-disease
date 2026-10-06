import { zodResolver } from '@hookform/resolvers/zod'
import { ArrowLeft, ArrowRight, CheckCircle2, Eye, EyeOff } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { z } from 'zod'
import Brand from '../../components/common/Brand.jsx'
import PreferenceControls from '../../components/common/PreferenceControls.jsx'
import { useAuth } from '../../contexts/AuthContext.jsx'
import { usePreferences } from '../../contexts/PreferencesContext.jsx'
import { getHomeForRole } from '../../utils/roles.js'

const schema = z.object({
  full_name: z.string().trim().min(2, 'Vui lòng nhập họ tên'),
  username: z.string().trim().min(3, 'Tên đăng nhập cần ít nhất 3 ký tự').max(50, 'Tên đăng nhập không quá 50 ký tự'),
  email: z.string().email('Email chưa đúng định dạng'),
  password: z
    .string()
    .min(8, 'Mật khẩu cần ít nhất 8 ký tự')
    .max(128, 'Mật khẩu không quá 128 ký tự')
    .regex(/[a-z]/, 'Mật khẩu phải chứa ít nhất 1 chữ thường')
    .regex(/[A-Z]/, 'Mật khẩu phải chứa ít nhất 1 chữ hoa')
    .regex(/\d/, 'Mật khẩu phải chứa ít nhất 1 chữ số'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: 'Mật khẩu nhập lại chưa khớp',
  path: ['confirmPassword'],
})

export default function RegisterPage() {
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [serverError, setServerError] = useState('')
  const { register: createAccount, user, isAuthenticated } = useAuth()
  const { language, t } = usePreferences()
  const navigate = useNavigate()
  const { register, handleSubmit, watch, formState: { errors, isSubmitting } } = useForm({
    resolver: zodResolver(schema),
    defaultValues: { full_name: '', username: '', email: '', password: '', confirmPassword: '' },
  })

  const passwordValue = watch('password') || ''

  const criteria = [
    { label: language === 'vi' ? 'Tối thiểu 8 ký tự' : 'At least 8 characters', met: passwordValue.length >= 8 },
    { label: language === 'vi' ? 'Có chữ hoa (A-Z)' : 'Uppercase letter', met: /[A-Z]/.test(passwordValue) },
    { label: language === 'vi' ? 'Có chữ thường (a-z)' : 'Lowercase letter', met: /[a-z]/.test(passwordValue) },
    { label: language === 'vi' ? 'Có chữ số (0-9)' : 'Number (0-9)', met: /\d/.test(passwordValue) },
  ]

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

  return (
    <div className="min-h-screen bg-hero-glow py-8 sm:py-12">
      <div className="page-container">
        <div className="mb-8 flex items-center justify-between gap-3">
          <Brand />
          <div className="flex items-center gap-2">
            <PreferenceControls compact />
            <Link to="/" className="hidden items-center gap-2 text-sm font-semibold text-slate-500 hover:text-leaf-700 sm:inline-flex">
              <ArrowLeft size={17} />{t('common.home')}
            </Link>
          </div>
        </div>
        <div className="mx-auto grid max-w-5xl overflow-hidden rounded-[2rem] border border-white bg-white shadow-soft lg:grid-cols-[.9fr_1.1fr]">
          <aside className="bg-leaf-800 p-8 text-white sm:p-10">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-leaf-200">{t('register.eyebrow')}</p>
            <h1 className="mt-4 text-3xl font-black leading-tight">{t('register.heroTitle')}</h1>
            <p className="mt-4 text-sm leading-7 text-leaf-100/70">{t('register.heroText')}</p>
            <div className="mt-8 space-y-4">
              {[t('register.benefit1'), t('register.benefit2'), t('register.benefit3')].map((item) => (
                <p key={item} className="flex items-center gap-3 text-sm font-semibold text-leaf-50">
                  <CheckCircle2 size={18} className="text-leaf-300" />{item}
                </p>
              ))}
            </div>
          </aside>
          <main className="p-7 sm:p-10">
            <h2 className="text-2xl font-black text-slate-900">{t('register.title')}</h2>
            <p className="mt-2 text-sm text-slate-500">{t('register.formText')}</p>
            <form onSubmit={handleSubmit(onSubmit)} className="mt-7 space-y-4" noValidate>
              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-slate-700">{t('register.fullName')}</span>
                <input className="input-control" placeholder={t('register.namePlaceholder')} {...register('full_name')} />
                {errors.full_name && <span className="mt-1.5 block text-xs font-medium text-rose-600">{errors.full_name.message}</span>}
              </label>

              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-slate-700">{t('login.username')}</span>
                <input className="input-control" placeholder={t('register.userPlaceholder')} {...register('username')} />
                {errors.username && <span className="mt-1.5 block text-xs font-medium text-rose-600">{errors.username.message}</span>}
              </label>

              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-slate-700">{t('register.email')}</span>
                <input type="email" className="input-control" placeholder={t('register.emailPlaceholder')} {...register('email')} />
                {errors.email && <span className="mt-1.5 block text-xs font-medium text-rose-600">{errors.email.message}</span>}
              </label>

              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-slate-700">{t('register.password')}</span>
                <span className="relative block">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    className="input-control pr-11"
                    placeholder={t('register.passwordPlaceholder')}
                    {...register('password')}
                  />
                  <button
                    type="button"
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-700"
                    onClick={() => setShowPassword((v) => !v)}
                    aria-label={t('login.passwordToggle')}
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </span>
                {errors.password && <span className="mt-1.5 block text-xs font-medium text-rose-600">{errors.password.message}</span>}
                <div className="mt-2.5 grid grid-cols-2 gap-2 rounded-xl bg-slate-50 p-2.5 text-xs">
                  {criteria.map((c, i) => (
                    <span key={i} className={`flex items-center gap-1.5 font-medium transition-colors ${c.met ? 'text-emerald-700' : 'text-slate-400'}`}>
                      <span className={`h-1.5 w-1.5 rounded-full ${c.met ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                      {c.label}
                    </span>
                  ))}
                </div>
              </label>

              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-slate-700">{t('register.confirmPassword')}</span>
                <span className="relative block">
                  <input
                    type={showConfirmPassword ? 'text' : 'password'}
                    className="input-control pr-11"
                    placeholder={t('register.confirmPasswordPlaceholder')}
                    {...register('confirmPassword')}
                  />
                  <button
                    type="button"
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-700"
                    onClick={() => setShowConfirmPassword((v) => !v)}
                    aria-label={t('login.passwordToggle')}
                  >
                    {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </span>
                {errors.confirmPassword && <span className="mt-1.5 block text-xs font-medium text-rose-600">{errors.confirmPassword.message}</span>}
              </label>

              {serverError && <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{serverError}</p>}
              <button className="btn-primary mt-2 w-full !py-3.5" disabled={isSubmitting}>
                {isSubmitting ? t('register.submitting') : t('register.submit')} <ArrowRight size={17} />
              </button>
            </form>
            <p className="mt-6 text-center text-sm text-slate-500">
              {t('register.hasAccount')} <Link to="/login" className="font-bold text-leaf-700">{t('common.login')}</Link>
            </p>
          </main>
        </div>
      </div>
    </div>
  )
}
