"""
Test luồng OOD gating theo tier (basic / standard / advanced) — chỉ chạy ML, không đụng backend.

Nguồn ảnh:
    - ID:       data/split/test  (lá thật, 38 class — sample đa dạng class)
    - near_ood: data/ood_test/near_ood  (ảnh gần phân bố lá)
    - far_ood:  data/ood_test/cifar10   (ảnh CIFAR-10 — khác xa lá cây)
    - custom:   thư mục bất kỳ qua --custom-dir (vd: "D:\\QLPM\\Ảnh")

Kỳ vọng:
    - ID       -> đa so is_valid_leaf=True (high_confidence hoặc ensemble thấp)
    - near/far -> đa so is_valid_leaf=False (FPR thực tế ~4-12% tuỳ tier, mẫu nhỏ nên nhiễu)
    - Xác minh lazy load: model phu chỉ duoc load khi có ảnh rơi vào vùng lửng

Cách dùng:
    python src/test_ood_flow.py                                  # cả 3 tier, mỗi nguồn 5 ảnh
    python src/test_ood_flow.py --tier standard                  # 1 tier
    python src/test_ood_flow.py --n 3 --custom-dir "D:\\QLPM\\Ảnh"
"""

import argparse
import gc
import json
import random
from datetime import datetime
from pathlib import Path

import torch
from PIL import Image

from config import load_config, ml_path
from ood_scoring import TIER_MODELS
from predict import load_predictor

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def collect_images(folder: Path, n: int, rng: random.Random, recursive: bool = False):
    """Lấy tối đa n đường dẫn ảnh trong thư mục (flat hoặc đệ quy)."""
    it = folder.rglob("*") if recursive else folder.glob("*")
    paths = [p for p in it if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES]
    paths = sorted(paths) 
    rng.shuffle(paths)
    return paths[:n]


def sample_id_images(split_test_dir: Path, n: int, rng: random.Random):
    """Sample n ảnh ID ngẫu nhiên từ TOÀN BỘ tập test (không giới hạn 1 ảnh/class)."""
    classes = sorted(d for d in Path(split_test_dir).iterdir() if d.is_dir())
    all_imgs = []
    for cls in classes:
        imgs = sorted(p for p in cls.glob("*") if p.suffix.lower() in IMAGE_SUFFIXES)
        all_imgs.extend(imgs)
    rng.shuffle(all_imgs)
    return all_imgs[:n]


