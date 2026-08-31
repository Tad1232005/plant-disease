"""
Load ảnh từ thư mục đã export + transform/augment dùng chung cho train & evaluate.

Train/evaluate chỉ đọc file ảnh trên disk — không tải lại từ Hugging Face.
"""

from pathlib import Path

from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms

from config import load_config

_cfg = load_config()
IMAGE_SIZE = _cfg["train"]["image_size"]

train_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomVerticalFlip(p=0.2),                                  # lá chụp lộn chiều cũng thường gặp ngoài thực tế
    transforms.RandomRotation(30),                                         # tăng từ 15 -> 30, ảnh thực tế góc chụp lệch nhiều hơn ảnh studio
    transforms.ColorJitter(brightness=0.4, contrast=0.4,
                            saturation=0.3, hue=0.05),                     # mạnh hơn để quen ánh sáng tự nhiên thay vì đèn studio đều
    transforms.RandomAffine(degrees=0, translate=(0.1, 0.1),
                             scale=(0.8, 1.2), shear=10),                  # mô phỏng lá không nằm giữa khung, xa/gần khác nhau
    transforms.RandomPerspective(distortion_scale=0.3, p=0.3),             # mô phỏng góc chụp nghiêng, không thẳng như ảnh studio
    transforms.RandomApply([transforms.GaussianBlur(kernel_size=3)], p=0.2),  # mô phỏng ảnh mờ do rung tay/lấy nét kém khi chụp thực tế
    transforms.ToTensor(),
    transforms.RandomErasing(p=0.2, scale=(0.02, 0.15)),                   # che ngẫu nhiên 1 phần ảnh -> ép model không chỉ dựa vào 1 vùng/nền cố định
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])

eval_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])


class PlantDiseaseDataset(Dataset):
    """
    Đọc ảnh từ cấu trúc thư mục dạng:
        data_dir/
            Tomato___healthy/
                img1.jpg
            Tomato___Early_blight/
                ...
    """

    def __init__(self, data_dir, transform=None):
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.classes = sorted(d.name for d in self.data_dir.iterdir() if d.is_dir())
        self.class_to_idx = {cls_name: i for i, cls_name in enumerate(self.classes)}

        self.samples = []
        for cls_name in self.classes:
            cls_dir = self.data_dir / cls_name
            for img_path in cls_dir.glob("*"):
                if img_path.suffix.lower() in (".jpg", ".jpeg", ".png"):
                    self.samples.append((img_path, self.class_to_idx[cls_name]))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        image = Image.open(img_path).convert("RGB")
        if self.transform:
            image = self.transform(image)
        return image, label