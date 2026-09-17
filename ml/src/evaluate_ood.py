"""
Benchmark 4 phương pháp OOD detection: MSP, Entropy, Energy, Ensemble disagreement.

Luồng:
    - ID data: data/split/test/ (ảnh lá cây, 38 lớp đã biết)
    - OOD data: data/ood_test/ (ảnh KHÔNG phải lá cây trong 38 lớp — tự chuẩn bị)
        Cấu trúc: chỉ cần 1 thư mục phẳng chứa ảnh, không cần chia theo lớp:
            data/ood_test/*.jpg

    Nếu CHƯA có data/ood_test/, script vẫn chạy được — chỉ in phân bố score
    trên ID để bạn hình dung, KHÔNG tính được AUROC/FPR95 (cần cả ID và OOD
    mới tính được, vì đây là bài toán phân loại nhị phân ID vs OOD).

Cách dùng:
    # Chỉ xem phân bố trên ID (chưa có OOD data)
    python ml/src/evaluate_ood.py

    # Đầy đủ AUROC/FPR95 khi đã có OOD data
    python ml/src/evaluate_ood.py --ood-dir data/ood_test

    # Giới hạn số ảnh ID để chạy nhanh hơn (mặc định dùng hết test set)
    python ml/src/evaluate_ood.py --ood-dir data/ood_test --max-id-images 1000

    # Chốt ngưỡng production theo percentile trên ID (lưu outputs/ood_threshold.json)
    python ml/src/evaluate_ood.py --ood-dir data/ood_test/near_ood --ood-method ensemble_disagreement --threshold-percentile 95

    # Calibrate ngưỡng theo tier (basic=EffNet đơn, standard=+MobileNet, advanced=+ResNet50)
    # Primary luôn là EfficientNet-B0; mỗi lần chạy chỉ cập nhật ngưỡng của tier đó
    python ml/src/evaluate_ood.py --tier standard --ood-dir data/ood_test/near_ood --max-id-images 2000
"""

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from sklearn.metrics import roc_auc_score
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

from config import load_config, ml_path
from data_loader import PlantDiseaseDataset, eval_transform
from model import build_model
from ood_scoring import HIGH_CONF_MSP, LOW_CONF_MSP, TIER_MODELS, compute_all_scores

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}

# 3 backbone cố định để tính ensemble disagreement — khớp với suffix bạn đã train
DEFAULT_SUFFIXES = {
    "resnet50": "resnet50_f",
    "efficientnet_b0": "efficientnet_b0_f",
    "mobilenet_v2": "mobilenet_v2_f",
}

# Hướng score của từng phương pháp: True = score càng CAO càng khả nghi ID
# (dùng chung cho compute_fpr_at_tpr và compute_percentile_thresholds)
METHOD_DIRECTION = {
    "msp": True,                     # MSP cao -> ID
    "entropy": False,                # Entropy cao -> OOD
    "energy": False,                 # Energy cao (ít âm) -> OOD
    "ensemble_disagreement": False,  # Disagreement cao -> OOD
}


class FlatImageDataset(Dataset):
    """Đọc toàn bộ ảnh phẳng trong 1 thư mục (dùng cho OOD test set, không cần nhãn)."""

    def __init__(self, image_dir: Path, transform):
        self.paths = [p for p in Path(image_dir).glob("*") if p.suffix.lower() in IMAGE_SUFFIXES]
        self.transform = transform

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, idx):
        image = Image.open(self.paths[idx]).convert("RGB")
        return self.transform(image), 0  # nhãn giả, không dùng tới


def load_all_models(models_dir: Path, device, suffixes: dict = None):
    """Load các backbone theo suffix map (mặc định: đủ 3 model — tier advanced)."""
    if suffixes is None:
        suffixes = DEFAULT_SUFFIXES
    models = {}
    for backbone, suffix in suffixes.items():
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
        models[backbone] = model
        print(f"  [OK] Đã load {backbone} ({suffix})")

    return models


