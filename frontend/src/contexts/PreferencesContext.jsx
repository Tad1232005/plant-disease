import { createContext, useContext, useEffect, useMemo, useState } from 'react'

const STORAGE_LANGUAGE = 'plantcare_language'
const STORAGE_THEME = 'plantcare_theme'

const messages = {
  vi: {
    'common.login': 'Đăng nhập', 'common.register': 'Đăng ký', 'common.home': 'Trang chủ', 'common.logout': 'Đăng xuất',
    'common.features': 'Tính năng', 'common.users': 'Đối tượng', 'common.workflow': 'Quy trình', 'common.loading': 'Đang tải...', 'common.results': 'kết quả', 'common.actions': 'Thao tác', 'common.page': 'Trang', 'common.previous': 'Trang trước', 'common.next': 'Trang sau', 'common.noData': 'Chưa có dữ liệu', 'common.noDataText': 'Dữ liệu mới sẽ xuất hiện tại đây.', 'common.search': 'Tìm kiếm...', 'common.cancel': 'Hủy', 'common.saving': 'Đang lưu...', 'common.save': 'Lưu thay đổi', 'common.select': 'Chọn', 'common.close': 'Đóng', 'common.closeDialog': 'Đóng hộp thoại', 'common.confirmDelete': 'Xác nhận xóa', 'common.deleteData': 'Xóa dữ liệu',
    'preferences.language': 'Đổi ngôn ngữ', 'preferences.light': 'Chế độ sáng', 'preferences.dark': 'Chế độ tối',
    'nav.workspace': 'Không gian làm việc', 'nav.dashboard': 'Tổng quan', 'nav.scan': 'Chẩn đoán mới', 'nav.history': 'Lịch sử chẩn đoán',
    'nav.farms': 'Quản lý trang trại', 'nav.people': 'Quản lý nhân sự', 'nav.farmDashboard': 'Dashboard theo Farm', 'nav.proposals': 'Đề xuất bệnh', 'nav.diseases': 'Thư viện bệnh',
    'header.hello': 'Xin chào,', 'header.notifications': 'Thông báo', 'header.menu': 'Mở menu',
    'landing.badge': 'Công nghệ AI hỗ trợ nông nghiệp thông minh', 'landing.title1': 'Phát hiện bệnh lá cây', 'landing.title2': 'sớm hơn', 'landing.title3': ', chăm sóc tốt hơn.',
    'landing.description': 'PlantCare AI giúp nhận diện bệnh từ ảnh, cung cấp độ tin cậy và hỗ trợ bạn chủ động bảo vệ cây trồng.',
    'landing.guestCta': 'Chẩn đoán ngay không cần đăng nhập', 'landing.accountCta': 'Tạo tài khoản để lưu lịch sử', 'landing.explore': 'Khám phá tính năng',
    'landing.benefit1': 'Hỗ trợ VI/EN', 'landing.benefit2': 'Kết quả trực quan', 'landing.benefit3': 'Phân quyền 5 vai trò',
    'landing.featureEyebrow': 'Tính năng cốt lõi', 'landing.featureTitle': 'Mọi công cụ cần thiết trên một nền tảng', 'landing.featureDescription': 'Từ một tấm ảnh đến thông tin hỗ trợ ra quyết định, được thiết kế rõ ràng và dễ sử dụng trên cả điện thoại.',
    'landing.feature1Title': 'Chẩn đoán từ ảnh', 'landing.feature1Text': 'Tải hoặc chụp ảnh lá cây, nhận kết quả và độ tin cậy chỉ trong vài giây.',
    'landing.feature2Title': 'Gợi ý xử lý dễ hiểu', 'landing.feature2Text': 'Thông tin triệu chứng và hướng xử lý được trình bày rõ cho từng loại bệnh.',
    'landing.feature3Title': 'Theo dõi theo khu vực', 'landing.feature3Text': 'Người có tài khoản được lưu lịch sử và theo dõi từng trang trại.',
    'landing.roleEyebrow': '5 vai trò trong hệ thống', 'landing.roleTitle': 'Đúng quyền cho đúng người dùng', 'landing.roleDescription': 'Guest dùng nhanh không cần tài khoản; các vai trò khác được bảo vệ đúng theo quyền.',
    'landing.guestTitle': 'Khách', 'landing.guestText': 'Chẩn đoán và xem kết quả, không lưu lịch sử.', 'landing.farmerTitle': 'Nông dân', 'landing.farmerText': 'Tự đăng ký, quét ảnh và xem lịch sử cá nhân.',
    'landing.technicianTitle': 'Kỹ thuật viên', 'landing.technicianText': 'Xem Grad-CAM và gửi đề xuất nội dung bệnh.', 'landing.managerTitle': 'Quản lý', 'landing.managerText': 'Quản lý Farm, Managed User và Dashboard theo khu vực.',
    'landing.adminTitle': 'Admin', 'landing.adminText': 'Tạo Technician/Manager, duyệt đề xuất và quản lý model.',
    'landing.startTitle': 'Bắt đầu chẩn đoán chỉ trong vài phút', 'landing.startText': 'Bạn có thể dùng ngay với tư cách Guest hoặc đăng ký để lưu lại lịch sử.',
    'landing.analysisResult': 'Kết quả phân tích', 'landing.checked': 'AI đã kiểm tra', 'landing.topResult': 'Kết quả hàng đầu', 'landing.confidence': 'Độ tin cậy', 'landing.uploaded': 'Ảnh đã tải lên', 'landing.sampleImage': 'Lá cà chua • Farm A1', 'landing.sampleDisease': 'Mốc sương cà chua', 'landing.sampleAdvice': 'Nên kiểm tra thêm mặt dưới lá và theo dõi vùng trồng trong 2–3 ngày tới.', 'landing.processingTime': 'Thời gian xử lý', 'landing.underFive': 'Dưới 5 giây', 'landing.footer': 'Đồ án Plant Disease Detection • React + FastAPI + PyTorch',
    'login.title': 'Chào mừng trở lại', 'login.description': 'Đăng nhập bằng tài khoản backend hoặc chọn nhanh một tài khoản demo.', 'login.username': 'Tên đăng nhập', 'login.password': 'Mật khẩu',
    'login.usernamePlaceholder': 'Nhập tên đăng nhập', 'login.passwordPlaceholder': 'Nhập mật khẩu', 'login.submit': 'Đăng nhập', 'login.submitting': 'Đang đăng nhập...', 'login.demo': 'TÀI KHOẢN DEMO',
    'login.noAccount': 'Chưa có tài khoản?', 'login.registerNow': 'Đăng ký ngay', 'login.guest': 'Tiếp tục với tư cách Guest', 'login.admin': 'Bạn là quản trị viên?', 'login.adminPanel': 'Mở Admin Panel', 'login.heroTitle': 'Hiểu cây trồng. Hành động đúng lúc.', 'login.heroText': 'Đăng nhập để chẩn đoán hình ảnh, xem lịch sử và quản lý sức khỏe cây trồng trên một giao diện duy nhất.', 'login.heroSecurity': 'Phân quyền riêng cho từng nhóm người dùng', 'login.footer': 'Hệ thống nhận diện bệnh lá cây', 'login.passwordToggle': 'Hiện hoặc ẩn mật khẩu',
    'register.title': 'Thông tin tài khoản', 'register.description': 'Tài khoản tự đăng ký luôn là Nông dân; Technician và Manager do Admin tạo.', 'register.fullName': 'Họ và tên', 'register.confirmPassword': 'Nhập lại mật khẩu',
    'register.submit': 'Tạo tài khoản', 'register.submitting': 'Đang tạo tài khoản...', 'register.hasAccount': 'Đã có tài khoản?', 'register.eyebrow': 'Tạo tài khoản', 'register.heroTitle': 'Bắt đầu quản lý sức khỏe cây trồng hôm nay.', 'register.heroText': 'Tài khoản tự đăng ký luôn là Nông dân. Manager tạo Managed User; Admin tạo Technician và Manager.', 'register.benefit1': 'Chẩn đoán ảnh lá cây', 'register.benefit2': 'Lưu lịch sử từng lần quét', 'register.benefit3': 'Quản lý khu vực trồng', 'register.formText': 'Điền thông tin để tạo tài khoản Nông dân.', 'register.email': 'Email', 'register.password': 'Mật khẩu', 'register.namePlaceholder': 'Nguyễn Văn An', 'register.userPlaceholder': 'nguyenvanan', 'register.emailPlaceholder': 'ban@example.com', 'register.passwordPlaceholder': 'Tối thiểu 6 ký tự',
    'scan.eyebrow': 'Chẩn đoán AI', 'scan.title': 'Chẩn đoán bệnh lá cây', 'scan.userDescription': 'Chụp hoặc tải ảnh, kiểm tra OOD, xem gợi ý xử lý và lưu lịch sử cá nhân.', 'scan.guestDescription': 'Chẩn đoán miễn phí không cần đăng nhập. Kết quả chỉ hiển thị trong phiên này và không lưu lịch sử.',
    'scan.farm': 'Gắn với khu vực', 'scan.optional': 'Không chọn khu vực', 'scan.privacy': 'Ảnh dùng cho mục đích chẩn đoán', 'scan.analyze': 'Phân tích bệnh', 'scan.analyzing': 'Đang phân tích...',
    'guest.badge': 'Chế độ Guest • Không cần tài khoản', 'guest.noHistory': 'Kết quả không được lưu vào lịch sử', 'guest.saveHistory': 'Đăng nhập để lưu lịch sử',
    'upload.drop': 'Kéo thả ảnh lá cây vào đây', 'upload.help': 'Chọn ảnh có sẵn hoặc dùng camera sau. Hỗ trợ JPG, PNG, WEBP tối đa 8 MB.', 'upload.library': 'Chọn từ thư viện', 'upload.camera': 'Chụp ảnh', 'upload.other': 'Chọn ảnh khác', 'upload.retake': 'Chụp lại', 'upload.previewAlt': 'Ảnh lá cây đã chọn', 'upload.previewHelp': 'Kiểm tra ảnh rõ nét và phần lá chiếm phần lớn khung hình.', 'upload.remove': 'Xóa ảnh',
    'result.waitTitle': 'Kết quả sẽ hiển thị tại đây', 'result.waitText': 'Chọn một ảnh rõ nét, sau đó nhấn “Phân tích bệnh” để bắt đầu.', 'result.loadingTitle': 'AI đang phân tích ảnh', 'result.loadingText': 'Đang kiểm tra OOD, đặc trưng trên lá và xếp hạng kết quả...',
    'result.failed': 'Chưa thể phân tích ảnh', 'result.demo': 'Xem kết quả mẫu', 'result.prediction': 'Kết quả dự đoán', 'result.ood': 'Cảnh báo OOD', 'result.invalid': 'Ảnh không phải lá hợp lệ',
    'result.confidence': 'Độ tin cậy', 'result.top': 'Top kết quả mô hình', 'result.treatment': 'Gợi ý xử lý', 'result.disclaimer': 'Kết quả AI chỉ mang tính hỗ trợ. Hãy đối chiếu triệu chứng thực tế trước khi xử lý.', 'result.reset': 'Chẩn đoán ảnh khác', 'result.invalidTitle': 'Ảnh nằm ngoài miền dữ liệu.', 'result.invalidText': 'Hãy chụp riêng một lá cây, tránh tay người, chậu hoặc nền chiếm quá nhiều khung hình.',
    'managed.eyebrow': 'Tuần 4 • Managed User & Farm Members', 'managed.title': 'Quản lý Managed User', 'managed.description': 'Manager chỉ tạo tài khoản Managed User (vai trò User) và gán vào Farm phụ trách. Technician và Manager do Admin tạo.', 'managed.add': 'Thêm Managed User', 'managed.total': 'Tổng Managed User', 'managed.assigned': 'Đã phân công', 'managed.unassigned': 'Chưa phân công', 'managed.initialPassword': 'Mật khẩu ban đầu', 'managed.farm': 'Gán vào trang trại', 'managed.createTitle': 'Tạo Managed User', 'managed.createText': 'Tài khoản luôn có vai trò User, không thể tự đăng ký và sẽ được gán vào một Farm.', 'managed.create': 'Tạo và phân công',
    'gradcam.title': 'Grad-CAM cho Kỹ thuật viên', 'gradcam.text': 'Tạo bản đồ nhiệt để xem vùng lá ảnh hưởng nhiều nhất đến dự đoán.', 'gradcam.create': 'Tạo ảnh giải thích', 'gradcam.loading': 'Đang tạo Grad-CAM...', 'gradcam.alt': 'Bản đồ nhiệt Grad-CAM', 'gradcam.explain': 'Vùng đỏ/vàng là khu vực mô hình tập trung khi đưa ra dự đoán. Đây là công cụ giải thích, không thay thế đánh giá chuyên môn.',
  },
  en: {
    'common.login': 'Sign in', 'common.register': 'Register', 'common.home': 'Home', 'common.logout': 'Sign out',
    'common.features': 'Features', 'common.users': 'Users', 'common.workflow': 'How it works', 'common.loading': 'Loading...', 'common.results': 'results', 'common.actions': 'Actions', 'common.page': 'Page', 'common.previous': 'Previous page', 'common.next': 'Next page', 'common.noData': 'No data yet', 'common.noDataText': 'New data will appear here.', 'common.search': 'Search...', 'common.cancel': 'Cancel', 'common.saving': 'Saving...', 'common.save': 'Save changes', 'common.select': 'Select', 'common.close': 'Close', 'common.closeDialog': 'Close dialog', 'common.confirmDelete': 'Confirm deletion', 'common.deleteData': 'Delete data',
    'preferences.language': 'Change language', 'preferences.light': 'Light mode', 'preferences.dark': 'Dark mode',
    'nav.workspace': 'Workspace', 'nav.dashboard': 'Overview', 'nav.scan': 'New diagnosis', 'nav.history': 'Diagnosis history',
    'nav.farms': 'Farm management', 'nav.people': 'Managed users', 'nav.farmDashboard': 'Farm dashboard', 'nav.proposals': 'Disease proposals', 'nav.diseases': 'Disease library',
    'header.hello': 'Hello,', 'header.notifications': 'Notifications', 'header.menu': 'Open menu',
    'landing.badge': 'AI technology for smarter agriculture', 'landing.title1': 'Detect plant diseases', 'landing.title2': 'earlier', 'landing.title3': ', care better.',
    'landing.description': 'PlantCare AI identifies plant diseases from images, shows confidence, and helps you protect crops proactively.',
    'landing.guestCta': 'Diagnose now without signing in', 'landing.accountCta': 'Create an account to save history', 'landing.explore': 'Explore features',
    'landing.benefit1': 'Vietnamese & English', 'landing.benefit2': 'Clear visual results', 'landing.benefit3': 'Five-role access control',
    'landing.featureEyebrow': 'Core features', 'landing.featureTitle': 'Everything you need in one platform', 'landing.featureDescription': 'From an image to decision-support information, designed to be clear and mobile-friendly.',
    'landing.feature1Title': 'Image diagnosis', 'landing.feature1Text': 'Upload or capture a leaf image and receive a prediction with confidence in seconds.',
    'landing.feature2Title': 'Actionable guidance', 'landing.feature2Text': 'Symptoms and treatment guidance are clearly presented for each disease.',
    'landing.feature3Title': 'Farm-based tracking', 'landing.feature3Text': 'Signed-in users can save history and monitor each farm.',
    'landing.roleEyebrow': 'Five system roles', 'landing.roleTitle': 'The right access for every user', 'landing.roleDescription': 'Guests can start instantly, while registered roles receive protected, role-specific tools.',
    'landing.guestTitle': 'Guest', 'landing.guestText': 'Diagnose and view results without saving history.', 'landing.farmerTitle': 'Farmer', 'landing.farmerText': 'Self-register, scan images, and view personal history.',
    'landing.technicianTitle': 'Technician', 'landing.technicianText': 'View Grad-CAM and submit disease content proposals.', 'landing.managerTitle': 'Manager', 'landing.managerText': 'Manage farms, managed users, and farm dashboards.',
    'landing.adminTitle': 'Admin', 'landing.adminText': 'Create Technicians/Managers, review proposals, and manage models.',
    'landing.startTitle': 'Start diagnosing in minutes', 'landing.startText': 'Continue as a Guest or register an account to save your diagnosis history.',
    'landing.analysisResult': 'Analysis result', 'landing.checked': 'AI checked', 'landing.topResult': 'Top result', 'landing.confidence': 'Confidence', 'landing.uploaded': 'Uploaded image', 'landing.sampleImage': 'Tomato leaf • Farm A1', 'landing.sampleDisease': 'Tomato late blight', 'landing.sampleAdvice': 'Check the underside of the leaf and monitor the growing area for the next 2–3 days.', 'landing.processingTime': 'Processing time', 'landing.underFive': 'Under 5 seconds', 'landing.footer': 'Plant Disease Detection project • React + FastAPI + PyTorch',
    'login.title': 'Welcome back', 'login.description': 'Sign in with your backend account or select a demo account.', 'login.username': 'Username', 'login.password': 'Password',
    'login.usernamePlaceholder': 'Enter username', 'login.passwordPlaceholder': 'Enter password', 'login.submit': 'Sign in', 'login.submitting': 'Signing in...', 'login.demo': 'DEMO ACCOUNTS',
    'login.noAccount': 'No account yet?', 'login.registerNow': 'Register now', 'login.guest': 'Continue as Guest', 'login.admin': 'Are you an administrator?', 'login.adminPanel': 'Open Admin Panel', 'login.heroTitle': 'Understand your crops. Act at the right time.', 'login.heroText': 'Sign in to diagnose images, review history, and manage plant health in one place.', 'login.heroSecurity': 'Role-specific access for every user group', 'login.footer': 'Plant disease detection system', 'login.passwordToggle': 'Show or hide password',
    'register.title': 'Account information', 'register.description': 'Self-registered accounts are always Farmers; Technicians and Managers are created by Admin.', 'register.fullName': 'Full name', 'register.confirmPassword': 'Confirm password',
    'register.submit': 'Create account', 'register.submitting': 'Creating account...', 'register.hasAccount': 'Already have an account?', 'register.eyebrow': 'Create account', 'register.heroTitle': 'Start managing plant health today.', 'register.heroText': 'Self-registered accounts are always Farmers. Managers create Managed Users; Admin creates Technicians and Managers.', 'register.benefit1': 'Diagnose leaf images', 'register.benefit2': 'Save every scan in history', 'register.benefit3': 'Manage growing areas', 'register.formText': 'Enter your details to create a Farmer account.', 'register.email': 'Email', 'register.password': 'Password', 'register.namePlaceholder': 'Alex Nguyen', 'register.userPlaceholder': 'alexnguyen', 'register.emailPlaceholder': 'you@example.com', 'register.passwordPlaceholder': 'At least 6 characters',
    'scan.eyebrow': 'AI diagnosis', 'scan.title': 'Plant disease diagnosis', 'scan.userDescription': 'Capture or upload a photo, check OOD, view guidance, and save personal history.', 'scan.guestDescription': 'Free diagnosis without signing in. Results are shown only in this session and are not saved.',
    'scan.farm': 'Attach to farm', 'scan.optional': 'No farm selected', 'scan.privacy': 'Image used for diagnostic purposes', 'scan.analyze': 'Analyze disease', 'scan.analyzing': 'Analyzing...',
    'guest.badge': 'Guest mode • No account required', 'guest.noHistory': 'Results are not saved to history', 'guest.saveHistory': 'Sign in to save history',
    'upload.drop': 'Drop a leaf image here', 'upload.help': 'Choose an existing image or use the rear camera. JPG, PNG, WEBP up to 8 MB.', 'upload.library': 'Choose from library', 'upload.camera': 'Take photo', 'upload.other': 'Choose another', 'upload.retake': 'Retake', 'upload.previewAlt': 'Selected leaf image', 'upload.previewHelp': 'Make sure the leaf is sharp and fills most of the frame.', 'upload.remove': 'Remove image',
    'result.waitTitle': 'Results will appear here', 'result.waitText': 'Choose a clear image, then select “Analyze disease” to begin.', 'result.loadingTitle': 'AI is analyzing the image', 'result.loadingText': 'Checking OOD, leaf features, and ranking predictions...',
    'result.failed': 'Unable to analyze image', 'result.demo': 'View sample result', 'result.prediction': 'Prediction result', 'result.ood': 'OOD warning', 'result.invalid': 'Image is not a valid leaf',
    'result.confidence': 'Confidence', 'result.top': 'Top model predictions', 'result.treatment': 'Suggested action', 'result.disclaimer': 'AI results are decision support only. Verify real symptoms before treatment.', 'result.reset': 'Diagnose another image', 'result.invalidTitle': 'Image is outside the model domain.', 'result.invalidText': 'Capture one clear leaf without hands, pots, or background taking up most of the frame.',
    'managed.eyebrow': 'Week 4 • Managed User & Farm Members', 'managed.title': 'Managed User management', 'managed.description': 'Managers create only Managed User accounts (User role) and assign them to their farms. Technicians and Managers are created by Admin.', 'managed.add': 'Add Managed User', 'managed.total': 'Total Managed Users', 'managed.assigned': 'Assigned', 'managed.unassigned': 'Unassigned', 'managed.initialPassword': 'Initial password', 'managed.farm': 'Assign to farm', 'managed.createTitle': 'Create Managed User', 'managed.createText': 'This account always has the User role, cannot self-register, and will be assigned to a farm.', 'managed.create': 'Create and assign',
    'gradcam.title': 'Grad-CAM for Technicians', 'gradcam.text': 'Generate a heatmap showing which leaf regions most influenced the prediction.', 'gradcam.create': 'Generate explanation', 'gradcam.loading': 'Generating Grad-CAM...', 'gradcam.alt': 'Grad-CAM heatmap', 'gradcam.explain': 'Red and yellow areas show where the model focused. This explanation tool does not replace professional assessment.',
  },
}

const PreferencesContext = createContext(null)

function initialTheme() {
  const saved = localStorage.getItem(STORAGE_THEME)
  if (saved === 'dark' || saved === 'light') return saved
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function PreferencesProvider({ children }) {
  const [language, setLanguage] = useState(() => localStorage.getItem(STORAGE_LANGUAGE) || 'vi')
  const [theme, setTheme] = useState(initialTheme)

  useEffect(() => {
    document.documentElement.lang = language
    localStorage.setItem(STORAGE_LANGUAGE, language)
  }, [language])

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    document.documentElement.style.colorScheme = theme
    localStorage.setItem(STORAGE_THEME, theme)
  }, [theme])

  const value = useMemo(() => ({
    language,
    setLanguage,
    theme,
    toggleTheme: () => setTheme((current) => current === 'dark' ? 'light' : 'dark'),
    t: (key) => messages[language]?.[key] || messages.vi[key] || key,
  }), [language, theme])

  return <PreferencesContext.Provider value={value}>{children}</PreferencesContext.Provider>
}

export function usePreferences() {
  const context = useContext(PreferencesContext)
  if (!context) throw new Error('usePreferences must be used inside PreferencesProvider')
  return context
}
