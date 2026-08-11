export default function ResultCard({ result, loading, error }) {
  if (loading) return <p>Đang phân tích ảnh...</p>
  if (error) return <p style={{ color: 'crimson' }}>Lỗi: {error}</p>
  if (!result) return null

  const confidencePercent = (result.confidence * 100).toFixed(1)

  return (
    <div style={{
      marginTop: 20,
      padding: 16,
      borderRadius: 8,
      background: '#f5f5f5',
      border: '1px solid #ddd',
    }}>
      <h3 style={{ margin: '0 0 8px' }}>Kết quả dự đoán</h3>
      <p><strong>Nhãn bệnh:</strong> {result.label}</p>
      <p><strong>Độ tin cậy:</strong> {confidencePercent}%</p>
      <div style={{ background: '#e0e0e0', borderRadius: 4, height: 8, marginTop: 8 }}>
        <div
          style={{
            width: `${confidencePercent}%`,
            background: confidencePercent > 70 ? '#4CAF50' : '#FFA726',
            height: '100%',
            borderRadius: 4,
            transition: 'width 0.3s',
          }}
        />
      </div>
    </div>
  )
}
