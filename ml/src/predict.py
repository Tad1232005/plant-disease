"""
Module inference dùng chung cho ML và backend.

Chức năng:
    - Load model + classes từ file
    - Preprocess ảnh (PIL → tensor)
    - Predict: trả label + confidence + all_probs

Cách dùng:
    from predict import load_predictor
    predictor = load_predictor()
    result = predictor.predict_single(pil_image)
    # result = {"label": "Tomato___healthy", "confidence": 0.9876, "all_probs": [...]}

Test CLI:
    python ml/src/predict.py --image path/to/image.jpg
"""

import json
from pathlib import Path
from typing import Dict, List

import torch
from PIL import Image

from config import load_config, ml_path
from data_loader import eval_transform
from model import build_model


class Predictor:
    """
    Wrapper cho model inference.
    Load model 1 lần, dùng nhiều lần predict.
    """

    def __init__(self, model_path: Path = None, classes_path: Path = None):
        """
        Args:
            model_path: Đường dẫn đến best_model.pt (mặc định từ config)
            classes_path: Đường dẫn đến classes.json (mặc định từ config)
        """
        cfg = load_config()
        models_dir = ml_path(cfg["paths"]["models_dir"])

        if model_path is None:
            model_path = models_dir / "best_model.pt"
        if classes_path is None:
            classes_path = models_dir / "classes.json"

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Device: {self.device}")

        # Load classes
        with open(classes_path, encoding="utf-8") as f:
            self.classes = json.load(f)
        self.num_classes = len(self.classes)
        print(f"Đã load {self.num_classes} classes")

        # Load model
        print(f"Đang load model từ {model_path}...")
        self.model = build_model(num_classes=self.num_classes)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()
        print("Đã load model xong")

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
        """
        # Preprocess
        input_tensor = self.preprocess(image)
        input_tensor = input_tensor.to(self.device)

        # Inference
        with torch.no_grad():
            outputs = self.model(input_tensor)  # [1, num_classes]
            probs = torch.softmax(outputs, dim=1)[0]  # [num_classes]
            probs_np = probs.cpu().numpy()

        # Get prediction
        pred_idx = int(probs.argmax().item())
        confidence = float(probs[pred_idx].item())
        label = self.classes[pred_idx]
        all_probs = probs_np.tolist()

        return {
            "label": label,
            "confidence": confidence,
            "all_probs": all_probs,
        }


def load_predictor(model_path: Path = None, classes_path: Path = None) -> Predictor:
    """
    Factory function để tạo Predictor instance.

    Args:
        model_path: Đường dẫn đến best_model.pt (optional)
        classes_path: Đường dẫn đến classes.json (optional)

    Returns:
        Predictor instance
    """
    return Predictor(model_path, classes_path)


def main():
    """CLI test - predict 1 ảnh mẫu."""
    import argparse

    parser = argparse.ArgumentParser(description="Test predict.py với 1 ảnh")
    parser.add_argument("--image", type=str, required=True, help="Đường dẫn đến ảnh test")
    args = parser.parse_args()

    # Load predictor
    predictor = load_predictor()

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
    print(f"Số classes: {len(result['all_probs'])}")
    print(f"Top 5 probs:")
    sorted_indices = sorted(range(len(result['all_probs'])), key=lambda i: result['all_probs'][i], reverse=True)[:5]
    for idx in sorted_indices:
        print(f"  {predictor.classes[idx]}: {result['all_probs'][idx]:.4f}")


if __name__ == "__main__":
    main()
