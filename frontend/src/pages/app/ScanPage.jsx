import { ScanLine, ShieldCheck } from 'lucide-react'
import { useEffect, useState } from 'react'
import { getApiError } from '../../api/client.js'
import { predictImage } from '../../api/predict.js'
import ResultCard from '../../components/ResultCard.jsx'
import UploadImage from '../../components/UploadImage.jsx'
import PageHeader from '../../components/common/PageHeader.jsx'
import { initialFarms } from '../../data/demoData.js'
import { loadCollection } from '../../utils/storage.js'

const DEMO_RESULT = {
  label: 'tomato_late_blight', confidence: 0.948,
  top_k: [
    { label: 'tomato_late_blight', confidence: 0.948, rank: 1 },
    { label: 'tomato_early_blight', confidence: 0.034, rank: 2 },
    { label: 'tomato_healthy', confidence: 0.018, rank: 3 },
  ],
}

export default function ScanPage() {
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [validationError, setValidationError] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [farmId, setFarmId] = useState('')
  const farms = loadCollection('plantcare_farms', initialFarms)

  useEffect(() => () => { if (previewUrl) URL.revokeObjectURL(previewUrl) }, [previewUrl])

  function handleFileSelect(nextFile) {
    setValidationError(''); setError(''); setResult(null)
    if (!['image/jpeg', 'image/png', 'image/webp'].includes(nextFile.type)) { setValidationError('Ảnh không hợp lệ. Vui lòng chọn file JPG, PNG hoặc WEBP.'); return }
    if (nextFile.size > 8 * 1024 * 1024) { setValidationError('Dung lượng ảnh vượt quá 8 MB.'); return }
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    setFile(nextFile); setPreviewUrl(URL.createObjectURL(nextFile))
  }

  function clearFile() {
    if (previewUrl) URL.revokeObjectURL(previewUrl)
    setFile(null); setPreviewUrl(''); setResult(null); setError(''); setValidationError('')
  }

  async function analyze() {
    if (!file) { setValidationError('Vui lòng chọn ảnh lá cây trước khi phân tích.'); return }
    setLoading(true); setError(''); setResult(null)
    try { setResult(await predictImage(file)) }
    catch (requestError) { setError(getApiError(requestError, 'Không thể phân tích ảnh.')) }
    finally { setLoading(false) }
  }

  return (
    <div className="mx-auto max-w-7xl">
      <PageHeader eyebrow="Chức năng cốt lõi" title="Chẩn đoán bệnh lá cây" description="Tải ảnh rõ nét để mô hình nhận diện nhãn bệnh, độ tin cậy và top 3 khả năng." />
      <div className="mb-6 grid gap-4 rounded-3xl border border-leaf-100 bg-leaf-50/60 p-4 sm:grid-cols-[1fr_auto] sm:items-center sm:p-5">
        <label><span className="mb-2 block text-xs font-bold uppercase tracking-wider text-leaf-700">Gắn với khu vực (không bắt buộc)</span><select className="input-control max-w-md" value={farmId} onChange={(event) => setFarmId(event.target.value)}><option value="">Không chọn khu vực</option>{farms.map((farm) => <option key={farm.id} value={farm.id}>{farm.name}</option>)}</select></label>
        <div className="flex items-center gap-2 text-xs text-leaf-800"><ShieldCheck size={17} /><span>Ảnh dùng cho mục đích chẩn đoán</span></div>
      </div>
      <div className="grid items-start gap-6 xl:grid-cols-[1.15fr_.85fr]">
        <div><UploadImage onFileSelect={handleFileSelect} previewUrl={previewUrl} fileName={file?.name} validationError={validationError} onClear={clearFile} /><button className="btn-primary mt-4 w-full !py-3.5" disabled={!file || loading} onClick={analyze}><ScanLine size={19} />{loading ? 'Đang phân tích...' : 'Phân tích bệnh'}</button></div>
        <ResultCard result={result} loading={loading} error={error} onUseDemo={() => { setError(''); setResult(DEMO_RESULT) }} />
      </div>
    </div>
  )
}