def collect_scores(loader, models: dict, primary_backbone: str, device, desc: str,
                   confidence_temperature: float = None):
    """Chạy toàn bộ ảnh qua các model, tính đủ các loại score."""
    all_scores = {"msp": [], "entropy": [], "energy": [], "ensemble_disagreement": []}

    other_backbones = [b for b in models if b != primary_backbone]

    with torch.no_grad():
        for images, _ in tqdm(loader, desc=desc):
            images = images.to(device)

            primary_logits = models[primary_backbone](images)
            other_logits = [models[b](images) for b in other_backbones]

            scores = compute_all_scores(primary_logits, ensemble_logits=other_logits,
                                        confidence_temperature=confidence_temperature)

            for key in all_scores:
                if key in scores:
                    all_scores[key].extend(scores[key].cpu().tolist())

    return {k: np.array(v) for k, v in all_scores.items() if len(v) > 0}


def compute_fpr_at_tpr(id_scores, ood_scores, tpr_target=0.95, higher_is_id=True):
    """
    FPR@95TPR: tại ngưỡng mà 95% ảnh ID được nhận đúng (TPR=95%),
    bao nhiêu % ảnh OOD bị lọt qua (bị coi nhầm là ID)?
    Càng THẤP càng tốt.
    """
    if not higher_is_id:
        id_scores = -id_scores
        ood_scores = -ood_scores

    threshold = np.percentile(id_scores, 100 * (1 - tpr_target))
    fpr = (ood_scores >= threshold).mean()
    return fpr


