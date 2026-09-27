import { ArrowLeft, Leaf } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useLanguage } from '../contexts/LanguageContext.jsx'

export default function NotFoundPage() {
  const { t } = useLanguage()
  return <div className="grid min-h-screen place-items-center bg-leaf-50 p-6 text-center"><div><span className="mx-auto grid h-20 w-20 place-items-center rounded-3xl bg-white text-leaf-700 shadow-soft"><Leaf size={34} /></span><p className="mt-7 text-sm font-bold uppercase tracking-[0.2em] text-leaf-600">404</p><h1 className="mt-2 text-3xl font-black text-slate-900">{t('notfound.title')}</h1><p className="mt-3 text-sm text-slate-500">{t('notfound.desc')}</p><Link to="/" className="btn-primary mt-7"><ArrowLeft size={17} /> {t('notfound.home')}</Link></div></div>
}
