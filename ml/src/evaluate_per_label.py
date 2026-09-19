import json
import argparse
from pathlib import Path
from collections import defaultdict

import torch
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report, confusion_matrix
import pandas as pd
import numpy as np

from config import load_config as config_loader, ml_path
from data_loader import PlantDiseaseDataset, eval_transform
from model import build_model


def evaluate_per_label(model, dataloader, device, class_names):
    """Danh gia model tren tung label rieng biet"""
    model.eval()
    
    all_preds = []
    all_labels = []
    label_correct = defaultdict(int)
    label_total = defaultdict(int)
    
    from tqdm import tqdm
    
    with torch.no_grad():
        for images, labels in tqdm(dataloader, desc="Evaluating"):
            images, labels = images.to(device), labels.to(device)
            
            outputs = model(images)
            _, predicted = torch.max(outputs, 1)
            
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            
            # Dem dung/sai tung class
            for pred, true_label in zip(predicted, labels):
                label_total[true_label.item()] += 1
                if pred == true_label:
                    label_correct[true_label.item()] += 1
    
    # === Per-Label Metrics ===
    per_label_metrics = {}
    for label_id in range(len(class_names)):
        if label_total[label_id] > 0:
            acc = label_correct[label_id] / label_total[label_id]
            per_label_metrics[class_names[label_id]] = {
                "accuracy": float(acc),
                "correct": int(label_correct[label_id]),
                "total": int(label_total[label_id])
            }
        else:
            per_label_metrics[class_names[label_id]] = {
                "accuracy": 0.0,
                "correct": 0,
                "total": 0
            }
    
    # === Overall Metrics ===
    all_preds = np.array(all_preds)
    all_labels = np.array(all_labels)
    overall_acc = (all_preds == all_labels).mean()
    
    report = classification_report(
        all_labels, all_preds,
        target_names=class_names,
        output_dict=True,
        zero_division=0
    )
    
    cm = confusion_matrix(all_labels, all_preds, labels=range(len(class_names)))
    
    return {
        "per_label": per_label_metrics,
        "overall": {
            "accuracy": float(overall_acc),
            "macro_avg_precision": float(report["macro avg"]["precision"]),
            "macro_avg_recall": float(report["macro avg"]["recall"]),
            "macro_avg_f1": float(report["macro avg"]["f1-score"]),
            "weighted_avg_f1": float(report["weighted avg"]["f1-score"])
        },
        "classification_report": report,
        "confusion_matrix": cm.tolist()
    }


def save_results(results, output_dir, model_suffix):
    """Lưu kết quả đánh giá vào file"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Luu JSON
    json_path = output_dir / f"eval_per_label_{model_suffix}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"[OK] Luu ket qua JSON: {json_path}")
    
    # Luu CSV per-label
    df_per_label = pd.DataFrame(results["per_label"]).T
    csv_path = output_dir / f"per_label_{model_suffix}.csv"
    df_per_label.to_csv(csv_path, encoding="utf-8")
    print(f"[OK] Luu per-label CSV: {csv_path}")
    
    return json_path, csv_path


def print_results(results, class_names):
    """In ket qua chi tiet ra console"""
    print("\n" + "="*90)
    print("DANH GIA RIENG TUNG LABEL (PER-CLASS ACCURACY)")
    print("="*90)
    
    per_label = results["per_label"]
    
    # Sắp xếp theo accuracy giảm dần
    sorted_labels = sorted(
        per_label.items(),
        key=lambda x: x[1]["accuracy"],
        reverse=True
    )
    
    print(f"{'#':<4}{'Class':<50}{'Accuracy':<15}{'Samples':<15}")
    print("-" * 90)
    
    for idx, (class_name, metrics) in enumerate(sorted_labels, 1):
        acc = metrics["accuracy"]
        total = metrics["total"]
        correct = metrics["correct"]
        acc_pct = f"{acc*100:.2f}%"
        sample_info = f"{correct}/{total}"
        print(f"{idx:<4}{class_name:<50}{acc_pct:<15}{sample_info:<15}")
    
    # Overall metrics
    overall = results["overall"]
    print("\n" + "="*90)
    print("TONG HOP")
    print("="*90)
    print(f"Overall Accuracy:        {overall['accuracy']*100:.2f}%")
    print(f"Macro Avg Precision:     {overall['macro_avg_precision']:.4f}")
    print(f"Macro Avg Recall:        {overall['macro_avg_recall']:.4f}")
    print(f"Macro Avg F1-Score:      {overall['macro_avg_f1']:.4f}")
    print(f"Weighted Avg F1-Score:   {overall['weighted_avg_f1']:.4f}")
    print("="*90 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Đánh giá model trên từng label riêng biệt"
    )
    parser.add_argument(
        "--model-suffix",
        type=str,
        default="mobilenet_v2_y",
        help="Suffix của model (ví dụ: resnet50_f, mobilenet_v2_y)"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/config.yaml",
        help="Đường dẫn config file"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size cho evaluation"
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Device: cuda hoặc cpu (mặc định: auto-detect)"
    )
    
    args = parser.parse_args()
    
    try:
        # === Load Config ===
        config = config_loader()
        class_names = config["target_classes"]
        num_classes = len(class_names)
        
        print(f"[*] Classes: {num_classes}")
        print(f"[*] Model Suffix: {args.model_suffix}")
        
        # === Device ===
        if args.device:
            device = torch.device(args.device)
        else:
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[*] Device: {device}")
        
        # === Load Model ===
        models_dir = ml_path(config["paths"]["models_dir"])
        model_path = models_dir / f"best_model_{args.model_suffix}.pt"
        
        if not model_path.exists():
            print(f"\n[ERROR] Model khong tim thay: {model_path}")
            print(f"[*] Cac file trong {models_dir}:")
            if models_dir.exists():
                for f in models_dir.glob("*.pt"):
                    print(f"   - {f.name}")
            else:
                print(f"   Thu muc {models_dir} khong ton tai!")
            return
        
        model = build_model(
            model_type=config["train"]["model_type"],
            num_classes=num_classes,
            pretrained=False
        )
        checkpoint = torch.load(model_path, map_location=device)
        model.load_state_dict(checkpoint)
        model = model.to(device)
        print(f"[OK] Model tai tu: {model_path}")
        
        # === Load Test Dataset ===
        split_dir = ml_path(config["paths"]["split_dir"])
        test_dir = split_dir / "test"
        
        if not test_dir.exists():
            print(f"\n[ERROR] Test dataset khong tim thay: {test_dir}")
            return
        
        test_dataset = PlantDiseaseDataset(
            data_dir=test_dir,
            transform=eval_transform
        )
        
        if len(test_dataset) == 0:
            print(f"\n[ERROR] Test dataset trong: {test_dir}")
            return
        
        test_loader = DataLoader(
            test_dataset,
            batch_size=args.batch_size,
            shuffle=False,
            num_workers=config["train"]["num_workers"]
        )
        
        print(f"[OK] Test dataset: {len(test_dataset)} anh")
        
        # === Evaluate ===
        print("\n[*] Dang danh gia...")
        results = evaluate_per_label(model, test_loader, device, class_names)
        
        # === Print & Save ===
        print_results(results, class_names)
        
        outputs_dir = ml_path(config["paths"]["outputs_dir"])
        save_results(results, outputs_dir, args.model_suffix)
        
        print("[OK] Hoan thanh!")
        
    except Exception as e:
        print(f"\n[ERROR] Loi: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())