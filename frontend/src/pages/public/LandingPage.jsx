import { ArrowRight, BarChart3, Camera, CheckCircle2, ChevronRight, Leaf, ScanSearch, ShieldCheck, Sparkles, Sprout, Stethoscope } from 'lucide-react'
import { Link } from 'react-router-dom'
import Brand from '../../components/common/Brand.jsx'

const features = [
  { icon: Camera, title: 'Chẩn đoán từ ảnh', text: 'Tải hoặc chụp ảnh lá cây, nhận kết quả và độ tin cậy chỉ trong vài giây.' },
  { icon: Stethoscope, title: 'Gợi ý xử lý dễ hiểu', text: 'Thông tin triệu chứng và hướng xử lý được trình bày rõ cho từng loại bệnh.' },
  { icon: BarChart3, title: 'Theo dõi theo khu vực', text: 'Lưu lịch sử chẩn đoán, quản lý nhiều trang trại và phát hiện xu hướng.' },
]

const personas = [
  { icon: Sprout, title: 'Nông dân', text: 'Thao tác nhanh, kết quả dễ hiểu, lưu lịch sử từng lần quét.' },
  { icon: ScanSearch, title: 'Kỹ thuật viên', text: 'Xem top dự đoán, độ tin cậy và dữ liệu chuyên môn chi tiết.' },
  { icon: BarChart3, title: 'Quản lý trang trại', text: 'Theo dõi tổng quan nhiều khu vực và ưu tiên nơi cần xử lý.' },
]

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      <header className="sticky top-0 z-30 border-b border-slate-100 bg-white/90 backdrop-blur-xl">
        <div className="page-container flex h-20 items-center justify-between">
          <Brand />
          <nav className="hidden items-center gap-8 text-sm font-semibold text-slate-500 md:flex">
            <a href="#features" className="hover:text-leaf-700">Tính năng</a>
            <a href="#users" className="hover:text-leaf-700">Đối tượng</a>
            <a href="#workflow" className="hover:text-leaf-700">Quy trình</a>
          </nav>
          <div className="flex items-center gap-2">
            <Link to="/login" className="hidden px-3 py-2 text-sm font-semibold text-slate-600 hover:text-leaf-700 sm:block">Đăng nhập</Link>
            <Link to="/register" className="btn-primary">Bắt đầu ngay <ArrowRight size={16} /></Link>
          </div>
        </div>
      </header>

      <main>
        <section className="overflow-hidden bg-hero-glow py-16 sm:py-24">
          <div className="page-container grid items-center gap-14 lg:grid-cols-[1.05fr_.95fr]">
            <div>
              <span className="inline-flex items-center gap-2 rounded-full border border-leaf-200 bg-white px-3 py-1.5 text-xs font-bold text-leaf-700 shadow-sm">
                <Sparkles size={14} /> Công nghệ AI hỗ trợ nông nghiệp thông minh
              </span>
              <h1 className="mt-6 max-w-3xl text-4xl font-black leading-[1.1] tracking-tight text-slate-900 sm:text-6xl">
                Phát hiện bệnh lá cây <span className="text-leaf-600">sớm hơn</span>, chăm sóc tốt hơn.
              </h1>
              <p className="mt-6 max-w-2xl text-base leading-8 text-slate-600 sm:text-lg">
                PlantCare AI giúp nhận diện bệnh từ ảnh, cung cấp độ tin cậy và lưu lịch sử theo từng khu vực để bạn chủ động bảo vệ cây trồng.
              </p>
              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Link to="/login" className="btn-primary !px-6 !py-3.5">Thử chẩn đoán miễn phí <ArrowRight size={18} /></Link>
                <a href="#features" className="btn-secondary !px-6 !py-3.5">Khám phá tính năng <ChevronRight size={18} /></a>
              </div>
              <div className="mt-8 flex flex-wrap gap-x-6 gap-y-3 text-sm text-slate-500">
                {['Giao diện tiếng Việt', 'Kết quả trực quan', 'Quản lý theo vai trò'].map((item) => (
                  <span key={item} className="inline-flex items-center gap-2"><CheckCircle2 className="text-leaf-500" size={17} />{item}</span>
                ))}
              </div>
            </div>

            <div className="relative mx-auto w-full max-w-xl">
              <div className="absolute -left-8 top-8 h-36 w-36 rounded-full bg-leaf-200/50 blur-3xl" />
              <div className="absolute -right-8 bottom-8 h-44 w-44 rounded-full bg-emerald-100 blur-3xl" />
              <div className="card relative overflow-hidden p-4 sm:p-6">
                <div className="mb-5 flex items-center justify-between">
                  <div><p className="text-xs font-semibold text-slate-400">KẾT QUẢ PHÂN TÍCH</p><p className="mt-1 font-bold text-slate-800">Lá cà chua • Vườn A1</p></div>
                  <span className="rounded-full bg-leaf-50 px-3 py-1 text-xs font-bold text-leaf-700">AI đã kiểm tra</span>
                </div>
                <div className="grid gap-4 sm:grid-cols-[1fr_1.15fr]">
                  <div className="relative flex min-h-56 items-center justify-center overflow-hidden rounded-2xl bg-gradient-to-br from-leaf-100 via-emerald-50 to-lime-100">
                    <Leaf className="rotate-[-18deg] text-leaf-600 drop-shadow-lg" size={122} strokeWidth={1.35} fill="#55c47d" />
                    <span className="absolute left-[42%] top-[40%] h-8 w-8 rounded-full border-2 border-amber-400 bg-amber-300/35 ring-4 ring-white/60" />
                    <span className="absolute bottom-3 left-3 rounded-lg bg-white/90 px-2.5 py-1 text-[10px] font-bold text-slate-600 shadow-sm">Ảnh đã tải lên</span>
                  </div>
                  <div className="rounded-2xl border border-leaf-100 bg-leaf-50/60 p-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-leaf-600 text-white"><ShieldCheck size={20} /></div>
                    <p className="mt-4 text-xs font-bold uppercase tracking-wider text-leaf-600">Kết quả hàng đầu</p>
                    <h3 className="mt-1 text-xl font-extrabold text-slate-900">Mốc sương cà chua</h3>
                    <div className="mt-5 flex items-end justify-between"><span className="text-sm text-slate-500">Độ tin cậy</span><strong className="text-2xl text-leaf-700">94.8%</strong></div>
                    <div className="mt-2 h-2 overflow-hidden rounded-full bg-white"><div className="h-full w-[94.8%] rounded-full bg-leaf-500" /></div>
                    <p className="mt-5 rounded-xl bg-white p-3 text-xs leading-5 text-slate-500">Nên kiểm tra thêm mặt dưới lá và theo dõi vùng trồng trong 2–3 ngày tới.</p>
                  </div>
                </div>
              </div>
              <div className="absolute -bottom-5 -left-5 hidden items-center gap-3 rounded-2xl border border-white bg-white p-3 shadow-soft sm:flex">
                <span className="grid h-10 w-10 place-items-center rounded-xl bg-amber-50 text-amber-600"><Sparkles size={19} /></span>
                <div><p className="text-xs text-slate-400">Thời gian xử lý</p><p className="text-sm font-extrabold text-slate-800">Dưới 5 giây</p></div>
              </div>
            </div>
          </div>
        </section>

        <section id="features" className="py-20 sm:py-24">
          <div className="page-container">
            <div className="mx-auto max-w-2xl text-center">
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-leaf-600">Tính năng cốt lõi</p>
              <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">Mọi công cụ cần thiết trên một nền tảng</h2>
              <p className="mt-4 leading-7 text-slate-500">Từ một tấm ảnh đến thông tin hỗ trợ ra quyết định, được thiết kế sáng, rõ và dễ sử dụng.</p>
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
          <div className="page-container grid gap-10 lg:grid-cols-[.8fr_1.2fr] lg:items-center">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-leaf-600">3 nhóm người dùng</p>
              <h2 className="mt-3 text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">Đúng thông tin cho đúng vai trò</h2>
              <p className="mt-4 leading-7 text-slate-500">Mỗi nhóm có màn hình và mức độ thông tin riêng, tránh phức tạp không cần thiết.</p>
              <Link to="/login" className="mt-7 inline-flex items-center gap-2 text-sm font-bold text-leaf-700 hover:text-leaf-800">Xem tài khoản demo <ArrowRight size={17} /></Link>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              {personas.map(({ icon: Icon, title, text }, index) => (
                <article key={title} className={`rounded-3xl border bg-white p-6 shadow-soft ${index === 1 ? 'border-leaf-200 sm:-translate-y-5' : 'border-white'}`}>
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
            <p className="text-sm font-bold text-leaf-200">BẮT ĐẦU TRONG VÀI PHÚT</p>
            <h2 className="mx-auto mt-3 max-w-2xl text-3xl font-extrabold">Chủ động phát hiện sớm vấn đề trên cây trồng của bạn</h2>
            <p className="mx-auto mt-4 max-w-xl text-sm leading-7 text-leaf-100/70">Đăng nhập, chọn khu vực, tải ảnh lá cây và theo dõi kết quả trong lịch sử chẩn đoán.</p>
            <Link to="/register" className="mt-7 inline-flex items-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-bold text-leaf-800 hover:bg-leaf-50">Tạo tài khoản <ArrowRight size={17} /></Link>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-100 py-8">
        <div className="page-container flex flex-col items-center justify-between gap-4 text-center sm:flex-row sm:text-left">
          <Brand />
          <p className="text-xs text-slate-400">Đồ án Plant Disease Detection • React + FastAPI + PyTorch</p>
        </div>
      </footer>
    </div>
  )
}
