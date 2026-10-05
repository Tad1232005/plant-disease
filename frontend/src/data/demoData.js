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
}

export const initialFarms = [
  { id: 1, name: 'Vườn cà chua A1', location: 'Đà Lạt, Lâm Đồng', crop: 'Cà chua', area: 2.4, status: 'healthy', lastScan: '15/08/2026' },
  { id: 2, name: 'Khu khoai tây B2', location: 'Đơn Dương, Lâm Đồng', crop: 'Khoai tây', area: 3.1, status: 'attention', lastScan: '14/08/2026' },
  { id: 3, name: 'Nhà lưới ươm giống', location: 'Đức Trọng, Lâm Đồng', crop: 'Ớt chuông', area: 1.2, status: 'healthy', lastScan: '12/08/2026' },
  { id: 4, name: 'Ruộng ngô C3', location: 'Củ Chi, TP.HCM', crop: 'Ngô', area: 4.6, status: 'risk', lastScan: '10/08/2026' },
]

export const initialManagedUsers = [
  { id: 201, username: 'farmer.an', full_name: 'Nguyễn Văn An', email: 'farmer.an@plantcare.vn', role: 'user', farmId: '1', farmName: 'Vườn cà chua A1', status: 'active' },
  { id: 202, username: 'tech.khoa', full_name: 'Trần Minh Khoa', email: 'tech.khoa@plantcare.vn', role: 'technician', farmId: '2', farmName: 'Khu khoai tây B2', status: 'active' },
  { id: 203, username: 'farmer.linh', full_name: 'Phạm Ngọc Linh', email: 'farmer.linh@plantcare.vn', role: 'user', farmId: '3', farmName: 'Nhà lưới ươm giống', status: 'active' },
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
  { id: 1, date: '15/08/2026 09:42', farm: 'Vườn cà chua A1', result: 'Lá khỏe mạnh', confidence: 96.8, severity: 'low', is_valid_leaf: true, treatment: 'Tiếp tục theo dõi định kỳ và duy trì chế độ chăm sóc hiện tại.' },
  { id: 2, date: '14/08/2026 16:20', farm: 'Khu khoai tây B2', result: 'Đốm vòng khoai tây', confidence: 88.4, severity: 'medium', is_valid_leaf: true, treatment: 'Loại bỏ lá bệnh, vệ sinh dụng cụ và cân đối dinh dưỡng.' },
  { id: 3, date: '12/08/2026 08:05', farm: 'Nhà lưới ươm giống', result: 'Lá khỏe mạnh', confidence: 94.1, severity: 'low', is_valid_leaf: true, treatment: 'Duy trì tưới tiêu và theo dõi lá non.' },
  { id: 4, date: '10/08/2026 15:31', farm: 'Ruộng ngô C3', result: 'Gỉ sắt ngô', confidence: 91.2, severity: 'high', is_valid_leaf: true, treatment: 'Cách ly khu vực có dấu hiệu bệnh và liên hệ kỹ thuật viên.' },
  { id: 5, date: '09/08/2026 11:05', farm: 'Không gắn khu vực', result: 'Ảnh ngoài miền dữ liệu', confidence: 34.6, severity: 'medium', is_valid_leaf: false, treatment: 'Chụp lại một lá cây rõ nét dưới ánh sáng tự nhiên.' },
]

export const initialProposals = [
  { id: 501, disease_name: 'Đốm lá vi khuẩn cà chua', label_key: 'tomato_bacterial_spot', plant: 'Cà chua', symptoms: 'Đốm nhỏ màu nâu đen, có quầng vàng quanh vết bệnh.', treatment: 'Loại bỏ lá bệnh, hạn chế làm ướt lá và vệ sinh dụng cụ.', evidence: 'Quan sát trên 4 mẫu tại Vườn cà chua A1.', status: 'pending', created_at: '18/08/2026 09:20' },
  { id: 502, disease_name: 'Khảm lá ớt', label_key: 'pepper_mosaic', plant: 'Ớt', symptoms: 'Lá loang màu và hơi biến dạng.', treatment: 'Cách ly cây nghi nhiễm và kiểm soát côn trùng môi giới.', evidence: 'Đối chiếu 3 ảnh chẩn đoán gần nhất.', status: 'approved', created_at: '16/08/2026 14:35' },
]

export const farmStatsDemo = {
  1: { total_scans: 54, healthy: 39, attention: 11, invalid: 4, trend: [5, 8, 6, 10, 7, 11, 9], diseases: [{ name: 'Khỏe mạnh', value: 39 }, { name: 'Mốc sương', value: 9 }, { name: 'Đốm lá', value: 6 }] },
  2: { total_scans: 47, healthy: 28, attention: 16, invalid: 3, trend: [4, 6, 8, 5, 9, 7, 8], diseases: [{ name: 'Khỏe mạnh', value: 28 }, { name: 'Đốm vòng', value: 13 }, { name: 'Khác', value: 6 }] },
  3: { total_scans: 31, healthy: 25, attention: 4, invalid: 2, trend: [3, 5, 4, 6, 4, 5, 4], diseases: [{ name: 'Khỏe mạnh', value: 25 }, { name: 'Khảm lá', value: 4 }, { name: 'Khác', value: 2 }] },
  4: { total_scans: 63, healthy: 35, attention: 24, invalid: 4, trend: [7, 9, 8, 12, 10, 9, 8], diseases: [{ name: 'Khỏe mạnh', value: 35 }, { name: 'Gỉ sắt', value: 21 }, { name: 'Khác', value: 7 }] },
}
