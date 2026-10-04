import { ArrowRight, BarChart3, Camera, CheckCircle2, ChevronRight, Leaf, ScanSearch, ShieldCheck, Sparkles, Sprout, Stethoscope, UserCog, UserRound } from 'lucide-react'
import { Link } from 'react-router-dom'
import Brand from '../../components/common/Brand.jsx'
import PreferenceControls from '../../components/common/PreferenceControls.jsx'
import { usePreferences } from '../../contexts/PreferencesContext.jsx'

export default function LandingPage() {
  const { t } = usePreferences()
  const features = [
    { icon: Camera, title: t('landing.feature1Title'), text: t('landing.feature1Text') },
    { icon: Stethoscope, title: t('landing.feature2Title'), text: t('landing.feature2Text') },
    { icon: BarChart3, title: t('landing.feature3Title'), text: t('landing.feature3Text') },
  ]
  const personas = [
    { icon: UserRound, title: t('landing.guestTitle'), text: t('landing.guestText') },
    { icon: Sprout, title: t('landing.farmerTitle'), text: t('landing.farmerText') },
    { icon: ScanSearch, title: t('landing.technicianTitle'), text: t('landing.technicianText') },
    { icon: BarChart3, title: t('landing.managerTitle'), text: t('landing.managerText') },
    { icon: UserCog, title: t('landing.adminTitle'), text: t('landing.adminText') },
  ]
  return (
    <div className="min-h-screen bg-white">
      <header className="sticky top-0 z-30 border-b border-slate-100 bg-white/90 backdrop-blur-xl">
        <div className="page-container flex h-20 items-center justify-between">
          <Brand />
          <nav className="hidden items-center gap-8 text-sm font-semibold text-slate-500 lg:flex">
            <a href="#features" className="hover:text-leaf-700">{t('common.features')}</a>
            <a href="#users" className="hover:text-leaf-700">{t('common.users')}</a>
            <a href="#workflow" className="hover:text-leaf-700">{t('common.workflow')}</a>
          </nav>
          <div className="flex items-center gap-2">
            <PreferenceControls compact />
            <Link to="/login" className="hidden px-3 py-2 text-sm font-semibold text-slate-600 hover:text-leaf-700 md:block">{t('common.login')}</Link>
            <Link to="/guest/scan" className="btn-primary hidden sm:inline-flex">{t('landing.guestTitle')} <ArrowRight size={16} /></Link>
          </div>
        </div>
      </header>

      <main>
        <section className="overflow-hidden bg-hero-glow py-16 sm:py-24">
          <div className="page-container grid items-center gap-14 lg:grid-cols-[1.05fr_.95fr]">
            <div>
              <span className="inline-flex items-center gap-2 rounded-full border border-leaf-200 bg-white px-3 py-1.5 text-xs font-bold text-leaf-700 shadow-sm">
                <Sparkles size={14} /> {t('landing.badge')}
              </span>
              <h1 className="mt-6 max-w-3xl text-4xl font-black leading-[1.1] tracking-tight text-slate-900 sm:text-6xl">
                {t('landing.title1')} <span className="text-leaf-600">{t('landing.title2')}</span>{t('landing.title3')}
              </h1>
              <p className="mt-6 max-w-2xl text-base leading-8 text-slate-600 sm:text-lg">
                {t('landing.description')}
              </p>
              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Link to="/guest/scan" className="btn-primary !px-6 !py-3.5">{t('landing.guestCta')} <ArrowRight size={18} /></Link>
                <Link to="/register" className="btn-secondary !px-6 !py-3.5">{t('landing.accountCta')} <ChevronRight size={18} /></Link>
              </div>
              <div className="mt-8 flex flex-wrap gap-x-6 gap-y-3 text-sm text-slate-500">
                {[t('landing.benefit1'), t('landing.benefit2'), t('landing.benefit3')].map((item) => (
                  <span key={item} className="inline-flex items-center gap-2"><CheckCircle2 className="text-leaf-500" size={17} />{item}</span>
                ))}
              </div>
            </div>

            <div className="relative mx-auto w-full max-w-xl">
              <div className="absolute -left-8 top-8 h-36 w-36 rounded-full bg-leaf-200/50 blur-3xl" />
              <div className="absolute -right-8 bottom-8 h-44 w-44 rounded-full bg-emerald-100 blur-3xl" />
              <div className="card relative overflow-hidden p-4 sm:p-6">
                <div className="mb-5 flex items-center justify-between">
                  <div><p className="text-xs font-semibold text-slate-400">{t('landing.analysisResult').toUpperCase()}</p><p className="mt-1 font-bold text-slate-800">{t('landing.sampleImage')}</p></div>
                  <span className="rounded-full bg-leaf-50 px-3 py-1 text-xs font-bold text-leaf-700">{t('landing.checked')}</span>
                </div>
                <div className="grid gap-4 sm:grid-cols-[1fr_1.15fr]">
                  <div className="relative flex min-h-56 items-center justify-center overflow-hidden rounded-2xl bg-gradient-to-br from-leaf-100 via-emerald-50 to-lime-100">
                    <Leaf className="rotate-[-18deg] text-leaf-600 drop-shadow-lg" size={122} strokeWidth={1.35} fill="#55c47d" />
                    <span className="absolute left-[42%] top-[40%] h-8 w-8 rounded-full border-2 border-amber-400 bg-amber-300/35 ring-4 ring-white/60" />
                    <span className="absolute bottom-3 left-3 rounded-lg bg-white/90 px-2.5 py-1 text-[10px] font-bold text-slate-600 shadow-sm">{t('landing.uploaded')}</span>
                  </div>
                  <div className="rounded-2xl border border-leaf-100 bg-leaf-50/60 p-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-leaf-600 text-white"><ShieldCheck size={20} /></div>
                    <p className="mt-4 text-xs font-bold uppercase tracking-wider text-leaf-600">{t('landing.topResult')}</p>
                    <h3 className="mt-1 text-xl font-extrabold text-slate-900">{t('landing.sampleDisease')}</h3>
                    <div className="mt-5 flex items-end justify-between"><span className="text-sm text-slate-500">{t('landing.confidence')}</span><strong className="text-2xl text-leaf-700">94.8%</strong></div>
                    <div className="mt-2 h-2 overflow-hidden rounded-full bg-white"><div className="h-full w-[94.8%] rounded-full bg-leaf-500" /></div>
                    <p className="mt-5 rounded-xl bg-white p-3 text-xs leading-5 text-slate-500">{t('landing.sampleAdvice')}</p>
                  </div>
                </div>
              </div>
              <div className="absolute -bottom-5 -left-5 hidden items-center gap-3 rounded-2xl border border-white bg-white p-3 shadow-soft sm:flex">
                <span className="grid h-10 w-10 place-items-center rounded-xl bg-amber-50 text-amber-600"><Sparkles size={19} /></span>
                <div><p className="text-xs text-slate-400">{t('landing.processingTime')}</p><p className="text-sm font-extrabold text-slate-800">{t('landing.underFive')}</p></div>
              </div>
            </div>
          </div>
        </section>

        <section id="features" className="py-20 sm:py-24">
          <div className="page-container">
            <div className="mx-auto max-w-2xl text-center">
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-leaf-600">{t('landing.featureEyebrow')}</p>
              <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">{t('landing.featureTitle')}</h2>
              <p className="mt-4 leading-7 text-slate-500">{t('landing.featureDescription')}</p>
            </div>
            <div className="mt-12 grid gap-5 md:grid-cols-3">
              {features.map(({ icon: Icon, title, text }) => (
                <article key={title} className="rounded-3xl border border-slate-100 bg-white p-7 shadow-soft transition hover:-translate-y-1">
                  <span className="grid h-12 w-12 place-items-center rounded-2xl bg-leaf-50 text-leaf-700"><Icon size={23} /></span>
                  <h3 className="mt-5 text-lg font-extrabold text-slate-900">{title}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-500">{text}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section id="users" className="bg-leaf-50/60 py-20 sm:py-24">
          <div className="page-container">
            <div className="mx-auto max-w-3xl text-center">
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-leaf-600">{t('landing.roleEyebrow')}</p>
              <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">{t('landing.roleTitle')}</h2>
              <p className="mt-4 leading-7 text-slate-500">{t('landing.roleDescription')}</p>
            </div>
            <div className="mt-10 grid auto-rows-fr gap-4 sm:grid-cols-2 lg:grid-cols-5">
              {personas.map(({ icon: Icon, title, text }, index) => (
                <article
  key={title}
  className={`flex h-full flex-col rounded-3xl border bg-white p-6 shadow-soft ${
    index === 0 ? 'border-leaf-300' : 'border-white'
  }`}
>
                  <span className="grid h-11 w-11 place-items-center rounded-2xl bg-leaf-100 text-leaf-700"><Icon size={21} /></span>
                  <h3 className="mt-5 font-extrabold text-slate-900">{title}</h3>
                  <p className="mt-2 text-sm leading-6 text-slate-500">{text}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section id="workflow" className="py-20">
          <div className="page-container rounded-[2rem] bg-leaf-900 px-6 py-12 text-center text-white sm:px-12">
            <p className="text-sm font-bold text-leaf-200">PLANTCARE AI</p>
            <h2 className="mx-auto mt-3 max-w-2xl text-3xl font-extrabold">{t('landing.startTitle')}</h2>
            <p className="mx-auto mt-4 max-w-xl text-sm leading-7 text-leaf-100/70">{t('landing.startText')}</p>
            <div className="mt-7 flex flex-col justify-center gap-3 sm:flex-row"><Link to="/guest/scan" className="inline-flex items-center justify-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-bold text-leaf-800 hover:bg-leaf-50">{t('landing.guestCta')} <ArrowRight size={17} /></Link><Link to="/register" className="inline-flex items-center justify-center rounded-xl border border-white/25 px-5 py-3 text-sm font-bold text-white hover:bg-white/10">{t('common.register')}</Link></div>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-100 py-8">
        <div className="page-container flex flex-col items-center justify-between gap-4 text-center sm:flex-row sm:text-left">
          <Brand />
          <p className="text-xs text-slate-400">{t('landing.footer')}</p>
        </div>
      </footer>
    </div>
  )
}
