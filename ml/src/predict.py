"""
Module inference dùng chung cho ML và backend.

Chức năng:
    - Load model + classes từ file
    - Preprocess ảnh (PIL → tensor)
    - Predict: trả label + confidence + all_probs
    - Temperature scaling calibration (tùy chọn)
    - GradCAM heatmap visualization (tùy chọn)

Cách dùng:
    from predict import load_predictor
    predictor = load_predictor(use_calibration=True)
    result = predictor.predict_single(pil_image)
    # result = {"label": "Tomato___healthy", "confidence": 0.9876, "all_probs": [...]}

Test CLI:
    python ml/src/predict.py --image path/to/image.jpg
    python ml/src/predict.py --image path/to/image.jpg --calibrate
    python ml/src/predict.py --image path/to/image.jpg --gradcam --output heatmap.png
"""

import io
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image

from config import load_config, ml_path
from data_loader import eval_transform
from model import build_model


class Predictor:
    """
    Wrapper cho model inference.
    Load model 1 lần, dùng nhiều lần predict.
    """

    def __init__(
        self,
        model_path: Path = None,
        classes_path: Path = None,
        use_calibration: bool = False,
        model_type: str = None,
        model_suffix: str = None,
    ):
        """
        Args:
            model_path: Đường dẫn đến best_model.pt (mặc định từ config)
            classes_path: Đường dẫn đến classes.json (mặc định từ config)
            use_calibration: Có dùng temperature scaling không (mặc định False)
            model_type: Loại model (mặc định từ config)
            model_suffix: Suffix của model (ví dụ: resnet50, efficientnet_b0)
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
            if model_type is None:
                model_type = cfg["train"].get("model_type", "mobilenet_v2")

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Device: {self.device}")

        # Load classes
        with open(classes_path, encoding="utf-8") as f:
            self.classes = json.load(f)
        self.num_classes = len(self.classes)
        print(f"Đã load {self.num_classes} classes")
        print(f"Model type: {model_type}")

        # Load model
        print(f"Đang load model từ {model_path}...")
        self.model = build_model(num_classes=self.num_classes, model_type=model_type)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()
        print("Đã load model xong")

        # Load temperature scaling
        self.temperature = 1.0
        self.use_calibration = use_calibration
        if use_calibration:
            if model_suffix:
                temperature_path = models_dir / f"temperature_{model_suffix}.json"
            else:
                temperature_path = models_dir / "temperature.json"
            if temperature_path.exists():
                with open(temperature_path, encoding="utf-8") as f:
                    temp_data = json.load(f)
                    self.temperature = temp_data["temperature"]
                print(f"Đã load temperature scaling: T = {self.temperature:.4f}")
            else:
                print(f"Warning: Không tìm thấy {temperature_path}, dùng T = 1.0")
                print(f"Chạy 'python ml/src/calibration.py --find-temperature --model-suffix {model_suffix}' để tìm T tối ưu")

    def preprocess(self, image: Image.Image) -> torch.Tensor:
        """
        Chuyển ảnh PIL → tensor (batch=1).

        Args:
            image: PIL Image (RGB)

        Returns:
            Tensor shape [1, 3, 224, 224]
        """
        if image.mode != "RGB":
            image = image.convert("RGB")
        tensor = eval_transform(image)
        return tensor.unsqueeze(0)  # [1, C, H, W]

    def predict_single(self, image: Image.Image) -> Dict[str, object]:
        """
        Predict cho 1 ảnh.

        Args:
            image: PIL Image (RGB)

        Returns:
            Dict với keys:
                - label: str (tên class)
                - confidence: float (max probability)
                - all_probs: List[float] (38 probabilities theo thứ tự classes)
                - temperature: float (nếu dùng calibration)
        """
        # Preprocess
        input_tensor = self.preprocess(image)
        input_tensor = input_tensor.to(self.device)

        # Inference
        with torch.no_grad():
            outputs = self.model(input_tensor)  # [1, num_classes]
            
            # Apply temperature scaling nếu enabled
            if self.use_calibration:
                outputs = outputs / self.temperature
            
            probs = torch.softmax(outputs, dim=1)[0]  # [num_classes]
            probs_np = probs.cpu().numpy()

        # Get prediction
        pred_idx = int(probs.argmax().item())
        confidence = float(probs[pred_idx].item())
        label = self.classes[pred_idx]
        all_probs = probs_np.tolist()

        result = {
            "label": label,
            "confidence": confidence,
            "all_probs": all_probs,
        }
        
        if self.use_calibration:
            result["temperature"] = self.temperature
        
        return result

    def generate_gradcam(
        self,
        image: Image.Image,
        target_class: Optional[int] = None,
    ) -> Tuple[np.ndarray, int]:
        """
        Generate GradCAM heatmap cho 1 ảnh.
        
        Args:
            image: PIL Image (RGB)
            target_class: Target class index (nếu None, dùng predicted class)
        
        Returns:
            Tuple[np.ndarray, int]: (heatmap [H, W], target_class)
        """
        import cv2
        
        # Preprocess
        input_tensor = self.preprocess(image)
        input_tensor = input_tensor.to(self.device)
        
        # Get target class
        if target_class is None:
            with torch.no_grad():
                outputs = self.model(input_tensor)
                target_class = outputs.argmax(dim=1).item()
        
        # Register hooks
        gradients = None
        activations = None
        
        def forward_hook(module, input, output):
            nonlocal activations
            activations = output

        def backward_hook(module, grad_input, grad_output):
            nonlocal gradients
            gradients = grad_output[0]

        # MobileNetV2: use last feature layer
        target_layer = self.model.features[-1]
        handle_forward = target_layer.register_forward_hook(forward_hook)
        handle_backward = target_layer.register_full_backward_hook(backward_hook)
        
        # Forward pass
        self.model.eval()
        output = self.model(input_tensor)
        
        # Backward pass
        self.model.zero_grad()
        output[0, target_class].backward(retain_graph=True)
        
        # Remove hooks
        handle_forward.remove()
        handle_backward.remove()
        
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
        
        return heatmap, target_class

    def visualize_gradcam(
        self,
        image: Image.Image,
        heatmap: np.ndarray,
        alpha: float = 0.4,
    ) -> Image.Image:
        """
        Overlay heatmap lên ảnh gốc.
        
        Args:
            image: PIL Image gốc
            heatmap: Heatmap từ generate_gradcam [H, W]
            alpha: Transparency của heatmap (0-1)
        
        Returns:
            Image.Image: Ảnh với heatmap overlay
        """
        import cv2
        
        # Resize heatmap về kích thước ảnh gốc
        heatmap_resized = cv2.resize(heatmap, (image.size[0], image.size[1]))
        
        # Apply colormap
        heatmap_colored = cv2.applyColorMap(heatmap_resized, cv2.COLORMAP_JET)
        heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)
        
        # Blend với ảnh gốc
        image_np = np.array(image)
        overlay = cv2.addWeighted(image_np, 1 - alpha, heatmap_colored, alpha, 0)
        
        return Image.fromarray(overlay)


def load_predictor(
    model_path: Path = None,
    classes_path: Path = None,
    use_calibration: bool = False,
    model_type: str = None,
    model_suffix: str = None,
) -> Predictor:
    """
    Factory function để tạo Predictor instance.

    Args:
        model_path: Đường dẫn đến best_model.pt (optional)
        classes_path: Đường dẫn đến classes.json (optional)
        use_calibration: Có dùng temperature scaling không (optional)
        model_type: Loại model (optional)
        model_suffix: Suffix của model (ví dụ: resnet50, efficientnet_b0)

    Returns:
        Predictor instance
    """
    return Predictor(model_path, classes_path, use_calibration, model_type, model_suffix)


def main():
    """CLI test - predict 1 ảnh mẫu."""
    import argparse

    parser = argparse.ArgumentParser(description="Test predict.py với 1 ảnh")
    parser.add_argument("--image", type=str, required=True, help="Đường dẫn đến ảnh test")
    parser.add_argument("--calibrate", action="store_true", help="Dùng temperature scaling calibration")
    parser.add_argument("--gradcam", action="store_true", help="Generate GradCAM heatmap")
    parser.add_argument("--output", type=str, help="Đường dẫn để lưu heatmap (chỉ dùng với --gradcam)")
    parser.add_argument("--model-suffix", type=str, help="Suffix của model (ví dụ: resnet50, efficientnet_b0)")
    args = parser.parse_args()

    # Load predictor
    predictor = load_predictor(use_calibration=args.calibrate, model_suffix=args.model_suffix)

    # Load ảnh
    img_path = Path(args.image)
    if not img_path.exists():
        print(f"Lỗi: Không tìm thấy ảnh tại {img_path}")
        return

    image = Image.open(img_path)

    # Predict
    result = predictor.predict_single(image)

    # Print result
    print("\n=== Kết quả predict ===")
    print(f"Label: {result['label']}")
    print(f"Confidence: {result['confidence']:.4f} ({result['confidence'] * 100:.2f}%)")
    if "temperature" in result:
        print(f"Temperature: {result['temperature']:.4f}")
    print(f"Số classes: {len(result['all_probs'])}")
    print(f"Top 5 probs:")
    sorted_indices = sorted(range(len(result['all_probs'])), key=lambda i: result['all_probs'][i], reverse=True)[:5]
    for idx in sorted_indices:
        print(f"  {predictor.classes[idx]}: {result['all_probs'][idx]:.4f}")

    # GradCAM
    if args.gradcam:
        print("\n=== Generating GradCAM heatmap ===")
        heatmap, target_class = predictor.generate_gradcam(image)
        overlay = predictor.visualize_gradcam(image, heatmap)
        
        # Save
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = img_path.parent / f"{img_path.stem}_gradcam{img_path.suffix}"
        
        overlay.save(output_path)
        print(f"Đã lưu heatmap tại {output_path}")
        print(f"Target class: {predictor.classes[target_class]}")


if __name__ == "__main__":
    main()
