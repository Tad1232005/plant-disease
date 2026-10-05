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

export const initialUsers = [
  {
    id: 101,
    username: 'farmer',
    full_name: 'Nguyễn Văn An',
    email: 'farmer@plantcare.vn',
    role: 'user',
    status: 'active',
    created_at: '2026-08-10 08:30:00',
  },
  {
    id: 102,
    username: 'technician',
    full_name: 'Trần Minh Khoa',
    email: 'technician@plantcare.vn',
    role: 'technician',
    status: 'active',
    created_at: '2026-08-11 09:15:00',
  },
  {
    id: 103,
    username: 'manager',
    full_name: 'Lê Hoàng Nam',
    email: 'manager@plantcare.vn',
    role: 'manager',
    status: 'active',
    created_at: '2026-08-12 10:20:00',
  },
  {
    id: 104,
    username: 'admin',
    full_name: 'Quản trị viên',
    email: 'admin@plantcare.vn',
    role: 'admin',
    status: 'active',
    created_at: '2026-08-01 07:00:00',
  },
]

export const initialModelVersions = [
  {
    id: 1,
    version_name: 'mobilenet_v2_primary_v2.1',
    model_type: 'mobilenet_v2',
    temperature: 1.042,
    accuracy: 0.9482,
    status: 'production',
    is_active: true,
    is_enabled: true,
    created_at: '2026-09-15 14:20:00',
  },
  {
    id: 2,
    version_name: 'efficientnet_b0_advanced_v1.8',
    model_type: 'efficientnet_b0',
    temperature: 0.985,
    accuracy: 0.9315,
    status: 'staging',
    is_active: false,
    is_enabled: true,
    created_at: '2026-09-28 11:05:00',
  },
  {
    id: 3,
    version_name: 'resnet50_experimental_v1.0',
    model_type: 'resnet50',
    temperature: null,
    accuracy: 0.912,
    status: 'inactive',
    is_active: false,
    is_enabled: false,
    created_at: '2026-08-20 09:30:00',
  },
]

export const initialSystemStats = {
  total_users: 29,
  total_scans: 148,
  total_farms: 4,
  active_model: 'mobilenet_v2_primary_v2.1',
  scans_by_day: [14, 22, 18, 29, 31, 24, 16],
  users_by_role: [
    { role: 'user', count: 18, name: 'Nông dân' },
    { role: 'technician', count: 5, name: 'Kỹ thuật viên' },
    { role: 'manager', count: 4, name: 'Quản lý' },
    { role: 'admin', count: 2, name: 'Quản trị viên' },
  ],
  disease_counts: [
    { name: 'Mốc sương cà chua', count: 42 },
    { name: 'Đốm vòng khoai tây', count: 35 },
    { name: 'Gỉ sắt ngô', count: 29 },
    { name: 'Lá khỏe mạnh', count: 22 },
  ],
}

export const initialProposals = [
  { id: 501, disease_name: 'Đốm lá vi khuẩn cà chua', label_key: 'tomato_bacterial_spot', plant: 'Cà chua', symptoms: 'Đốm nhỏ màu nâu đen, có quầng vàng quanh vết bệnh.', treatment: 'Loại bỏ lá bệnh, hạn chế làm ướt lá và vệ sinh dụng cụ.', evidence: 'Quan sát trên 4 mẫu tại Vườn cà chua A1.', proposer_name: 'Trần Minh Khoa', status: 'pending', created_at: '18/08/2026 09:20' },
  { id: 502, disease_name: 'Khảm lá ớt', label_key: 'pepper_mosaic', plant: 'Ớt', symptoms: 'Lá loang màu và hơi biến dạng.', treatment: 'Cách ly cây nghi nhiễm và kiểm soát côn trùng môi giới.', evidence: 'Đối chiếu 3 ảnh chẩn đoán gần nhất.', proposer_name: 'Trần Minh Khoa', status: 'approved', created_at: '16/08/2026 14:35' },
  { id: 503, disease_name: 'Vàng lá khoai tây', label_key: 'potato_yellow_leaf', plant: 'Khoai tây', symptoms: 'Lá vàng từ mép, sinh trưởng chậm.', treatment: 'Kiểm tra đất và dinh dưỡng trước khi xử lý.', evidence: 'Một mẫu đơn lẻ, cần bổ sung dữ liệu.', proposer_name: 'Nguyễn Hải Nam', status: 'rejected', created_at: '15/08/2026 10:15', admin_note: 'Chưa đủ bằng chứng chuyên môn.' },
]
