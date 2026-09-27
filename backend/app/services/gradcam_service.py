"""Grad-CAM explanation generation for PyTorch models.

Tách riêng logic hook layer và sinh heatmap overlay để predict_service
tập trung vào inference và ensemble.
"""

from __future__ import annotations

import io
from typing import Any, cast

import numpy as np
from PIL import Image
import torch
import torch.nn as nn
import torch.nn.functional as F

from app.core.exceptions import ModelConfigurationError


def get_gradcam_target_layer(model: nn.Module, model_type: str) -> nn.Module:
    """Return the final convolutional block for a supported backbone."""
    if model_type in {"efficientnet_b0", "mobilenet_v2"}:
        return cast(nn.Sequential, getattr(model, "features"))[-1]
    if model_type == "resnet50":
        return cast(nn.Sequential, getattr(model, "layer4"))[-1]
    raise ModelConfigurationError(f"Grad-CAM không hỗ trợ model_type: {model_type}")


def compute_gradcam_overlay(
    model: nn.Module,
    classes: list[str],
    image: Image.Image,
    target_label: str,
    device: torch.device,
    transform: Any,
    model_type: str,
) -> bytes:
    """Tính toán Grad-CAM overlay heatmap và trả về PNG bytes."""
    try:
        target_index = classes.index(target_label)
    except ValueError as exc:
        raise ModelConfigurationError(
            "Nhãn của Scan không thuộc classes của model đã lưu"
        ) from exc

    tensor = transform(image).unsqueeze(0).to(device)
    activations: torch.Tensor | None = None
    gradients: torch.Tensor | None = None

    def forward_hook(_module: nn.Module, _inputs: Any, output: torch.Tensor) -> None:
        nonlocal activations
        activations = output

    def backward_hook(
        _module: nn.Module,
        _grad_inputs: Any,
        grad_outputs: tuple[torch.Tensor, ...],
    ) -> None:
        nonlocal gradients
        gradients = grad_outputs[0]

    target_layer = get_gradcam_target_layer(model, model_type)
    forward_handle = target_layer.register_forward_hook(forward_hook)
    backward_handle = target_layer.register_full_backward_hook(backward_hook)
    try:
        model.zero_grad(set_to_none=True)
        logits = model(tensor)
        if logits.shape != (1, len(classes)) or not torch.isfinite(logits).all():
            raise ModelConfigurationError("Logits không hợp lệ khi tạo Grad-CAM")
        logits[0, target_index].backward()
        if activations is None or gradients is None:
            raise ModelConfigurationError("Không lấy được activation/gradient cho Grad-CAM")
        weights = gradients.mean(dim=(2, 3), keepdim=True)
        heatmap = torch.relu((weights * activations).sum(dim=1, keepdim=True))
        heatmap = F.interpolate(
            heatmap,
            size=(image.height, image.width),
            mode="bilinear",
            align_corners=False,
        )[0, 0]
        heatmap = heatmap - heatmap.min()
        maximum = heatmap.max()
        if not torch.isfinite(maximum) or float(maximum.detach()) <= 0:
            raise ModelConfigurationError("Grad-CAM không có vùng kích hoạt hợp lệ")
        normalized = (heatmap / maximum).detach().cpu().numpy()
    finally:
        forward_handle.remove()
        backward_handle.remove()
        model.zero_grad(set_to_none=True)

    # A compact jet-like palette avoids an OpenCV runtime dependency.
    red = np.clip(1.5 - np.abs(4 * normalized - 3), 0, 1)
    green = np.clip(1.5 - np.abs(4 * normalized - 2), 0, 1)
    blue = np.clip(1.5 - np.abs(4 * normalized - 1), 0, 1)
    colors = np.stack((red, green, blue), axis=-1) * 255.0
    source = np.asarray(image, dtype=np.float32)
    overlay = np.clip(source * 0.60 + colors * 0.40, 0, 255).astype(np.uint8)
    output = io.BytesIO()
    Image.fromarray(overlay, mode="RGB").save(output, format="PNG", optimize=True)
    return output.getvalue()
