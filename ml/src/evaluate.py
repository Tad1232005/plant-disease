"""
Đánh giá model đã train trên tập test: accuracy, precision/recall/f1 theo lớp, confusion matrix.

Cách dùng:
    python ml/src/evaluate.py
"""

import json
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

from dataset import PlantDiseaseDataset, eval_transform
from model import build_model

DATA_DIR = Path("ml/data/split/test")
MODEL_PATH = Path("ml/models/best_model.pt")
CLASSES_PATH = Path("ml/models/classes.json")
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def main():
    with open(CLASSES_PATH, encoding="utf-8") as f:
        classes = json.load(f)

    test_ds = PlantDiseaseDataset(DATA_DIR, transform=eval_transform)
    test_loader = DataLoader(test_ds, batch_size=32, shuffle=False)

    model = build_model(num_classes=len(classes))
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.to(DEVICE)
    model.eval()

    all_preds, all_labels = [], []
    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(DEVICE)
            outputs = model(images)
            preds = outputs.argmax(dim=1).cpu()
            all_preds.extend(preds.tolist())
            all_labels.extend(labels.tolist())

    print("\n=== Classification Report ===")
    print(classification_report(all_labels, all_preds, target_names=classes))

    cm = confusion_matrix(all_labels, all_preds)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt="d", xticklabels=classes, yticklabels=classes, cmap="Blues")
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title("Confusion Matrix")
    plt.tight_layout()
    plt.savefig("ml/models/confusion_matrix.png")
    print("\nĐã lưu confusion matrix tại ml/models/confusion_matrix.png")


if __name__ == "__main__":
    main()
