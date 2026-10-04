import { zodResolver } from '@hookform/resolvers/zod'
import { ArrowLeft, ArrowRight, CheckCircle2 } from 'lucide-react'
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
  username: z.string().trim().min(3, 'Tên đăng nhập cần ít nhất 3 ký tự').max(50),
  email: z.string().email('Email chưa đúng định dạng'),
  password: z.string().min(6, 'Mật khẩu cần ít nhất 6 ký tự'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, { message: 'Mật khẩu nhập lại chưa khớp', path: ['confirmPassword'] })

export default function RegisterPage() {
  const [serverError, setServerError] = useState('')
  const { register: createAccount, user, isAuthenticated } = useAuth()
  const { t } = usePreferences()
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
    { name: 'full_name', label: t('register.fullName'), placeholder: t('register.namePlaceholder') },
    { name: 'username', label: t('login.username'), placeholder: t('register.userPlaceholder') },
    { name: 'email', label: t('register.email'), placeholder: t('register.emailPlaceholder'), type: 'email' },
    { name: 'password', label: t('register.password'), placeholder: t('register.passwordPlaceholder'), type: 'password' },
    { name: 'confirmPassword', label: t('register.confirmPassword'), placeholder: t('register.confirmPassword'), type: 'password' },
  ]

  return (
    <div className="min-h-screen bg-hero-glow py-8 sm:py-12">
      <div className="page-container">
        <div className="mb-8 flex items-center justify-between gap-3"><Brand /><div className="flex items-center gap-2"><PreferenceControls compact /><Link to="/" className="hidden items-center gap-2 text-sm font-semibold text-slate-500 hover:text-leaf-700 sm:inline-flex"><ArrowLeft size={17} />{t('common.home')}</Link></div></div>
        <div className="mx-auto grid max-w-5xl overflow-hidden rounded-[2rem] border border-white bg-white shadow-soft lg:grid-cols-[.9fr_1.1fr]">
          <aside className="bg-leaf-800 p-8 text-white sm:p-10">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-leaf-200">{t('register.eyebrow')}</p>
            <h1 className="mt-4 text-3xl font-black leading-tight">{t('register.heroTitle')}</h1>
            <p className="mt-4 text-sm leading-7 text-leaf-100/70">{t('register.heroText')}</p>
            <div className="mt-8 space-y-4">
              {[t('register.benefit1'), t('register.benefit2'), t('register.benefit3')].map((item) => <p key={item} className="flex items-center gap-3 text-sm font-semibold text-leaf-50"><CheckCircle2 size={18} className="text-leaf-300" />{item}</p>)}
            </div>
          </aside>
          <main className="p-7 sm:p-10">
            <h2 className="text-2xl font-black text-slate-900">{t('register.title')}</h2>
            <p className="mt-2 text-sm text-slate-500">{t('register.formText')}</p>
            <form onSubmit={handleSubmit(onSubmit)} className="mt-7 space-y-4" noValidate>
              {fields.map((field) => (
                <label key={field.name} className="block">
                  <span className="mb-2 block text-sm font-semibold text-slate-700">{field.label}</span>
                  <input type={field.type || 'text'} className="input-control" placeholder={field.placeholder} {...register(field.name)} />
                  {errors[field.name] && <span className="mt-1.5 block text-xs font-medium text-rose-600">{errors[field.name].message}</span>}
                </label>
              ))}
              {serverError && <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{serverError}</p>}
              <button className="btn-primary mt-2 w-full !py-3.5" disabled={isSubmitting}>{isSubmitting ? t('register.submitting') : t('register.submit')} <ArrowRight size={17} /></button>
            </form>
            <p className="mt-6 text-center text-sm text-slate-500">{t('register.hasAccount')} <Link to="/login" className="font-bold text-leaf-700">{t('common.login')}</Link></p>
          </main>
        </div>
      </div>
    </div>
  )
}
