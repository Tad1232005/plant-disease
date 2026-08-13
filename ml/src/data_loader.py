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
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
    transforms.ToTensor(),
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
