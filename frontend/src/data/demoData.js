export const demoUsers = {
  farmer: {
    id: 101,
    username: 'farmer',
    password: '123456',
    full_name: 'Nguyễn Văn An',
    email: 'farmer@plantcare.vn',
    role: 'user',
  },
  technician: {
    id: 102,
    username: 'technician',
    password: '123456',
    full_name: 'Trần Minh Khoa',
    email: 'technician@plantcare.vn',
    role: 'technician',
  },
  manager: {
    id: 103,
    username: 'manager',
    password: '123456',
    full_name: 'Lê Hoàng Nam',
    email: 'manager@plantcare.vn',
    role: 'manager',
  },
  admin: {
    id: 104,
    username: 'admin',
    password: '123456',
    full_name: 'Quản trị viên',
    email: 'admin@plantcare.vn',
    role: 'admin',
  },
}

export const initialFarms = [
  { id: 1, name: 'Vườn cà chua A1', location: 'Đà Lạt, Lâm Đồng', crop: 'Cà chua', area: 2.4, status: 'healthy', lastScan: '15/08/2026' },
  { id: 2, name: 'Khu khoai tây B2', location: 'Đơn Dương, Lâm Đồng', crop: 'Khoai tây', area: 3.1, status: 'attention', lastScan: '14/08/2026' },
  { id: 3, name: 'Nhà lưới ươm giống', location: 'Đức Trọng, Lâm Đồng', crop: 'Ớt chuông', area: 1.2, status: 'healthy', lastScan: '12/08/2026' },
  { id: 4, name: 'Ruộng ngô C3', location: 'Củ Chi, TP.HCM', crop: 'Ngô', area: 4.6, status: 'risk', lastScan: '10/08/2026' },
]

export const initialDiseases = [
  {
    id: 1,
    labelKey: 'tomato_late_blight',
    name: 'Mốc sương cà chua',
    plant: 'Cà chua',
    severity: 'high',
    symptoms: 'Đốm nâu sẫm lan nhanh trên lá, thường xuất hiện khi độ ẩm cao.',
    treatment: 'Loại bỏ lá bị bệnh, giữ vườn thông thoáng và dùng thuốc theo hướng dẫn chuyên môn.',
  },
  {
    id: 2,
    labelKey: 'potato_early_blight',
    name: 'Đốm vòng khoai tây',
    plant: 'Khoai tây',
    severity: 'medium',
    symptoms: 'Vết bệnh nâu có các vòng đồng tâm, thường xuất hiện trên lá già.',
    treatment: 'Luân canh cây trồng, vệ sinh đồng ruộng và cân đối dinh dưỡng.',
  },
  {
    id: 3,
    labelKey: 'corn_common_rust',
    name: 'Gỉ sắt ngô',
    plant: 'Ngô',
    severity: 'medium',
    symptoms: 'Các ổ nhỏ màu nâu cam xuất hiện rải rác trên hai mặt lá.',
    treatment: 'Theo dõi mật độ bệnh, ưu tiên giống kháng và xử lý theo khuyến cáo địa phương.',
  },
  {
    id: 4,
    labelKey: 'pepper_healthy',
    name: 'Lá ớt khỏe mạnh',
    plant: 'Ớt',
    severity: 'low',
    symptoms: 'Lá xanh đồng đều, không có vùng đổi màu hoặc tổn thương rõ rệt.',
    treatment: 'Tiếp tục theo dõi định kỳ và duy trì chế độ chăm sóc hiện tại.',
  },
]

export const scanHistory = [
  { id: 1, date: '15/08/2026 09:42', farm: 'Vườn cà chua A1', result: 'Lá khỏe mạnh', confidence: 96.8, severity: 'low' },
  { id: 2, date: '14/08/2026 16:20', farm: 'Khu khoai tây B2', result: 'Đốm vòng khoai tây', confidence: 88.4, severity: 'medium' },
  { id: 3, date: '12/08/2026 08:05', farm: 'Nhà lưới ươm giống', result: 'Lá khỏe mạnh', confidence: 94.1, severity: 'low' },
  { id: 4, date: '10/08/2026 15:31', farm: 'Ruộng ngô C3', result: 'Gỉ sắt ngô', confidence: 91.2, severity: 'high' },
]
