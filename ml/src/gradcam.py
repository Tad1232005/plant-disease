"""
GradCAM - Gradient-weighted Class Activation Mapping.

Mục đích:
    - Tạo heatmap để giải thích model đang "nhìn" vào vùng nào của ảnh
    - Giúp debug model: model có nhìn đúng vùng bệnh không?
    - Visualize kết quả predict

Cách dùng:
    python ml/src/gradcam.py --image path/to/image.jpg --output heatmap.png

Output:
    heatmap.png - ảnh gốc với heatmap overlay
"""

import io
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from tqdm import tqdm

from config import load_config, ml_path
from data_loader import eval_transform
from model import build_model


class GradCAM:
    """
    GradCAM implementation cho MobileNetV2, ResNet50, EfficientNet.

    Tạo heatmap bằng cách:
    1. Forward pass để lấy feature map và output
    2. Backward pass để lấy gradient w.r.t. target class
    3. Compute weights bằng global average pooling gradient
    4. Combine weights với feature map để tạo heatmap
    """

    def __init__(self, model: nn.Module, model_type: str = "mobilenet_v2"):
        """
        Args:
            model: PyTorch model (MobileNetV2, ResNet50, EfficientNet)
            model_type: Loại model để tự động chọn target layer
        """
        self.model = model
        self.model_type = model_type
        self.gradients = None
        self.activations = None

        # Register hooks
        self._register_hooks()

    def _register_hooks(self):
        """Register forward và backward hooks để capture gradient và activation."""

        def forward_hook(module, input, output):
            self.activations = output

        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0]

        # Tìm target layer theo model type
        if self.model_type == "mobilenet_v2":
            target_module = self.model.features[-1]
        elif self.model_type == "resnet50":
            target_module = self.model.layer4[-1]
        elif self.model_type == "efficientnet_b0":
            target_module = self.model.features[-1]
        else:
            # Fallback: tìm layer cuối cùng của features
            if hasattr(self.model, 'features'):
                target_module = self.model.features[-1]
            elif hasattr(self.model, 'layer4'):
                target_module = self.model.layer4[-1]
            else:
                raise ValueError(f"Không tìm thấy target layer cho model_type: {self.model_type}")

        target_module.register_forward_hook(forward_hook)
        target_module.register_full_backward_hook(backward_hook)

    def generate_heatmap(
        self,
        input_tensor: torch.Tensor,
        target_class: Optional[int] = None,
    ) -> np.ndarray:
        """
        Generate GradCAM heatmap.
        
        Args:
            input_tensor: Input tensor [1, 3, H, W]
            target_class: Target class index (nếu None, dùng predicted class)
        
        Returns:
            np.ndarray: Heatmap [H, W] normalized 0-255
        """
        # Forward pass
        self.model.eval()
        output = self.model(input_tensor)
        
        # Get target class
        if target_class is None:
            target_class = output.argmax(dim=1).item()
        
        # Backward pass
        self.model.zero_grad()
        output[0, target_class].backward(retain_graph=True)
        
        # Get gradients và activations
        gradients = self.gradients  # [1, C, H', W']
        activations = self.activations  # [1, C, H', W']
        
        # Compute weights: global average pooling của gradients
        weights = gradients.mean(dim=[2, 3], keepdim=True)  # [1, C, 1, 1]
        
        # Weighted sum của activations
        heatmap = (weights * activations).sum(dim=1).squeeze()  # [H', W']
        
        # ReLU để chỉ giữ positive values
        heatmap = F.relu(heatmap)
        
        # Normalize về 0-255
        heatmap = heatmap - heatmap.min()
        heatmap = heatmap / (heatmap.max() + 1e-8)
        heatmap = (heatmap * 255).detach().cpu().numpy().astype(np.uint8)
        
        return heatmap

    def visualize_heatmap(
        self,
        image: Image.Image,
        heatmap: np.ndarray,
        alpha: float = 0.4,
        colormap: int = cv2.COLORMAP_JET,
    ) -> np.ndarray:
        """
        Overlay heatmap lên ảnh gốc.
        
        Args:
            image: PIL Image gốc
            heatmap: Heatmap từ generate_heatmap [H, W]
            alpha: Transparency của heatmap (0-1)
            colormap: OpenCV colormap
        
        Returns:
            np.ndarray: Ảnh với heatmap overlay [H, W, 3] (RGB)
        """
        # Resize heatmap về kích thước ảnh gốc
        heatmap_resized = cv2.resize(heatmap, (image.size[0], image.size[1]))
        
        # Apply colormap
        heatmap_colored = cv2.applyColorMap(heatmap_resized, colormap)
        heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)
        
        # Blend với ảnh gốc
        image_np = np.array(image)
        overlay = cv2.addWeighted(image_np, 1 - alpha, heatmap_colored, alpha, 0)
        
        return overlay