def compute_percentile_thresholds(id_scores, ood_scores, higher_is_id, percentiles=(90, 95, 99)):
    """
    Tính ngưỡng production theo percentile trên phân bố ID (Step 5).

    Khác với compute_fpr_at_tpr (đo chuẩn paper), ở đây ngưỡng được chọn TRỰC TIẾP
    từ phân bố ID: "tôi muốn q% ảnh lá thật được chấp nhận". Không tối ưu ngưỡng
    trên OOD để tránh overfit vào near-OOD set nhỏ (~100 ảnh).

    Quy ước ngưỡng khớp chính xác với compute_fpr_at_tpr:
        - higher_is_id=True : threshold = percentile(id, 100-q), chấp nhận score >= threshold
        - higher_is_id=False: threshold = percentile(id, q),     chấp nhận score <= threshold
    Nhờ vậy FPR@OOD tại q=95 sẽ xấp xỉ FPR@95TPR đo bằng benchmark (sanity check).

    Args:
        id_scores: [N] score trên tập ID (test set lá cây)
        ood_scores: [M] score trên tập OOD
        higher_is_id: True nếu score càng CAO càng khả nghi ID (vd MSP)
        percentiles: các mức q cần tính

    Returns:
        list[dict]: mỗi phần tử {percentile_id, threshold, tpr_id, fpr_ood}
    """
    rows = []
    for q in percentiles:
        if higher_is_id:
            threshold = np.percentile(id_scores, 100 - q)
            tpr_id = float((id_scores >= threshold).mean())
            fpr_ood = float((ood_scores >= threshold).mean())
        else:
            threshold = np.percentile(id_scores, q)
            tpr_id = float((id_scores <= threshold).mean())
            fpr_ood = float((ood_scores <= threshold).mean())
        rows.append({
            "percentile_id": q,
            "threshold": float(threshold),
            "tpr_id": tpr_id,
            "fpr_ood": fpr_ood,
        })
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ood-dir", type=str, default=None,
                        help="Thư mục ảnh OOD (không phải lá cây). Nếu bỏ trống, chỉ xem phân bố ID.")
    parser.add_argument("--tier", type=str, default="advanced",
                        choices=list(TIER_MODELS.keys()),
                        help="Tier cần calibrate: basic (1 model), standard (2), advanced (3)")
    parser.add_argument("--primary-backbone", type=str, default="efficientnet_b0",
                        choices=list(DEFAULT_SUFFIXES.keys()),
                        help="Backbone chính cho MSP/Entropy/Energy (mặc định: EffNet-B0 — primary mọi tier)")
    parser.add_argument("--max-id-images", type=int, default=None,
                        help="Giới hạn số ảnh ID để chạy nhanh hơn (mặc định dùng hết)")
    parser.add_argument("--ood-method", type=str, default="ensemble_disagreement",
                        choices=list(METHOD_DIRECTION.keys()),
                        help="Phương pháp được chốt làm tín hiệu OOD production")
    parser.add_argument("--threshold-percentile", type=int, default=95,
                        choices=[90, 95, 99],
                        help="Mức percentile trên ID dùng để chốt ngưỡng (95 = giữ 95%% ảnh lá thật)")
    parser.add_argument("--use-temperature", action="store_true",
                        help="Tính MSP trên softmax(logits/T) — confidence đã hiệu chỉnh "
                             "theo temperature của primary (gate công bằng mọi model)")
    args = parser.parse_args()

    cfg = load_config()
    split_dir = ml_path(cfg["paths"]["split_dir"])
    models_dir = ml_path(cfg["paths"]["models_dir"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print("=" * 70)
    print("BENCHMARK OOD DETECTION — MSP / Entropy / Energy / Ensemble")
    print("=" * 70)
    print(f"\nDevice: {device}")
    print(f"Backbone chính: {args.primary_backbone}\n")

    tier_suffixes = TIER_MODELS[args.tier]
    if args.primary_backbone not in tier_suffixes:
        raise ValueError(
            f"Primary backbone '{args.primary_backbone}' không thuộc tier '{args.tier}'. "
            f"Chọn 1 trong: {list(tier_suffixes.keys())}"
        )

    print(f"Đang load {len(tier_suffixes)} model của tier '{args.tier}'...")
    models = load_all_models(models_dir, device, suffixes=tier_suffixes)
    if args.primary_backbone not in models:
        raise ValueError(f"Không tìm thấy model chính '{args.primary_backbone}' đã train.")
    if len(models) < 2:
        print("\nCảnh báo: chỉ có 1 model (tier basic), không tính được ensemble_disagreement.")

    # Temperature của PRIMARY — gate MSP calibrated (nếu --use-temperature)
    confidence_temperature = None
    if args.use_temperature:
        primary_suffix = tier_suffixes[args.primary_backbone]
        temp_path = models_dir / f"temperature_{primary_suffix}.json"
        if temp_path.exists():
            with open(temp_path, encoding="utf-8") as f:
                confidence_temperature = json.load(f).get("temperature", 1.0)
            print(f"Confidence temperature ({primary_suffix}): T = {confidence_temperature:.4f}")
        else:
            print(f"[Cảnh báo] Không tìm thấy {temp_path.name} — dùng raw MSP (T = 1.0).")
            confidence_temperature = 1.0

    batch_size = cfg["train"]["batch_size"]

    # ------------------------------------------------------------------ #
    # ID data
    # ------------------------------------------------------------------ #
    id_ds = PlantDiseaseDataset(split_dir / "test", transform=eval_transform)
    if args.max_id_images and len(id_ds) > args.max_id_images:
        indices = np.random.RandomState(42).choice(len(id_ds), args.max_id_images, replace=False)
        id_ds = torch.utils.data.Subset(id_ds, indices)
    id_loader = DataLoader(id_ds, batch_size=batch_size, shuffle=False)

    print(f"\nID test set: {len(id_ds):,} ảnh")
    id_scores = collect_scores(id_loader, models, args.primary_backbone, device,
                               "ID (lá cây đã biết)", confidence_temperature=confidence_temperature)

    # ------------------------------------------------------------------ #
    # In phân bố score trên ID (luôn làm, kể cả chưa có OOD)
    # ------------------------------------------------------------------ #
    print(f"\n{'-' * 70}")
    print("PHÂN BỐ SCORE TRÊN ID (để tham khảo trước khi có OOD)")
    print(f"{'-' * 70}")
    for name, scores in id_scores.items():
        print(f"  {name:25s}: mean={scores.mean():.4f}  std={scores.std():.4f}  "
              f"min={scores.min():.4f}  max={scores.max():.4f}")

    if not args.ood_dir:
        print("\n[Chưa có --ood-dir] Chỉ hiển thị phân bố ID.")
        print("Chuẩn bị thư mục ảnh OOD (không phải lá cây) rồi chạy lại với --ood-dir để tính AUROC/FPR95.")
        return

    # ------------------------------------------------------------------ #
    # OOD data
    # ------------------------------------------------------------------ #
    ood_ds = FlatImageDataset(args.ood_dir, transform=eval_transform)
    if len(ood_ds) == 0:
        raise FileNotFoundError(f"Không tìm thấy ảnh nào trong {args.ood_dir}")
    ood_loader = DataLoader(ood_ds, batch_size=batch_size, shuffle=False)

    print(f"\nOOD test set: {len(ood_ds):,} ảnh (từ {args.ood_dir})")
    ood_scores = collect_scores(ood_loader, models, args.primary_backbone, device,
                                "OOD (không phải lá cây)", confidence_temperature=confidence_temperature)

    # ------------------------------------------------------------------ #
    # Tính AUROC + FPR95 cho từng phương pháp
    # ------------------------------------------------------------------ #
    # higher_is_id: True nghĩa là score càng CAO càng khả nghi ID (ngược lại là OOD)
    method_direction = METHOD_DIRECTION

    print(f"\n{'=' * 70}")
    print("KẾT QUẢ SO SÁNH 4 PHƯƠNG PHÁP")
    print(f"{'=' * 70}")
    print(f"{'Phương pháp':<25} {'AUROC':>8} {'FPR@95TPR':>12}   Ghi chú")
    print("-" * 70)

    results = {}
    for method, higher_is_id in method_direction.items():
        if method not in id_scores or method not in ood_scores:
            continue

        id_s = id_scores[method]
        ood_s = ood_scores[method]

        # Nhãn: 1 = ID, 0 = OOD. roc_auc_score cần score càng cao -> label càng "1"
        labels = np.concatenate([np.ones(len(id_s)), np.zeros(len(ood_s))])
        combined = np.concatenate([id_s, ood_s])
        if not higher_is_id:
            combined = -combined  # đảo dấu để "cao hơn = ID hơn" cho đúng chuẩn roc_auc_score

        auroc = roc_auc_score(labels, combined)
        fpr95 = compute_fpr_at_tpr(id_s, ood_s, tpr_target=0.95, higher_is_id=higher_is_id)

        results[method] = {"auroc": auroc, "fpr95": fpr95}

        print(f"{method:<25} {auroc:>8.4f} {fpr95:>11.2%}   AUROC càng cao / FPR95 càng thấp = tốt")

    # Lưu kết quả
    outputs_dir = ml_path(cfg["paths"]["outputs_dir"])
    result_path = outputs_dir / f"ood_benchmark_results_{args.tier}.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nĐã lưu kết quả tại {result_path}")

    best_method = max(results, key=lambda m: results[m]["auroc"])
    print(f"\n=> Phương pháp tốt nhất theo AUROC: {best_method} (AUROC={results[best_method]['auroc']:.4f})")

    # ------------------------------------------------------------------ #
    # Step 5: Chốt ngưỡng production theo percentile trên ID
    # (không tối ưu ngưỡng trực tiếp trên OOD — tránh overfit near-OOD ~100 ảnh)
    # ------------------------------------------------------------------ #
    print(f"\n{'=' * 70}")
    print("NGƯỠNG PRODUCTION THEO PERCENTILE TRÊN ID")
    print(f"{'=' * 70}")
    print("Ý nghĩa: chọn ngưỡng sao cho q% ảnh ID (lá thật) được chấp nhận,")
    print("rồi đo bao nhiêu % ảnh OOD lọt qua ngưỡng đó (FPR@OOD — càng thấp càng tốt).")

    all_thresholds = {}
    for method, higher_is_id in method_direction.items():
        if method not in id_scores or method not in ood_scores:
            continue
        rows = compute_percentile_thresholds(
            id_scores[method], ood_scores[method], higher_is_id
        )
        all_thresholds[method] = rows
        print(f"\n{method}:")
        print(f"{'q%':>4} {'threshold':>12} {'TPR@ID (đo)':>14} {'FPR@OOD':>10}")
        for row in rows:
            print(f"{row['percentile_id']:>4} {row['threshold']:>12.4f} "
                  f"{row['tpr_id']:>14.2%} {row['fpr_ood']:>10.2%}")

    chosen_method = args.ood_method
    if chosen_method not in all_thresholds:
        # Tier basic chỉ có 1 model -> không có ensemble_disagreement.
        # Ưu tiên 'msp' (đơn giản, khớp logic tier basic trong predict.py);
        # nếu không có thì chọn method tốt nhất còn lại theo AUROC.
        if "msp" in all_thresholds:
            chosen_method = "msp"
        elif results:
            chosen_method = max(results, key=lambda m: results[m]["auroc"])
        else:
            chosen_method = next(iter(all_thresholds))
        print(f"\n[Thông báo] '{args.ood_method}' không khả dụng ở tier '{args.tier}' "
              f"-> chốt method: '{chosen_method}'")

    chosen = {r["percentile_id"]: r for r in all_thresholds[chosen_method]}[
        args.threshold_percentile
    ]
    id_arr = id_scores[chosen_method]

    # Sanity check: FPR@OOD tại q=95 phải xấp xỉ FPR@95TPR của benchmark
    # (cùng quy ước percentile — nếu lệch nhiều nghĩa là có bug)
    benchmark_fpr95 = results.get(chosen_method, {}).get("fpr95")
    if benchmark_fpr95 is not None:
        delta = abs(chosen["fpr_ood"] - benchmark_fpr95)
        print(f"\nSanity check ({chosen_method}): FPR@OOD(q={args.threshold_percentile}) = "
              f"{chosen['fpr_ood']:.2%}  vs  FPR@95TPR benchmark = {benchmark_fpr95:.2%}  "
              f"(chênh lệch {delta:.2%})")
        if delta > 0.02:
            print("[CẢNH BÁO] Chênh lệch > 2% — kiểm tra lại hướng score/percentile.")

    # Gom ngưỡng của TẤT CẢ method khả dụng ở tier này theo mức percentile đã chọn
    signals = {}
    for method, rows in all_thresholds.items():
        row = next(r for r in rows if r["percentile_id"] == args.threshold_percentile)
        signals[method] = {
            "threshold": row["threshold"],
            "tpr_id": row["tpr_id"],
            "fpr_ood": row["fpr_ood"],
        }

    # Gate high/low conf theo percentile của CALIBRATED MSP (q=90 / q=99):
    #   high = p90 của ID  -> skip tầng 2 cho ~90% ảnh tự tin nhất (giữ profile compute)
    #   low  = p1  của ID  -> chỉ ~1% ảnh ID bị reject nhầm ở cổng dưới
    # T-normalization (chia logits/T của primary) đưa mọi model về cùng thang
    # -> các gate này áp dụng CÔNG BẰNG cho mọi model user chọn làm primary.
    gates = {}
    if "msp" in all_thresholds:
        msp_rows = {r["percentile_id"]: r for r in all_thresholds["msp"]}
        if 90 in msp_rows:
            gates["high_conf_msp"] = msp_rows[90]["threshold"]
        if 99 in msp_rows:
            gates["low_conf_msp"] = msp_rows[99]["threshold"]

    tier_entry = {
        "models": sorted(tier_suffixes.values()),
        "primary": tier_suffixes[args.primary_backbone],
        "gates": gates,
        "n_id_images": int(len(id_arr)),
        "n_ood_images": int(len(ood_scores[chosen_method])),
        "id_stats": {
            "mean": float(id_arr.mean()),
            "std": float(id_arr.std()),
            "p50": float(np.percentile(id_arr, 50)),
            "p95": float(np.percentile(id_arr, 95)),
            "p99": float(np.percentile(id_arr, 99)),
            "max": float(id_arr.max()),
        },
        "signals": signals,
    }

    # Gộp vào ood_threshold.json — mỗi lần chạy chỉ cập nhật tier hiện tại,
    # giữ nguyên các tier đã calibrate trước đó
    threshold_path = outputs_dir / "ood_threshold.json"
    payload = {}
    if threshold_path.exists():
        with open(threshold_path, encoding="utf-8") as f:
            payload = json.load(f)
        if "tiers" not in payload:
            payload = {}  # schema cũ (trước khi chia tier) -> ghi đè sạch

    payload["ood_method"] = chosen_method
    payload["percentile_id"] = args.threshold_percentile
    payload["high_conf_msp"] = HIGH_CONF_MSP
    payload["low_conf_msp"] = LOW_CONF_MSP
    payload["confidence_temperature"] = confidence_temperature
    payload["msp_scale"] = "calibrated" if args.use_temperature else "raw"
    payload.setdefault("tiers", {})[args.tier] = tier_entry

    with open(threshold_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\n✅ ĐÃ CHỐT tier '{args.tier}': method={chosen_method}, q={args.threshold_percentile}")
    for method, sig in signals.items():
        print(f"   {method:25s} threshold={sig['threshold']:.6f}  "
              f"TPR@ID={sig['tpr_id']:.2%}  FPR@OOD={sig['fpr_ood']:.2%}")
    print(f"Đã lưu ngưỡng tại {threshold_path}")


if __name__ == "__main__":
    main()
