"""
Bước 3 — Train model từ ảnh đã export trong data/split/.

Luồng:
    split/train/ + split/val/  →  train loop  →  models/best_model.pt
                                              →  models/classes.json

Lưu ý:
    - Chỉ dùng train/ và val/ — KHÔNG đụng test/ (test dành cho evaluate.py).
    - best_model.pt = epoch có val_acc cao nhất, không phải epoch cuối.
    - classes.json lưu thứ tự tên class khớp index output của model (backend cần file này).

Cách dùng:
    python ml/src/train.py
    # hoặc: cd ml && python src/train.py
"""

import json

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from config import load_config, ml_path
from data_loader import PlantDiseaseDataset, eval_transform, train_transform
from model import build_model


def main():
    cfg = load_config()
    train_cfg = cfg["train"]
    split_dir = ml_path(cfg["paths"]["split_dir"])
    output_dir = ml_path(cfg["paths"]["models_dir"])

    output_dir.mkdir(parents=True, exist_ok=True)

    # train: có augment (flip, rotate, ...) | val: chỉ resize + normalize
    train_ds = PlantDiseaseDataset(split_dir / "train", transform=train_transform)
    val_ds = PlantDiseaseDataset(split_dir / "val", transform=eval_transform)

    train_loader = DataLoader(
        train_ds,
        batch_size=train_cfg["batch_size"],
        shuffle=True,  # xáo batch mỗi epoch
        num_workers=train_cfg["num_workers"],
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=train_cfg["batch_size"],
        shuffle=False,
        num_workers=train_cfg["num_workers"],
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # Số class = số folder trong split/train/ (vd. 38 class PlantVillage)
    num_classes = len(train_ds.classes)
    print(f"Số lớp: {num_classes} -> {train_ds.classes}")

    # MobileNetV2 pretrain ImageNet, thay classifier cuối → num_classes output
    model = build_model(num_classes=num_classes).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=train_cfg["lr"])

    best_val_acc = 0.0

    for epoch in range(1, train_cfg["epochs"] + 1):
        # ----- TRAIN -----
        model.train()
        train_loss = 0.0
        for images, labels in tqdm(
            train_loader, desc=f"Epoch {epoch}/{train_cfg['epochs']} [train]"
        ):
            images, labels = images.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(images)  # shape: [batch, num_classes]
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * images.size(0)

        train_loss /= len(train_ds)

        # ----- VALIDATION (chọn best model, không cập nhật weight) -----
        model.eval()
        correct, total = 0, 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                preds = outputs.argmax(dim=1)  # class có logit cao nhất
                correct += (preds == labels).sum().item()
                total += labels.size(0)

        val_acc = correct / total
        print(f"Epoch {epoch}: train_loss={train_loss:.4f}  val_acc={val_acc:.4f}")

        # Lưu checkpoint tốt nhất theo val — tránh overfit epoch cuối
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), output_dir / "best_model.pt")
            print(f"  -> Đã lưu model tốt nhất (val_acc={val_acc:.4f})")

    # Map index → tên bệnh cho backend (thứ tự phải khớp train_ds.classes)
    with open(output_dir / "classes.json", "w", encoding="utf-8") as f:
        json.dump(train_ds.classes, f, ensure_ascii=False, indent=2)

    print(f"\nHoàn tất train. Best val_acc = {best_val_acc:.4f}")
    print(f"Model lưu tại: {output_dir / 'best_model.pt'}")


if __name__ == "__main__":
    main()
