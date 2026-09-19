"""
Test batch ảnh với 3 model và so sánh kết quả.

Ví dụ:
    py src/test_batch.py --image-dir "D:\QLPM\Ảnh"
    py src/test_batch.py --image-dir "D:\QLPM\Ảnh" --output "results.csv"
"""

import argparse
import csv
from pathlib import Path

import torch
from PIL import Image

from config import load_config, ml_path
from data_loader import eval_transform
from model import build_model


def load_model_with_suffix(suffix: str):
    """Load model với suffix."""
    cfg = load_config()
    models_dir = ml_path(cfg["paths"]["models_dir"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model_path = models_dir / f"best_model_{suffix}.pt"
    classes_path = models_dir / f"classes_{suffix}.json"
    model_type_path = models_dir / f"model_type_{suffix}.json"

    # Load model_type
    if model_type_path.exists():
        import json
        with open(model_type_path, encoding="utf-8") as f:
            model_type_data = json.load(f)
            model_type = model_type_data.get("model_type", "mobilenet_v2")
    else:
        model_type = "mobilenet_v2"

    # Load classes
    import json
    with open(classes_path, encoding="utf-8") as f:
        classes = json.load(f)
    num_classes = len(classes)

    # Load model
    model = build_model(num_classes=num_classes, model_type=model_type)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()

    return model, classes, model_type, device


def predict_single(model, image_tensor, classes, device):
    """Predict cho 1 ảnh."""
    image_tensor = image_tensor.unsqueeze(0).to(device)
    with torch.no_grad():
        outputs = model(image_tensor)
        probs = torch.softmax(outputs, dim=1)[0]
        confidence, pred_idx = torch.max(probs, dim=0)

    label = classes[pred_idx.item()]
    confidence = confidence.item()

    return label, confidence


def main():
    parser = argparse.ArgumentParser(description="Test batch ảnh với 3 model")
    parser.add_argument("--image-dir", type=str, required=True, help="Đường dẫn đến thư mục ảnh")
    parser.add_argument("--output", type=str, default="results.csv", help="File output CSV")
    args = parser.parse_args()

    image_dir = Path(args.image_dir)
    if not image_dir.exists():
        print(f"❌ Không tìm thấy thư mục {image_dir}")
        return

    # Lấy tất cả ảnh
    image_files = [f for f in image_dir.glob("*") if f.suffix.lower() in (".jpg", ".jpeg", ".png")]
    print(f"📷 Tìm thấy {len(image_files)} ảnh")

    # 3 model
    model_suffixes = ["efficientnet_b0_f", "mobilenet_v2_f", "resnet50_f"]
    models = {}

    # Load models
    for suffix in model_suffixes:
        try:
            model, classes, model_type, device = load_model_with_suffix(suffix)
            models[suffix] = {"model": model, "classes": classes, "device": device}
            print(f"✅ Đã load model {suffix} ({model_type})")
        except Exception as e:
            print(f"❌ Không thể load model {suffix}: {e}")

    # Test từng ảnh
    results = []
    for img_path in image_files:
        print(f"\n🔄 Đang test {img_path.name}...")
        image = Image.open(img_path).convert("RGB")
        image_tensor = eval_transform(image)

        row = {"image": img_path.name}
        for suffix in model_suffixes:
            if suffix in models:
                model_data = models[suffix]
                label, confidence = predict_single(
                    model_data["model"],
                    image_tensor,
                    model_data["classes"],
                    model_data["device"]
                )
                row[f"{suffix}_label"] = label
                row[f"{suffix}_confidence"] = f"{confidence:.4f}"
            else:
                row[f"{suffix}_label"] = "N/A"
                row[f"{suffix}_confidence"] = "N/A"

        results.append(row)

    # Xuất CSV
    output_path = Path(args.output)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["image"] + [f"{s}_label" for s in model_suffixes] + [f"{s}_confidence" for s in model_suffixes]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Đã lưu kết quả vào {output_path}")

    # Hiển thị bảng kết quả
    print("\n📊 Kết quả:")
    print("-" * 120)
    header = f"{'Image':<30} | {'EfficientNet':<30} | {'MobileNet':<30} | {'ResNet50':<30}"
    print(header)
    print("-" * 120)
    for row in results:
        eff = f"{row['efficientnet_b0_f_label']} ({row['efficientnet_b0_f_confidence']})"
        mob = f"{row['mobilenet_v2_f_label']} ({row['mobilenet_v2_f_confidence']})"
        res = f"{row['resnet50_f_label']} ({row['resnet50_f_confidence']})"
        print(f"{row['image']:<30} | {eff:<30} | {mob:<30} | {res:<30}")


if __name__ == "__main__":
    main()