def run_tier(tier: str, sources: dict, gate_scale: str = "calibrated",
             seed: int = 42, n: int = 5, log_dir: Path = None,
             primary_backbone: str = None) -> dict:
    """Chạy 1 tier qua tất cả nguồn ảnh, in bảng kết quả + tổng kết (dùng chung cho raw/calibrated)."""
    primary_used = primary_backbone or next(iter(TIER_MODELS[tier]))
    print(f"\n{'=' * 78}")
    print(f"TIER: {tier.upper()}  (primary = {TIER_MODELS[tier][primary_used]}, "
          f"{len(TIER_MODELS[tier])} model trong tier)")
    print(f"{'=' * 78}")

    predictor = load_predictor(tier=tier, gate_scale=gate_scale,
                               primary_backbone=primary_backbone)
    rows = []
    forward_pass_count = 0
    aux_models_loaded = 0  # ✅ thêm dòng này để tracking lazy load

    for source_name, paths in sources.items():
        for path in paths:
            try:
                image = Image.open(path).convert("RGB")
            except Exception as e:  # ảnh lỗi -> ghi nhận và bỏ qua
                rows.append((source_name, path.name, f"[LOI DOC ANH: {e}]", None, None, None, None, None))
                continue
            result = predictor.predict_single(image)
            forward_pass_count += 1
            if result.get("ood_method") == "ensemble":
                # ✅ đếm số aux model thực sự được dùng trong lần này
                aux_models_loaded += len(predictor.ensemble_backbones)
                forward_pass_count += len(predictor.ensemble_backbones)
            rows.append((
                source_name,
                path.name,
                result["label"],
                result["confidence"],
                result.get("ood_method"),
                result.get("is_valid_leaf"),
                result.get("ensemble_disagreement"),
                result.get("msp_calibrated"),
            ))

    # Bảng chi tiết
    print(f"\n{'Nguon':<9} {'Anh':<36} {'Label':<30} {'Conf':>6} "
          f"{'MSPcal':>7} {'Method':<18} {'Leaf?':>6} {'Disagr':>8}")
    print("-" * 128)
    for source_name, name, label, conf, method, valid, disagreement, msp_cal in rows:
        conf_str = f"{conf:.4f}" if conf is not None else "-"
        cal_str = f"{msp_cal:.4f}" if msp_cal is not None else "-"
        method_str = method if method else "-"
        valid_str = ("TRUE" if valid else "FALSE") if valid is not None else "-"
        dis_str = f"{disagreement:.4f}" if disagreement is not None else "-"
        print(f"{source_name:<9} {name[:36]:<36} {str(label)[:30]:<30} {conf_str:>6} "
              f"{cal_str:>7} {method_str:<18} {valid_str:>6} {dis_str:>8}")

    # Tổng kết theo nguồn
    print(f"\n--- Tong ket tier {tier} ---")
    summary = {}
    for source_name in sources:
        sub = [r for r in rows if r[0] == source_name and r[5] is not None]
        if not sub:
            continue
        accepted = sum(1 for r in sub if r[5])
        if source_name == "ID":
            false_reject = len(sub) - accepted
            rate = false_reject / len(sub)
            summary["id_accept_rate"] = accepted / len(sub)
            summary["id_false_reject_rate"] = rate
            print(f"  {source_name:<9}: chap nhan {accepted}/{len(sub)} anh la that "
                  f"| BI CHAN OAN: {false_reject}/{len(sub)} ({rate:.1%})")
        else:
            fpr = accepted / len(sub)
            summary[f"{source_name.lower()}_fpr"] = fpr
            print(f"  {source_name:<9}: chan {len(sub) - accepted}/{len(sub)} anh OOD "
                  f"(FPR thuc te = {fpr:.1%})")
    summary["avg_forward_passes"] = forward_pass_count / max(len(rows), 1)
    
    # ✅ sửa: dùng aux_models_loaded thay vì aux_loaded
    print(f"  Lazy load: {aux_models_loaded} model phu da duoc load (qua ensemble)")
    print(f"  Avg forward passes/anh: {summary['avg_forward_passes']:.2f}")

    # Log ra file JSON — cấu trúc: outputs/<tier>/<primary>/ood_flow_<gate_scale>_<tier>_<ts>.json
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if log_dir is None:
        log_dir = Path(__file__).parent.parent / "outputs"
    out_dir = log_dir / tier / primary_used
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / f"ood_flow_{gate_scale}_{tier}_{ts}.json"
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "tier": tier,
        "gate_scale": gate_scale,
        "primary": primary_used,
        "seed": seed,
        "n": n,
        "sampled_files": {
            source: [str(p) for p in paths]
            for source, paths in sources.items()
        },
        "rows": [
            {
                "source": r[0],
                "file": r[1],
                "label": r[2],
                "confidence": r[3],
                "ood_method": r[4],
                "is_valid_leaf": r[5],
                "ensemble_disagreement": r[6],
                "msp_calibrated": r[7],
            }
            for r in rows
        ],
        "summary": summary,
    }
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)
    print(f"\n  [LOG] Ghi: {log_path}")

    del predictor
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return summary