def generate_gradcam(
    image_path: Path,
    model_path: Path = None,
    classes_path: Path = None,
    output_path: Path = None,
    target_class: Optional[int] = None,
    model_suffix: str = None,
) -> Path:
    """
    Generate GradCAM heatmap cho 1 ảnh.
    
    Args:
        image_path: Đường dẫn đến ảnh input
        model_path: Đường dẫn đến best_model.pt
        classes_path: Đường dẫn đến classes.json
        output_path: Đường dẫn để lưu heatmap
        target_class: Target class index (nếu None, dùng predicted class)
        model_type: Loại model (mặc định từ config)
    """
    cfg = load_config()
    models_dir = ml_path(cfg["paths"]["models_dir"])

    # Load model theo suffix hoặc mặc định
    if model_suffix:
        model_path = models_dir / f"best_model_{model_suffix}.pt"
        classes_path = models_dir / f"classes_{model_suffix}.json"
        model_type_path = models_dir / f"model_type_{model_suffix}.json"

        # Đọc model_type từ file
        if model_type_path.exists():
            import json
            with open(model_type_path, encoding="utf-8") as f:
                model_type_data = json.load(f)
                model_type = model_type_data.get("model_type", "mobilenet_v2")
        else:
            model_type = "mobilenet_v2"  # Fallback
    else:
        if model_path is None:
            model_path = models_dir / "best_model.pt"
        if classes_path is None:
            classes_path = models_dir / "classes.json"
        model_type = cfg["train"].get("model_type", "mobilenet_v2")

    if output_path is None:
        output_path = image_path.parent / f"{image_path.stem}_gradcam{image_path.suffix}"
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    
    # Load classes
    import json
    with open(classes_path, encoding="utf-8") as f:
        classes = json.load(f)
    num_classes = len(classes)
    print(f"Đã load {num_classes} classes")
    print(f"Model type: {model_type}")
    
    # Load model
    print(f"Đang load model từ {model_path}...")
    model = build_model(num_classes=num_classes, model_type=model_type)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    print("Đã load model xong")
    
    # Load và preprocess ảnh
    image = Image.open(image_path).convert("RGB")
    input_tensor = eval_transform(image).unsqueeze(0).to(device)
    
    # Predict
    with torch.no_grad():
        output = model(input_tensor)
        probs = F.softmax(output, dim=1)[0]
        pred_idx = output.argmax(dim=1).item()
        confidence = probs[pred_idx].item()
    
    print(f"\nPredict: {classes[pred_idx]} ({confidence * 100:.2f}%)")

    # Create GradCAM với model_type
    gradcam = GradCAM(model, model_type=model_type)
    
    # Generate heatmap
    print("Đang generate heatmap...")
    heatmap = gradcam.generate_heatmap(input_tensor, target_class)
    
    # Visualize
    overlay = gradcam.visualize_heatmap(image, heatmap)
    
    # Save
    overlay_pil = Image.fromarray(overlay)
    overlay_pil.save(output_path)
    print(f"Đã lưu heatmap tại {output_path}")
    
    return output_path


def main():
    """CLI - generate GradCAM heatmap."""
    import argparse

    parser = argparse.ArgumentParser(description="GradCAM Heatmap Visualization")
    parser.add_argument("--image", type=str, required=True, help="Đường dẫn đến ảnh input")
    parser.add_argument("--model-path", type=str, help="Đường dẫn đến best_model.pt")
    parser.add_argument("--classes-path", type=str, help="Đường dẫn đến classes.json")
    parser.add_argument("--output", type=str, help="Đường dẫn để lưu heatmap")
    parser.add_argument(
        "--target-class",
        type=int,
        help="Target class index (nếu None, dùng predicted class)",
    )
    parser.add_argument(
        "--model-suffix",
        type=str,
        help="Suffix của model (ví dụ: resnet50, efficientnet_b0) để load model tương ứng",
    )
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"Lỗi: Không tìm thấy ảnh tại {image_path}")
        return

    generate_gradcam(
        image_path=image_path,
        model_path=Path(args.model_path) if args.model_path else None,
        classes_path=Path(args.classes_path) if args.classes_path else None,
        output_path=Path(args.output) if args.output else None,
        target_class=args.target_class,
        model_suffix=args.model_suffix,
    )


if __name__ == "__main__":
    main()
