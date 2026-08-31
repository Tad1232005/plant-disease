"""
Định nghĩa model — hỗ trợ MobileNetV2, ResNet50, EfficientNet cho transfer learning.
"""

import torch.nn as nn
from torchvision import models


def build_model(num_classes: int, model_type: str = "mobilenet_v2", pretrained: bool = True):
    """
    Build model với transfer learning.
    
    Args:
        num_classes: Số lượng class output
        model_type: Loại model ("mobilenet_v2", "resnet50", "efficientnet_b0")
        pretrained: Có dùng pretrained weights không
    
    Returns:
        nn.Module: Model đã modify classifier
    """
    if model_type == "mobilenet_v2":
        model = models.mobilenet_v2(weights="IMAGENET1K_V1" if pretrained else None)
        in_features = model.classifier[1].in_features
        model.classifier[1] = nn.Linear(in_features, num_classes)
        
    elif model_type == "resnet50":
        model = models.resnet50(weights="IMAGENET1K_V2" if pretrained else None)
        in_features = model.fc.in_features
        model.fc = nn.Linear(in_features, num_classes)
        
    elif model_type == "efficientnet_b0":
        model = models.efficientnet_b0(weights="IMAGENET1K_V1" if pretrained else None)
        in_features = model.classifier[1].in_features
        model.classifier[1] = nn.Linear(in_features, num_classes)
        
    else:
        raise ValueError(f"Model type không được hỗ trợ: {model_type}. "
                        f"Chọn: mobilenet_v2, resnet50, efficientnet_b0")

    return model