def main():
    parser = argparse.ArgumentParser(description="Test luong OOD gating theo tier (ML only)")
    parser.add_argument("--tier", type=str, default=None, choices=list(TIER_MODELS.keys()),
                        help="Chi chay 1 tier. Bo trong = chay ca 3 tier.")
    parser.add_argument("--n", type=int, default=5, help="So anh moi nguon (ID/near/far)")
    parser.add_argument("--custom-dir", type=str, default=None,
                        help="Thu muc anh tuy y de test them (vd: 'D:\\\\QLPM\\\\Anh')")
    parser.add_argument("--seed", type=int, default=42, help="Seed sample anh (tai lap duoc)")
    parser.add_argument("--compare-gate", action="store_true",
                        help="Chay ca RAW + CALIBRATED gate tren cung 1 bo anh, in bang so sanh")
    parser.add_argument("--primary", type=str, default=None,
                        choices=sorted({b for models in TIER_MODELS.values() for b in models}),
                        help="Model lam primary (label/confidence tu model nay). "
                             "Mac dinh: model dau tien cua tier (EffNet-B0)")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    cfg = load_config()
    split_test = ml_path(cfg["paths"]["split_dir"]) / "test"
    ood_dir = ml_path(cfg["paths"]["outputs_dir"]).parent / "data" / "ood_test"

    # Sample 1 lan duy nhat — dung chung cho moi run (cung seed = cong bang)
    sources = {
        "ID": sample_id_images(split_test, args.n, rng),
        "NEAR-OOD": collect_images(ood_dir / "near_ood", args.n, rng),
        "FAR-OOD": collect_images(ood_dir / "cifar10", args.n, rng, recursive=True),
    }
    if args.custom_dir:
        custom = collect_images(Path(args.custom_dir), 20, rng, recursive=True)
        if custom:
            sources["CUSTOM"] = custom
        else:
            print(f"[Canh bao] Khong tim thay anh trong {args.custom_dir}")

    for name, paths in sources.items():
        print(f"Nguon {name}: {len(paths)} anh")

    tiers = [args.tier] if args.tier else list(TIER_MODELS.keys())

    if args.compare_gate:
        print(f"\n{'=' * 78}")
        print("CHAY SO SANH RAW vs CALIBRATED (cung 1 bo anh, cung seed)")
        print(f"{'=' * 78}")
        comparison = {}
        for tier in tiers:
            print(f"\n--- RAW — tier {tier} ---")
            raw_summary = run_tier(tier, sources, gate_scale="raw", seed=args.seed, n=args.n,
                                   primary_backbone=args.primary)
            print(f"\n--- CALIBRATED — tier {tier} ---")
            calib_summary = run_tier(tier, sources, gate_scale="calibrated", seed=args.seed, n=args.n,
                                     primary_backbone=args.primary)
            comparison[tier] = {"raw": raw_summary, "calibrated": calib_summary}

        print(f"\n{'=' * 78}")
        print("BANG SO SANH RAW vs CALIBRATED")
        print(f"{'=' * 78}")
        for tier_key, res in comparison.items():
            print(f"\n--- Tier: {tier_key} ---")
            print(f"{'Chi so':<28} {'RAW':>10} {'CALIBRATED':>12}")
            for key in res["raw"]:
                r = res["raw"][key]
                c = res["calibrated"][key]
                if isinstance(r, float) and isinstance(c, float):
                    print(f"{key:<28} {r:>10.3f} {c:>12.3f}")
                else:
                    print(f"{key:<28} {str(r):>10} {str(c):>12}")
    else:
        for tier in tiers:
            run_tier(tier, sources, gate_scale="calibrated", seed=args.seed, n=args.n,
                     primary_backbone=args.primary)

    print("\nHoan tat test luong OOD gating.")


# chạy bằng lệnh:
# python ml/src/test_ood_flow.py              # cả 3 tier, 5 ảnh/nguồn
# python ml/src/test_ood_flow.py --tier advanced --n 10
# python ml/src/test_ood_flow.py --custom-dir "D:\Anh" --n 3
if __name__ == "__main__":
    main()

    # python ml/src/test_ood_flow.py --compare-gate