"""
Định nghĩa model — baseline dùng transfer learning MobileNetV2 (nhẹ, train nhanh,
phù hợp deadline 8 tuần). Có thể đổi sang efficientnet_b0/resnet50 sau khi có baseline.
"""

import torch.nn as nn
from torchvision import models


def build_model(num_classes: int, pretrained: bool = True):
    model = models.mobilenet_v2(weights="IMAGENET1K_V1" if pretrained else None)

    # Đóng băng phần backbone ở giai đoạn đầu, chỉ train lại classifier
    # (bỏ comment 2 dòng dưới nếu muốn fine-tune nhẹ trước khi train toàn bộ)
    # for param in model.features.parameters():
    #     param.requires_grad = False

    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)

    return model
