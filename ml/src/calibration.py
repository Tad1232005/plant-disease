"""
Temperature Scaling Calibration cho model.

Mục đích:
    - Tìm temperature T tối ưu trên validation set
    - Scale logits bằng T trước khi softmax
    - Confidence sau calibration đáng tin hơn (95% ≈ đúng 95%)

Cách dùng:
    # Tìm temperature tối ưu trên validation set (model mặc định, không hậu tố)
    python ml/src/calibration.py --find-temperature

    # Tìm temperature cho đúng model đã train theo suffix (khuyến nghị dùng cái này)
    python ml/src/calibration.py --find-temperature --model-suffix resnet50_full_data

    # Dùng temperature đã lưu trong predict
    python ml/src/predict.py --image path/to/image.jpg --model-suffix resnet50_full_data --calibrate

Output:
    models/temperature.json               — không dùng model_suffix
    models/temperature_<suffix>.json      — có dùng model_suffix (khuyến nghị)
"""

import json
from pathlib import Path
from typing import List

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from config import load_config, ml_path
from data_loader import PlantDiseaseDataset, eval_transform
from model import build_model


class TemperatureScaler:
    """
    Temperature Scaling để calibrate confidence.

    T > 1: confidence thấp hơn (overconfident model)
    T < 1: confidence cao hơn (underconfident model)
    T = 1: không thay đổi
    """

    def __init__(self):
        self.temperature = 1.0

    def fit(self, logits: np.ndarray, labels: np.ndarray) -> float:
        """
        Tìm temperature tối ưu bằng minimizing NLL trên validation set.

        Args:
            logits: np.ndarray shape [N, C] - raw logits từ model
            labels: np.ndarray shape [N] - ground truth labels

        Returns:
            float: temperature tối ưu
        """
        print("Đang tìm temperature tối ưu...")

        logits_tensor = torch.from_numpy(logits).float()
        labels_tensor = torch.from_numpy(labels).long()

        self.temperature = nn.Parameter(torch.ones(1) * 1.5)
        optimizer = torch.optim.LBFGS([self.temperature], lr=0.001, max_iter=1000)

        criterion = nn.CrossEntropyLoss()

        def eval_loss():
            optimizer.zero_grad()
            loss = criterion(logits_tensor / self.temperature, labels_tensor)
            loss.backward()
            return loss

        optimizer.step(eval_loss)

        temperature = self.temperature.item()
        print(f"Temperature tối ưu: {temperature:.4f}")
        return temperature

    def scale(self, logits: torch.Tensor) -> torch.Tensor:
        """
        Scale logits bằng temperature.

        Args:
            logits: torch.Tensor shape [N, C]

        Returns:
            torch.Tensor shape [N, C] - scaled logits
        """
        return logits / self.temperature


def find_temperature(
    model_path: Path = None,
    classes_path: Path = None,
    temperature_path: Path = None,
    model_type: str = None,
    model_suffix: str = None,
):
    """
    Tìm temperature tối ưu trên validation set và lưu file.

    Args:
        model_path: Đường dẫn đến best_model.pt (bỏ qua nếu dùng model_suffix)
        classes_path: Đường dẫn đến classes.json (bỏ qua nếu dùng model_suffix)
        temperature_path: Đường dẫn để lưu temperature.json (bỏ qua nếu dùng model_suffix)
        model_type: Loại model (mặc định từ config, bỏ qua nếu dùng model_suffix)
        model_suffix: Hậu tố model đã train (vd resnet50_full_data) — tự động load
            đúng best_model_<suffix>.pt / classes_<suffix>.json / model_type_<suffix>.json
            và lưu ra temperature_<suffix>.json, tránh nhầm với model khác.
    """
    cfg = load_config()
    models_dir = ml_path(cfg["paths"]["models_dir"])
    split_dir = ml_path(cfg["paths"]["split_dir"])

    if model_suffix:
        if model_path is None:
            model_path = models_dir / f"best_model_{model_suffix}.pt"
        if classes_path is None:
            classes_path = models_dir / f"classes_{model_suffix}.json"
        if temperature_path is None:
            temperature_path = models_dir / f"temperature_{model_suffix}.json"
        if model_type is None:
            model_type_path = models_dir / f"model_type_{model_suffix}.json"
            if model_type_path.exists():
                with open(model_type_path, encoding="utf-8") as f:
                    model_type = json.load(f)["model_type"]
            else:
                model_type = model_suffix
    else:
        if model_path is None:
            model_path = models_dir / "best_model.pt"
        if classes_path is None:
            classes_path = models_dir / "classes.json"
        if temperature_path is None:
            temperature_path = models_dir / "temperature.json"
        if model_type is None:
            model_type = cfg["train"].get("model_type", "mobilenet_v2")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    print(f"Model path: {model_path}")

    with open(classes_path, encoding="utf-8") as f:
        classes = json.load(f)
    num_classes = len(classes)
    print(f"Đã load {num_classes} classes")
    print(f"Model type: {model_type}")

    print(f"Đang load model từ {model_path}...")
    model = build_model(num_classes=num_classes, model_type=model_type)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()
    print("Đã load model xong")

    val_ds = PlantDiseaseDataset(split_dir / "val", transform=eval_transform)
    batch_size = cfg["train"]["batch_size"]
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)
    print(f"Validation: {len(val_ds):,} ảnh, {len(val_loader):,} batch")

    print("Đang collect logits từ validation set...")
    all_logits = []
    all_labels = []

    with torch.no_grad():
        for images, labels in tqdm(val_loader, desc="Collecting logits", unit="batch"):
            images = images.to(device)
            outputs = model(images)
            all_logits.append(outputs.cpu().numpy())
            all_labels.extend(labels.tolist())

    all_logits = np.concatenate(all_logits, axis=0)
    all_labels = np.array(all_labels)
    print(f"Đã collect {len(all_logits):,} logits")

    scaler = TemperatureScaler()
    temperature = scaler.fit(all_logits, all_labels)

    temperature_data = {
        "temperature": temperature,
        "num_samples": len(all_labels),
        "num_classes": num_classes,
    }

    with open(temperature_path, "w", encoding="utf-8") as f:
        json.dump(temperature_data, f, indent=2)

    print(f"Đã lưu temperature tại {temperature_path}")

    print("\n=== Đánh giá calibration ===")
    evaluate_calibration(all_logits, all_labels, temperature, classes)


