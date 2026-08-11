import { useState } from 'react'
import UploadImage from './components/UploadImage.jsx'
import ResultCard from './components/ResultCard.jsx'
import { predictImage } from './api/predict.js'

export default function App() {
  const [previewUrl, setPreviewUrl] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleFileSelect(file) {
    setPreviewUrl(URL.createObjectURL(file))
    setResult(null)
    setError(null)
    setLoading(true)

    try {
      const data = await predictImage(file)
      setResult(data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Không thể kết nối tới server, thử lại sau.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 480, margin: '40px auto', fontFamily: 'sans-serif', padding: '0 16px' }}>
      <h1 style={{ fontSize: 22 }}>🌿 Nhận diện bệnh lá cây</h1>
      <p style={{ color: '#666' }}>Upload ảnh lá cây để nhận diện bệnh và độ tin cậy của mô hình.</p>

      <UploadImage onFileSelect={handleFileSelect} previewUrl={previewUrl} />
      <ResultCard result={result} loading={loading} error={error} />
    </div>
  )
}
