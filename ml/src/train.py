"""
Train baseline model.

Cách dùng:
    python ml/src/train.py

Yêu cầu cấu trúc dữ liệu đã chia sẵn train/val (xem README.md phần "Chia tập dữ liệu"):
    ml/data/split/train/<class_name>/*.jpg
    ml/data/split/val/<class_name>/*.jpg
"""

import json
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from dataset import PlantDiseaseDataset, train_transform, eval_transform
from model import build_model

# ===== Config =====
DATA_DIR = Path("ml/data/split")
OUTPUT_DIR = Path("ml/models")
BATCH_SIZE = 32
EPOCHS = 15
LR = 1e-4
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    train_ds = PlantDiseaseDataset(DATA_DIR / "train", transform=train_transform)
    val_ds = PlantDiseaseDataset(DATA_DIR / "val", transform=eval_transform)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=2)

    num_classes = len(train_ds.classes)
    print(f"Số lớp: {num_classes} -> {train_ds.classes}")

    model = build_model(num_classes=num_classes).to(DEVICE)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)

    best_val_acc = 0.0

    for epoch in range(1, EPOCHS + 1):
        model.train()
        train_loss = 0.0
        for images, labels in tqdm(train_loader, desc=f"Epoch {epoch}/{EPOCHS} [train]"):
            images, labels = images.to(DEVICE), labels.to(DEVICE)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * images.size(0)

        train_loss /= len(train_ds)

        # ----- validation -----
        model.eval()
        correct, total = 0, 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(DEVICE), labels.to(DEVICE)
                outputs = model(images)
                preds = outputs.argmax(dim=1)
                correct += (preds == labels).sum().item()
                total += labels.size(0)

        val_acc = correct / total
        print(f"Epoch {epoch}: train_loss={train_loss:.4f}  val_acc={val_acc:.4f}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), OUTPUT_DIR / "best_model.pt")
            print(f"  -> Đã lưu model tốt nhất (val_acc={val_acc:.4f})")

    # Lưu danh sách tên lớp để backend dùng khi load model + map index -> tên bệnh
    with open(OUTPUT_DIR / "classes.json", "w", encoding="utf-8") as f:
        json.dump(train_ds.classes, f, ensure_ascii=False, indent=2)

    print(f"\nHoàn tất train. Best val_acc = {best_val_acc:.4f}")
    print(f"Model lưu tại: {OUTPUT_DIR / 'best_model.pt'}")


if __name__ == "__main__":
    main()
