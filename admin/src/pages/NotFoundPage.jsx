import { ArrowLeft, Leaf } from 'lucide-react'
import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return <div className="grid min-h-screen place-items-center bg-leaf-50 p-6 text-center"><div><span className="mx-auto grid h-20 w-20 place-items-center rounded-3xl bg-white text-leaf-700 shadow-soft"><Leaf size={34} /></span><p className="mt-7 text-sm font-bold uppercase tracking-[0.2em] text-leaf-600">404</p><h1 className="mt-2 text-3xl font-black text-slate-900">Không tìm thấy trang</h1><p className="mt-3 text-sm text-slate-500">Đường dẫn bạn mở không tồn tại hoặc đã được thay đổi.</p><Link to="/" className="btn-primary mt-7"><ArrowLeft size={17} /> Về trang chủ</Link></div></div>
}
