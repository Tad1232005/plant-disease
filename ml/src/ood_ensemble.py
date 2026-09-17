"""
Script test OOD detection với ensemble disagreement.

Chạy cả 3 model (ResNet50, EfficientNet, MobileNetV2) trên cùng 1 ảnh,
tính độ bất đồng giữa các model để detect OOD.

Cách dùng:
    python ml/src/ood_ensemble.py --image path/to/image.jpg
    python ml/src/ood_ensemble.py --image path/to/image.jpg --model-suffix resnet50_f
"""

import argparse
import json
from pathlib import Path

import torch
from PIL import Image

from config import load_config, ml_path
from data_loader import eval_transform
from model import build_model
from ood_scoring import compute_all_scores

# 3 backbone cố định để tính ensemble disagreement
DEFAULT_SUFFIXES = {
    "resnet50": "resnet50_f",
    "efficientnet_b0": "efficientnet_b0_f",
    "mobilenet_v2": "mobilenet_v2_f",
}


def load_all_models(models_dir: Path, device):
    """Load cả 3 backbone để tính ensemble disagreement."""
    models = {}
    for backbone, suffix in DEFAULT_SUFFIXES.items():
        model_path = models_dir / f"best_model_{suffix}.pt"
        classes_path = models_dir / f"classes_{suffix}.json"
        model_type_path = models_dir / f"model_type_{suffix}.json"

        if not model_path.exists():
            print(f"  [BỎ QUA] Không tìm thấy {model_path}")
            continue

        with open(classes_path, encoding="utf-8") as f:
            classes = json.load(f)
        with open(model_type_path, encoding="utf-8") as f:
            model_type = json.load(f)["model_type"]

        model = build_model(num_classes=len(classes), model_type=model_type)
        model.load_state_dict(torch.load(model_path, map_location=device))
        model.to(device)
        model.eval()
        models[backbone] = {"model": model, "classes": classes, "model_type": model_type}
        print(f"  [OK] Đã load {backbone} ({suffix})")

    return models


def predict_ensemble(image_path: Path, models: dict, device, primary_backbone: str = "resnet50"):
    """Predict với cả 3 model và tính ensemble disagreement."""
    # Load và preprocess ảnh
    image = Image.open(image_path).convert("RGB")
    input_tensor = eval_transform(image).unsqueeze(0).to(device)

    # Chạy qua cả 3 model
    results = {}
    logits_list = []
    
    with torch.no_grad():
        for backbone, model_data in models.items():
            model = model_data["model"]
            classes = model_data["classes"]
            
            logits = model(input_tensor)
            logits_list.append(logits)
            
            probs = torch.softmax(logits, dim=1)[0]
            pred_idx = int(probs.argmax().item())
            confidence = float(probs[pred_idx].item())
            label = classes[pred_idx]
            
            results[backbone] = {
                "label": label,
                "confidence": confidence,
                "all_probs": probs.cpu().numpy().tolist(),
            }

    # Tính ensemble disagreement
    if len(logits_list) >= 2:
        primary_logits = logits_list[0]  # Dùng model đầu tiên làm primary
        other_logits = logits_list[1:]
        
        ood_scores = compute_all_scores(primary_logits, ensemble_logits=other_logits)
        ensemble_disagreement = float(ood_scores["ensemble_disagreement"].item())
    else:
        ensemble_disagreement = None

    return results, ensemble_disagreement


def main():
    parser = argparse.ArgumentParser(description="Test OOD detection với ensemble")
    parser.add_argument("--image", type=str, required=True, help="Đường dẫn đến ảnh test")
    parser.add_argument("--primary-backbone", type=str, default="resnet50",
                        choices=list(DEFAULT_SUFFIXES.keys()),
                        help="Backbone chính")
    args = parser.parse_args()

    cfg = load_config()
    models_dir = ml_path(cfg["paths"]["models_dir"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print("=" * 70)
    print("OOD DETECTION WITH ENSEMBLE DISAGREEMENT")
    print("=" * 70)
    print(f"\nDevice: {device}")
    print(f"Image: {args.image}\n")

    print("Đang load 3 model...")
    models = load_all_models(models_dir, device)
    
    if len(models) < 2:
        print("\nCảnh báo: chỉ có 1 model, không tính được ensemble_disagreement.")
        return

    img_path = Path(args.image)
    if not img_path.exists():
        print(f"Lỗi: Không tìm thấy ảnh tại {img_path}")
        return

    print(f"\nĐang predict với ensemble...")
    results, ensemble_disagreement = predict_ensemble(img_path, models, device, args.primary_backbone)

    # In kết quả từng model
    print(f"\n{'=' * 70}")
    print("KẾT QUẢ TỪNG MODEL")
    print(f"{'=' * 70}")
    for backbone, result in results.items():
        print(f"\n{backbone.upper()}:")
        print(f"  Label: {result['label']}")
        print(f"  Confidence: {result['confidence']:.4f} ({result['confidence'] * 100:.2f}%)")

    # In ensemble disagreement
    if ensemble_disagreement is not None:
        print(f"\n{'=' * 70}")
        print("ENSEMBLE DISAGREEMENT")
        print(f"{'=' * 70}")
        print(f"Disagreement score: {ensemble_disagreement:.4f}")
        print(f"\nGiải thích:")
        print(f"  - Score thấp (< 0.1): Các model đồng thuận cao -> khả năng ID cao")
        print(f"  - Score trung bình (0.1 - 0.5): Các model có sự khác biệt -> cần kiểm tra")
        print(f"  - Score cao (> 0.5): Các model 'cãi nhau' nhiều -> khả năng OOD cao")

        # Kiểm tra xem các model có đồng thuận về label không
        labels = [r["label"] for r in results.values()]
        unique_labels = set(labels)
        if len(unique_labels) == 1:
            print(f"\n✅ Tất cả model đồng thuận: {labels[0]}")
        else:
            print(f"\n⚠️  Các model KHÔNG đồng thuận:")
            for label in unique_labels:
                count = labels.count(label)
                print(f"  - {label}: {count}/{len(labels)} model")


if __name__ == "__main__":
    main()
