import { zodResolver } from '@hookform/resolvers/zod'
import { ArrowLeft, ArrowRight, Eye, EyeOff, Leaf, ShieldCheck } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { z } from 'zod'
import Brand from '../../components/common/Brand.jsx'
import PreferenceControls from '../../components/common/PreferenceControls.jsx'
import { useAuth } from '../../contexts/AuthContext.jsx'
import { usePreferences } from '../../contexts/PreferencesContext.jsx'
import { getHomeForRole } from '../../utils/roles.js'

const schema = z.object({
  username: z.string().trim().min(3, 'Tên đăng nhập cần ít nhất 3 ký tự'),
  password: z.string().min(6, 'Mật khẩu cần ít nhất 6 ký tự'),
})

const ADMIN_URL = import.meta.env.VITE_ADMIN_URL || 'http://localhost:5174'

export default function LoginPage() {
  const [showPassword, setShowPassword] = useState(false)
  const [serverError, setServerError] = useState('')
  const { login, user, isAuthenticated } = useAuth()
  const { t } = usePreferences()
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
      navigate(requested || getHomeForRole(profile.role), { replace: true })
    } catch (error) {
      if (error.code === 'ADMIN_ACCOUNT') {
        window.location.assign(`${ADMIN_URL}/login`)
        return
      }
      setServerError(error.message)
    }
  }

  return (
    <div className="grid min-h-screen bg-[#f8fbf9] lg:grid-cols-[.92fr_1.08fr]">
      <aside className="relative hidden overflow-hidden bg-leaf-900 p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="absolute -right-24 -top-24 h-80 w-80 rounded-full border-[70px] border-white/5" />
        <div className="absolute -bottom-20 -left-20 h-72 w-72 rounded-full bg-leaf-500/10 blur-2xl" />
        <Brand light />
        <div className="relative max-w-lg">
          <span className="grid h-14 w-14 place-items-center rounded-2xl bg-white/10 text-leaf-200"><Leaf size={28} /></span>
          <h1 className="mt-7 text-4xl font-black leading-tight">{t('login.heroTitle')}</h1>
          <p className="mt-5 max-w-md leading-8 text-leaf-100/65">{t('login.heroText')}</p>
          <div className="mt-9 flex items-center gap-3 text-sm text-leaf-100/70"><ShieldCheck size={20} className="text-leaf-300" />{t('login.heroSecurity')}</div>
        </div>
        <p className="relative text-xs text-leaf-200/40">PlantCare AI • {t('login.footer')}</p>
      </aside>

      <main className="flex items-center justify-center p-5 sm:p-10">
        <div className="w-full max-w-lg">
          <div className="mb-8 flex items-center justify-between lg:hidden"><Brand /><div className="flex items-center gap-2"><PreferenceControls compact /><Link to="/" className="hidden text-sm font-semibold text-slate-500 sm:inline">{t('common.home')}</Link></div></div>
          <div className="mb-7 hidden items-center justify-between lg:flex"><Link to="/" className="inline-flex items-center gap-2 text-sm font-semibold text-slate-500 hover:text-leaf-700"><ArrowLeft size={17} />{t('common.home')}</Link><PreferenceControls /></div>
          <h2 className="text-3xl font-black tracking-tight text-slate-900">{t('login.title')}</h2>
          <p className="mt-2 text-sm leading-6 text-slate-500">{t('login.description')}</p>

          <form onSubmit={handleSubmit(onSubmit)} className="mt-7 space-y-5" noValidate>
            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-slate-700">{t('login.username')}</span>
              <input className="input-control !py-3" placeholder={t('login.usernamePlaceholder')} {...register('username')} />
              {errors.username && <span className="mt-1.5 block text-xs font-medium text-rose-600">{errors.username.message}</span>}
            </label>
            <label className="block">
              <span className="mb-2 block text-sm font-semibold text-slate-700">{t('login.password')}</span>
              <span className="relative block">
                <input type={showPassword ? 'text' : 'password'} className="input-control !py-3 pr-11" placeholder={t('login.passwordPlaceholder')} {...register('password')} />
                <button type="button" className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-700" onClick={() => setShowPassword((value) => !value)} aria-label={t('login.passwordToggle')}>
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </span>
              {errors.password && <span className="mt-1.5 block text-xs font-medium text-rose-600">{errors.password.message}</span>}
            </label>
            {serverError && <p className="rounded-xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{serverError}</p>}
            <button className="btn-primary w-full !py-3.5" disabled={isSubmitting}>{isSubmitting ? t('login.submitting') : t('login.submit')} <ArrowRight size={17} /></button>
          </form>
          <Link to="/guest/scan" className="btn-secondary mt-6 w-full">{t('login.guest')} <ArrowRight size={17} /></Link>
          <p className="mt-7 text-center text-sm text-slate-500">{t('login.noAccount')} <Link to="/register" className="font-bold text-leaf-700 hover:text-leaf-800">{t('login.registerNow')}</Link></p>
          <p className="mt-3 text-center text-sm text-slate-500">{t('login.admin')} <a href={`${ADMIN_URL}/login`} className="font-bold text-leaf-700 hover:text-leaf-800">{t('login.adminPanel')}</a></p>
        </div>
      </main>
    </div>
  )
}
