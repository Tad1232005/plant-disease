"""Module service xử lý nạp mô hình MobileNetV2 và dự đoán bệnh lá cây."""

import io
import json
from typing import Any, Dict

import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torchvision import models, transforms  # type: ignore[import]

from app.core.config import settings


class PredictService:
    """Quản lý việc load model 1 lần duy nhất và thực hiện dự đoán."""

    def __init__(self) -> None:
        """Khởi tạo cấu hình, nạp nhãn và mô hình MobileNetV2 vào RAM."""
        # 1. Load danh sách lớp
        with open(settings.CLASSES_PATH, "r", encoding="utf-8") as f:
            self.classes: list[str] = json.load(f)

        # 2. Thiết lập thiết bị tính toán (GPU / CPU)
        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        # 3. Khởi tạo kiến trúc MobileNetV2 và thay thế classifier
        self.model = models.mobilenet_v2(weights=None)
        in_features = self.model.classifier[1].in_features
        self.model.classifier[1] = nn.Linear(in_features, len(self.classes))

        # 4. Nạp trọng số Model (Thêm weights_only=True để an toàn)
        state_dict = torch.load(
            settings.MODEL_PATH,
            map_location=self.device,
            weights_only=True,
        )
        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        self.model.eval()

        # 5. Pipeline tiền xử lý ảnh chuẩn (Giữ tỉ lệ ảnh, chống méo lá)
        self.transform = transforms.Compose(
            [
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ]
        )

    def predict(self, image_bytes: bytes) -> Dict[str, Any]:
        """Nhận byte ảnh, tiền xử lý và trả về kết quả dự đoán.

        Args:
            image_bytes (bytes): Dữ liệu file ảnh dạng byte thô.

        Returns:
            Dict[str, Any]: Kết quả chứa label, confidence, is_valid_leaf,
            top_k và all_probs.
        """
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        tensor = self.transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            outputs = self.model(tensor)
            probs = F.softmax(outputs, dim=1)[0]

        # Tìm nhãn có độ tin cậy cao nhất
        best_idx = int(torch.argmax(probs))
        confidence = float(probs[best_idx])
        label = self.classes[best_idx]
        is_valid_leaf = confidence >= settings.CONFIDENCE_THRESHOLD

        # Lấy Top 3 kết quả cao nhất (Rất hữu ích cho Frontend hiển thị)
        topk_conf, topk_idx = torch.topk(probs, k=min(3, len(self.classes)))
        top_k = [
            {
                "label": self.classes[idx.item()],
                "confidence": round(conf.item(), 4),
                "rank": rank,
            }
            for rank, (conf, idx) in enumerate(
                zip(topk_conf, topk_idx), start=1
            )
        ]

        # Bảng xác suất cho toàn bộ danh sách lớp (được làm tròn 4 chữ số)
        all_probs = {
            self.classes[i]: round(float(probs[i]), 4)
            for i in range(len(self.classes))
        }

        return {
            "label": label,
            "confidence": round(confidence, 4),
            "is_valid_leaf": is_valid_leaf,
            "top_k": top_k,
            "all_probs": all_probs,
        }


# Khởi tạo 1 instance duy nhất khi app khởi động (Singleton Pattern)
predict_service = PredictService()