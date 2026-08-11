"""
Load model đã train (.pt) + danh sách lớp (classes.json) để phục vụ predict.

Kiến trúc model phải KHỚP với kiến trúc lúc train ở ml/src/model.py
(mobilenet_v2 + thay classifier cuối). Nếu bên ML đổi kiến trúc, cập nhật lại hàm build_model
bên dưới cho đồng bộ.
"""

import json
from pathlib import Path

import torch
import torch.nn as nn
from torchvision import models

MODEL_PATH = Path(__file__).parent / "models" / "best_model.pt"
CLASSES_PATH = Path(__file__).parent / "models" / "classes.json"

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def build_model(num_classes: int):
    model = models.mobilenet_v2(weights=None)
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)
    return model


def load_model():
    if not MODEL_PATH.exists() or not CLASSES_PATH.exists():
        raise FileNotFoundError(
            "Chưa có model. Copy 'best_model.pt' và 'classes.json' từ ml/models/ "
            "vào backend/app/models/ trước khi chạy server."
        )

    with open(CLASSES_PATH, encoding="utf-8") as f:
        classes = json.load(f)

    model = build_model(num_classes=len(classes))
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.to(DEVICE)
    model.eval()

    return model, classes
