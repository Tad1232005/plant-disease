"""Service xử lý load model và inference dự đoán bệnh lá cây."""

import io
import json

import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms  # type: ignore[import]

from app.core.config import settings


class PredictService:
    """Quản lý việc load model 1 lần và chạy dự đoán."""

    def __init__(self) -> None:
        # load danh sách lớp
        with open(settings.CLASSES_PATH, "r", encoding="utf-8") as f:
            self.classes = json.load(f)

        # device và model
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )
        self.model = models.mobilenet_v2(weights=None)
        in_features = self.model.classifier[1].in_features
        self.model.classifier[1] = nn.Linear(in_features, len(self.classes))
        state_dict = torch.load(settings.MODEL_PATH, map_location=self.device)
        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        self.model.eval()

        # transform chuẩn cho model
        self.transform = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ]
        )

    def predict(self, image_bytes: bytes) -> dict:
        """Nhận ảnh bytes, trả về label, confidence và all_probs."""
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        tensor = self.transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            outputs = self.model(tensor)
            probs = torch.nn.functional.softmax(outputs, dim=1)[0]

        all_probs = {
            self.classes[i]: float(probs[i]) for i in range(len(self.classes))
        }
        best_idx = int(torch.argmax(probs))
        label = self.classes[best_idx]
        confidence = float(probs[best_idx])
        is_valid_leaf = confidence >= settings.CONFIDENCE_THRESHOLD

        return {
            "label": label,
            "confidence": confidence,
            "is_valid_leaf": is_valid_leaf,
            "all_probs": all_probs,
        }


# Khởi tạo 1 lần duy nhất khi app start, dùng chung cho mọi request
predict_service = PredictService()
