"""
Đánh giá model trên tập test (đọc ảnh từ data/split/test/).

Cách dùng:
    python ml/src/evaluate.py
    # hoặc: cd ml && python src/evaluate.py

Output:
    outputs/metrics.json              — accuracy + bảng per-class (push GitHub được)
    outputs/figures/confusion_matrix.png
    outputs/figures/confusion_matrix_errors.png
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import torch
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from torch.utils.data import DataLoader
from tqdm import tqdm

from config import load_config, ml_path
from data_loader import PlantDiseaseDataset, eval_transform
from model import build_model


def class_codes(n: int) -> list[str]:
    return [f"C{i + 1:02d}" for i in range(n)]


def save_metrics(
    outputs_dir: Path,
    classes: list[str],
    accuracy: float,
    report: dict,
) -> Path:
    codes = class_codes(len(classes))
    per_class = []
    for code, name in zip(codes, classes):
        stats = report[name]
        per_class.append(
            {
                "code": code,
                "name": name,
                "precision": stats["precision"],
                "recall": stats["recall"],
                "f1_score": stats["f1-score"],
                "support": int(stats["support"]),
            }
        )

    metrics = {
        "accuracy": accuracy,
        "test_samples": int(report["weighted avg"]["support"]),
        "macro_avg": {
            "precision": report["macro avg"]["precision"],
            "recall": report["macro avg"]["recall"],
            "f1_score": report["macro avg"]["f1-score"],
        },
        "weighted_avg": {
            "precision": report["weighted avg"]["precision"],
            "recall": report["weighted avg"]["recall"],
            "f1_score": report["weighted avg"]["f1-score"],
        },
        "per_class": per_class,
    }

    path = outputs_dir / "metrics.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    return path


def plot_confusion_matrix(
    cm: np.ndarray,
    codes: list[str],
    figures_dir: Path,
    accuracy: float,
) -> tuple[Path, Path]:
    figures_dir.mkdir(parents=True, exist_ok=True)

    # Ma trận đầy đủ — màu theo số lượng, không ghi số (38 class dễ nhìn hơn)
    fig, ax = plt.subplots(figsize=(14, 12))
    sns.heatmap(
        cm,
        annot=False,
        cmap="Blues",
        xticklabels=codes,
        yticklabels=codes,
        cbar_kws={"label": "Số ảnh"},
        ax=ax,
    )
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(f"Confusion Matrix (Test accuracy: {accuracy * 100:.2f}%)")
    plt.xticks(rotation=90, fontsize=8)
    plt.yticks(rotation=0, fontsize=8)
    plt.tight_layout()

    full_path = figures_dir / "confusion_matrix.png"
    fig.savefig(full_path, dpi=150)
    plt.close(fig)

    # Chỉ hiện ô predict sai — ít ô, ghi số rõ ràng
    errors = cm.copy()
    np.fill_diagonal(errors, 0)
    fig, ax = plt.subplots(figsize=(14, 12))
    sns.heatmap(
        errors,
        annot=True,
        fmt="d",
        cmap="Reds",
        xticklabels=codes,
        yticklabels=codes,
        cbar_kws={"label": "Số ảnh predict sai"},
        ax=ax,
        linewidths=0.5,
        linecolor="white",
    )
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Misclassifications only (off-diagonal)")
    plt.xticks(rotation=90, fontsize=8)
    plt.yticks(rotation=0, fontsize=8)
    plt.tight_layout()

    errors_path = figures_dir / "confusion_matrix_errors.png"
    fig.savefig(errors_path, dpi=150)
    plt.close(fig)

    return full_path, errors_path


def main():
    cfg = load_config()
    split_dir = ml_path(cfg["paths"]["split_dir"])
    models_dir = ml_path(cfg["paths"]["models_dir"])
    outputs_dir = ml_path(cfg["paths"]["outputs_dir"])
    figures_dir = outputs_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    model_path = models_dir / "best_model.pt"
    classes_path = models_dir / "classes.json"
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    with open(classes_path, encoding="utf-8") as f:
        classes = json.load(f)

    test_ds = PlantDiseaseDataset(split_dir / "test", transform=eval_transform)
    batch_size = cfg["train"]["batch_size"]
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False)
    print(f"Test: {len(test_ds):,} ảnh, {len(test_loader):,} batch (batch_size={batch_size})")

    print("Đang load model...")
    model = build_model(num_classes=len(classes))
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    model.eval()

    all_preds, all_labels = [], []
    with torch.no_grad():
        for images, labels in tqdm(test_loader, desc="Evaluating", unit="batch"):
            images = images.to(device)
            outputs = model(images)
            preds = outputs.argmax(dim=1).cpu()
            all_preds.extend(preds.tolist())
            all_labels.extend(labels.tolist())

    accuracy = accuracy_score(all_labels, all_preds)
    report = classification_report(
        all_labels, all_preds, target_names=classes, output_dict=True
    )

    print(f"\n=== Test Accuracy: {accuracy:.4f} ({accuracy * 100:.2f}%) ===")
    print("\n=== Classification Report ===")
    print(classification_report(all_labels, all_preds, target_names=classes))

    metrics_path = save_metrics(outputs_dir, classes, accuracy, report)
    print(f"\nĐã lưu metrics tại {metrics_path}")

    cm = confusion_matrix(all_labels, all_preds)
    codes = class_codes(len(classes))
    print("Đang vẽ confusion matrix...")
    full_path, errors_path = plot_confusion_matrix(cm, codes, figures_dir, accuracy)
    print(f"Đã lưu confusion matrix tại {full_path}")
    print(f"Đã lưu ma trận lỗi tại {errors_path}")


if __name__ == "__main__":
    main()
