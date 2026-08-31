"""
So sánh 2 model trên cùng ảnh test.

Ví dụ:
    py src/compare_models.py --image "path/to/image.jpg"
    py src/compare_models.py --image "path/to/image.jpg" --gradcam
"""

import argparse
import json
from pathlib import Path

import torch
from PIL import Image

from config import load_config, ml_path
from data_loader import eval_transform
from model import build_model


def load_model_with_suffix(suffix: str = None):
    """
    Load model với suffix (ví dụ: resnet50).

    Nếu suffix=None: load model mặc định (best_model.pt, classes.json)
    Nếu suffix="resnet50": load best_model_resnet50.pt, classes_resnet50.json, model_type_resnet50.json
    """
    cfg = load_config()
    models_dir = ml_path(cfg["paths"]["models_dir"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if suffix is None:
        # Model mặc định (MobileNetV2 cũ)
        model_path = models_dir / "best_model.pt"
        classes_path = models_dir / "classes.json"
        model_type = "mobilenet_v2"  # Mặc định cho model cũ
    else:
        # Model mới với suffix
        model_path = models_dir / f"best_model_{suffix}.pt"
        classes_path = models_dir / f"classes_{suffix}.json"
        model_type_path = models_dir / f"model_type_{suffix}.json"

        if not model_type_path.exists():
            model_type = "mobilenet_v2"  # Fallback
        else:
            with open(model_type_path, encoding="utf-8") as f:
                model_type_data = json.load(f)
                model_type = model_type_data.get("model_type", "mobilenet_v2")

    # Load classes
    with open(classes_path, encoding="utf-8") as f:
        classes = json.load(f)
    num_classes = len(classes)

    # Load model
    model = build_model(num_classes=num_classes, model_type=model_type)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()

    return model, classes, model_type


def predict_single(model, image_tensor, classes, device):
    """Predict cho 1 ảnh và trả về kết quả."""
    image_tensor = image_tensor.unsqueeze(0).to(device)
    with torch.no_grad():
        outputs = model(image_tensor)
        probs = torch.softmax(outputs, dim=1)[0]
        confidence, pred_idx = torch.max(probs, dim=0)

    label = classes[pred_idx.item()]
    confidence = confidence.item()

    # Top-5
    top5_probs, top5_indices = torch.topk(probs, 5)
    top5 = [
        (classes[idx.item()], prob.item())
        for idx, prob in zip(top5_indices, top5_probs)
    ]

    return label, confidence, top5


def main():
    parser = argparse.ArgumentParser(description="So sánh 2 model trên cùng ảnh")
    parser.add_argument("--image", type=str, required=True, help="Đường dẫn đến ảnh test")
    parser.add_argument("--suffix", type=str, default="resnet50", help="Suffix của model mới (mặc định: resnet50)")
    args = parser.parse_args()

    # Load ảnh
    image_path = Path(args.image)
    if not image_path.exists():
        print(f"❌ Không tìm thấy ảnh tại {image_path}")
        return

    image = Image.open(image_path).convert("RGB")
    image_tensor = eval_transform(image)

    print(f"📷 Đang test ảnh: {image_path}")
    print("=" * 60)

    # Load model cũ (MobileNetV2)
    print("🔄 Đang load model cũ (MobileNetV2)...")
    model_old, classes_old, model_type_old = load_model_with_suffix(suffix=None)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"✅ Model cũ: {model_type_old}")

    # Load model mới (ResNet50)
    print(f"🔄 Đang load model mới ({args.suffix.upper()})...")
    model_new, classes_new, model_type_new = load_model_with_suffix(suffix=args.suffix)
    print(f"✅ Model mới: {model_type_new}")

    print("=" * 60)

    # Predict với model cũ
    label_old, conf_old, top5_old = predict_single(model_old, image_tensor, classes_old, device)
    print(f"📊 Model cũ ({model_type_old}):")
    print(f"   Label: {label_old}")
    print(f"   Confidence: {conf_old:.4f} ({conf_old*100:.2f}%)")
    print(f"   Top-5:")
    for cls, prob in top5_old:
        print(f"     {cls}: {prob:.4f} ({prob*100:.2f}%)")

    print("=" * 60)

    # Predict với model mới
    label_new, conf_new, top5_new = predict_single(model_new, image_tensor, classes_new, device)
    print(f"📊 Model mới ({model_type_new}):")
    print(f"   Label: {label_new}")
    print(f"   Confidence: {conf_new:.4f} ({conf_new*100:.2f}%)")
    print(f"   Top-5:")
    for cls, prob in top5_new:
        print(f"     {cls}: {prob:.4f} ({prob*100:.2f}%)")

    print("=" * 60)

    # So sánh
    print("🔍 So sánh:")
    if label_old == label_new:
        print(f"   ✅ Cả 2 model predict giống nhau: {label_old}")
    else:
        print(f"   ❌ Model cũ: {label_old} vs Model mới: {label_new}")

    if conf_old > conf_new:
        print(f"   📈 Model cũ confident hơn: {conf_old:.4f} > {conf_new:.4f}")
    else:
        print(f"   📈 Model mới confident hơn: {conf_new:.4f} > {conf_old:.4f}")


if __name__ == "__main__":
    main()