def evaluate_calibration(
    logits: np.ndarray,
    labels: np.ndarray,
    temperature: float,
    classes: List[str],
):
    """
    Đánh giá calibration trước và sau temperature scaling.

    Args:
        logits: raw logits từ model
        labels: ground truth labels
        temperature: temperature tối ưu
        classes: danh sách tên class
    """
    from sklearn.metrics import accuracy_score

    probs_before = torch.softmax(torch.from_numpy(logits).float(), dim=1).numpy()
    preds_before = probs_before.argmax(axis=1)
    conf_before = probs_before.max(axis=1)
    acc_before = accuracy_score(labels, preds_before)
    avg_conf_before = conf_before.mean()

    logits_tensor = torch.from_numpy(logits).float()
    probs_after = torch.softmax(logits_tensor / temperature, dim=1).numpy()
    preds_after = probs_after.argmax(axis=1)
    conf_after = probs_after.max(axis=1)
    acc_after = accuracy_score(labels, preds_after)
    avg_conf_after = conf_after.mean()

    print(f"\nTrước calibration (T=1.0):")
    print(f"  Accuracy: {acc_before:.4f} ({acc_before * 100:.2f}%)")
    print(f"  Avg confidence: {avg_conf_before:.4f} ({avg_conf_before * 100:.2f}%)")
    print(f"  Confidence - Accuracy gap: {(avg_conf_before - acc_before):.4f}")

    print(f"\nSau calibration (T={temperature:.4f}):")
    print(f"  Accuracy: {acc_after:.4f} ({acc_after * 100:.2f}%)")
    print(f"  Avg confidence: {avg_conf_after:.4f} ({avg_conf_after * 100:.2f}%)")
    print(f"  Confidence - Accuracy gap: {(avg_conf_after - acc_after):.4f}")

    n_bins = 10
    ece_before = compute_ece(probs_before, preds_before, labels, n_bins)
    ece_after = compute_ece(probs_after, preds_after, labels, n_bins)

    print(f"\nExpected Calibration Error (ECE, {n_bins} bins):")
    print(f"  Trước: {ece_before:.4f}")
    print(f"  Sau: {ece_after:.4f}")
    print(f"  Cải thiện: {(ece_before - ece_after):.4f}")


def compute_ece(probs: np.ndarray, preds: np.ndarray, labels: np.ndarray, n_bins: int = 10) -> float:
    """
    Compute Expected Calibration Error (ECE).

    Args:
        probs: predicted probabilities [N, C]
        preds: predicted labels [N]
        labels: ground truth labels [N]
        n_bins: số bins để chia confidence

    Returns:
        float: ECE score
    """
    confidences = probs.max(axis=1)
    accuracies = (preds == labels).astype(float)

    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
        prop_in_bin = in_bin.mean()

        if prop_in_bin > 0:
            accuracy_in_bin = accuracies[in_bin].mean()
            avg_confidence_in_bin = confidences[in_bin].mean()
            ece += prop_in_bin * abs(avg_confidence_in_bin - accuracy_in_bin)

    return ece


def main():
    """CLI - tìm temperature tối ưu."""
    import argparse

    parser = argparse.ArgumentParser(description="Temperature Scaling Calibration")
    parser.add_argument(
        "--find-temperature",
        action="store_true",
        help="Tìm temperature tối ưu trên validation set",
    )
    parser.add_argument("--model-path", type=str, help="Đường dẫn đến best_model.pt")
    parser.add_argument("--classes-path", type=str, help="Đường dẫn đến classes.json")
    parser.add_argument("--temperature-path", type=str, help="Đường dẫn để lưu temperature.json")
    parser.add_argument(
        "--model-suffix",
        type=str,
        help="Hậu tố model đã train (vd: resnet50_full_data) để tự load đúng "
             "best_model_<suffix>.pt và lưu ra temperature_<suffix>.json",
    )
    args = parser.parse_args()

    if args.find_temperature:
        find_temperature(
            model_path=Path(args.model_path) if args.model_path else None,
            classes_path=Path(args.classes_path) if args.classes_path else None,
            temperature_path=Path(args.temperature_path) if args.temperature_path else None,
            model_suffix=args.model_suffix,
        )
    else:
        print("Sử dụng --find-temperature để tìm temperature tối ưu")


if __name__ == "__main__":
    main()