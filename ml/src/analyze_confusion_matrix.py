"""
Phân tích confusion matrix từ metrics file.

Cách dùng:
    python ml/src/analyze_confusion_matrix --model-suffix efficientnet_b0_f
"""

import argparse
import json
from pathlib import Path


def analyze_confusion_matrix_from_metrics(metrics_path: Path):
    """Phân tích confusion matrix từ metrics file."""
    
    # Load metrics
    with open(metrics_path, encoding="utf-8") as f:
        metrics = json.load(f)
    
    print(f"=== Tổng quan ===")
    print(f"Accuracy: {metrics['accuracy']:.4f} ({metrics['accuracy'] * 100:.2f}%)")
    print(f"Test samples: {metrics['test_samples']}")
    print(f"Macro F1: {metrics['macro_avg']['f1_score']:.4f}")
    print(f"Weighted F1: {metrics['weighted_avg']['f1_score']:.4f}")
    
    per_class = metrics['per_class']
    
    # Tìm class có recall thấp nhất (thường bị nhầm nhiều nhất)
    sorted_by_recall = sorted(per_class, key=lambda x: x['recall'])
    print(f"\n=== Top 5 class có recall thấp nhất (thường bị nhầm nhiều nhất) ===")
    for i, cls in enumerate(sorted_by_recall[:5]):
        print(f"{i+1}. {cls['name']}: Recall={cls['recall']:.4f}, Precision={cls['precision']:.4f}, F1={cls['f1_score']:.4f}, Support={cls['support']}")
    
    # Tìm class có precision thấp nhất (thường nhầm lẫn class khác)
    sorted_by_precision = sorted(per_class, key=lambda x: x['precision'])
    print(f"\n=== Top 5 class có precision thấp nhất (thường nhầm lẫn class khác) ===")
    for i, cls in enumerate(sorted_by_precision[:5]):
        print(f"{i+1}. {cls['name']}: Precision={cls['precision']:.4f}, Recall={cls['recall']:.4f}, F1={cls['f1_score']:.4f}, Support={cls['support']}")
    
    # Tìm class có F1 thấp nhất
    sorted_by_f1 = sorted(per_class, key=lambda x: x['f1_score'])
    print(f"\n=== Top 5 class có F1 thấp nhất ===")
    for i, cls in enumerate(sorted_by_f1[:5]):
        print(f"{i+1}. {cls['name']}: F1={cls['f1_score']:.4f}, Precision={cls['precision']:.4f}, Recall={cls['recall']:.4f}, Support={cls['support']}")


def main():
    parser = argparse.ArgumentParser(description="Phân tích confusion matrix")
    parser.add_argument("--model-suffix", type=str, required=True, help="Suffix của model")
    args = parser.parse_args()
    
    outputs_dir = Path("ml/outputs")
    metrics_path = outputs_dir / f"metrics_{args.model_suffix}.json"
    
    if not metrics_path.exists():
        print(f"Không tìm thấy {metrics_path}")
        return
    
    analyze_confusion_matrix_from_metrics(metrics_path)


if __name__ == "__main__":
    main()
