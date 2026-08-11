import { useState } from 'react'

export default function UploadImage({ onFileSelect, previewUrl }) {
  const [dragActive, setDragActive] = useState(false)

  function handleChange(e) {
    const file = e.target.files?.[0]
    if (file) onFileSelect(file)
  }

  function handleDrop(e) {
    e.preventDefault()
    setDragActive(false)
    const file = e.dataTransfer.files?.[0]
    if (file) onFileSelect(file)
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragActive(true) }}
      onDragLeave={() => setDragActive(false)}
      onDrop={handleDrop}
      style={{
        border: `2px dashed ${dragActive ? '#4CAF50' : '#ccc'}`,
        borderRadius: 8,
        padding: 24,
        textAlign: 'center',
        cursor: 'pointer',
        background: dragActive ? '#f0fff0' : '#fafafa',
      }}
    >
      {previewUrl ? (
        <img src={previewUrl} alt="preview" style={{ maxWidth: '100%', maxHeight: 300, borderRadius: 8 }} />
      ) : (
        <p>Kéo thả ảnh lá cây vào đây, hoặc chọn file bên dưới</p>
      )}
      <input type="file" accept="image/*" onChange={handleChange} style={{ marginTop: 12 }} />
    </div>
  )
}
