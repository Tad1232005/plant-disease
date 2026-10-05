/**
 * Tiện ích nén và tối ưu hóa ảnh trước khi upload (Client-side Image Compressor)
 * Giúp giảm dung lượng từ 5MB-20MB xuống dưới 1MB (~200KB - 600KB)
 * Đảm bảo tương thích hoàn toàn với camera smartphone và mạng di động 3G/4G chập chờn.
 */

export async function compressImage(
  file,
  options = { maxDimension: 1280, quality: 0.82 }
) {
  const { maxDimension = 1280, quality = 0.82 } = options

  // Nếu không phải ảnh hợp lệ, trả về nguyên bản
  if (!file || !file.type.startsWith('image/')) {
    return {
      file,
      originalSize: file?.size || 0,
      compressedSize: file?.size || 0,
      wasCompressed: false,
    }
  }

  // Nếu file vốn đã nhẹ (< 600 KB), chỉ nén nếu cần thiết
  const originalSize = file.size
  if (originalSize < 600 * 1024) {
    return {
      file,
      originalSize,
      compressedSize: originalSize,
      wasCompressed: false,
    }
  }

  return new Promise((resolve) => {
    const reader = new FileReader()

    reader.onload = (readerEvent) => {
      const img = new Image()
      img.onload = () => {
        let width = img.naturalWidth || img.width
        let height = img.naturalHeight || img.height

        // Tính toán kích thước mới bảo toàn tỷ lệ khung hình
        if (width > maxDimension || height > maxDimension) {
          if (width > height) {
            height = Math.round((height * maxDimension) / width)
            width = maxDimension
          } else {
            width = Math.round((width * maxDimension) / height)
            height = maxDimension
          }
        }

        const canvas = document.createElement('canvas')
        canvas.width = width
        canvas.height = height

        const ctx = canvas.getContext('2d')
        if (!ctx) {
          return resolve({
            file,
            originalSize,
            compressedSize: originalSize,
            wasCompressed: false,
          })
        }

        // Bật chế độ làm mịn chất lượng cao
        ctx.imageSmoothingEnabled = true
        ctx.imageSmoothingQuality = 'high'
        ctx.drawImage(img, 0, 0, width, height)

        // Xuất ra định dạng JPEG nén nhẹ
        canvas.toBlob(
          (blob) => {
            if (!blob || blob.size >= originalSize) {
              return resolve({
                file,
                originalSize,
                compressedSize: originalSize,
                wasCompressed: false,
              })
            }

            // Tạo đối tượng File mới giữ nguyên tên gốc
            const compressedFile = new File([blob], file.name.replace(/\.[^/.]+$/, '') + '.jpg', {
              type: 'image/jpeg',
              lastModified: Date.now(),
            })

            resolve({
              file: compressedFile,
              originalSize,
              compressedSize: compressedFile.size,
              wasCompressed: true,
            })
          },
          'image/jpeg',
          quality
        )
      }

      img.onerror = () => {
        resolve({
          file,
          originalSize,
          compressedSize: originalSize,
          wasCompressed: false,
        })
      }

      img.src = readerEvent.target?.result
    }

    reader.onerror = () => {
      resolve({
        file,
        originalSize,
        compressedSize: originalSize,
        wasCompressed: false,
      })
    }

    reader.readAsDataURL(file)
  })
}

/**
 * Định dạng dung lượng byte sang KB/MB dễ đọc
 */
export function formatBytes(bytes, decimals = 1) {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
}
