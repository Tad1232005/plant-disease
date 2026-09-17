"""
Module inference dùng chung cho ML và backend.

Chức năng:
    - Load model + classes từ file
    - Preprocess ảnh (PIL → tensor)
    - Predict: trả label + confidence + all_probs
    - Temperature scaling calibration (tùy chọn)
    - GradCAM heatmap visualization (tùy chọn)

Cách dùng:
    from predict import load_predictor
    predictor = load_predictor(use_calibration=True)
    result = predictor.predict_single(pil_image)
    # result = {"label": "Tomato___healthy", "confidence": 0.9876, "all_probs": [...]}

Test CLI:
    python ml/src/predict.py --image path/to/image.jpg
    python ml/src/predict.py --image path/to/image.jpg --calibrate
    python ml/src/predict.py --image path/to/image.jpg --gradcam --output heatmap.png
"""

import io
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image

from config import load_config, ml_path
from data_loader import eval_transform
from model import build_model
from ood_scoring import (
    HIGH_CONF_MSP,
    LOW_CONF_MSP,
    TIER_MODELS,
    compute_all_scores,
    compute_ensemble_disagreement,
)


class Predictor:
    """
    Wrapper cho model inference.
    Load model 1 lần, dùng nhiều lần predict.
    """

    def __init__(
        self,
        model_path: Path = None,
        classes_path: Path = None,
        use_calibration: bool = False,
        model_type: str = None,
        model_suffix: str = None,
        tier: str = None,
        primary_backbone: str = None,
        high_conf_msp: float = None,
        low_conf_msp: float = None,
        ood_threshold_path: Path = None,
        gate_scale: str = "calibrated",   # "calibrated" (mặc định) / "raw"
    ):
        """
        Args:
            model_path: Đường dẫn den best_model.pt (mặc định từ config)
            classes_path: Đường dẫn den classes.json (mặc định từ config)
            use_calibration: Có dùng temperature scaling không (mặc định False)
            model_type: Loại model (mặc định từ config)
            model_suffix: Suffix của model (ví dụ: resnet50, efficientnet_b0)
            tier: "basic" | "standard" | "advanced" — bật logic 2 tầng (OOD gating).
                Khi set, các model còn lại duoc LAZY LOAD chỉ khi ảnh rơi vào vùng lửng MSP.
            primary_backbone: Backbone làm PRIMARY — label/confidence lấy từ model này
                (mặc định: model ĐẦU TIÊN của tier = EffNet-B0). Bắt buộc thuộc bo model
                của tier. Ensemble vẫn đủ bo tier nên ngưỡng per-tier KHÔNG đổi.
                Riêng tier basic: chỉ hỗ trợ primary mặc định (ngưỡng MSP chỉ
                calibrate cho EffNet-B0).
            high_conf_msp: Ngưỡng MSP "rat tự tin" (mặc định HIGH_CONF_MSP = 0.99)
            low_conf_msp: Ngưỡng MSP "quá phân vân" (mặc định LOW_CONF_MSP = 0.5)
            ood_threshold_path: File ngưỡng (mặc định outputs/ood_threshold.json)
            gate_scale: "calibrated" (mặc định — dùng gate JSON + T thực tế);
                        "raw" (bỏ qua gate JSON, dùng T=1.0 + ngưỡng goc)
        """
        cfg = load_config()
        models_dir = ml_path(cfg["paths"]["models_dir"])
        outputs_dir = ml_path(cfg["paths"]["outputs_dir"])

        # ---- Cấu hình tier (Basic / Standard / Advanced) ------------------ #
        self.tier = tier
        self.high_conf_msp = high_conf_msp if high_conf_msp is not None else HIGH_CONF_MSP
        self.low_conf_msp = low_conf_msp if low_conf_msp is not None else LOW_CONF_MSP
        self.gate_scale = gate_scale
        self.ensemble_available = False
        self.ood_threshold = None       # ngưỡng ensemble disagreement của tier
        self.msp_threshold = None       # ngưỡng MSP (dùng cho tier basic)
        self._aux_models = None         # lazy load — chỉ load khi ảnh vào vùng lửng
        self.ensemble_backbones = []
        self.ensemble_suffixes = []

        if tier is not None:
            if tier not in TIER_MODELS:
                raise ValueError(f"Tier không hợp lệ: '{tier}'. Chọn 1 trong: {list(TIER_MODELS)}")
            tier_suffixes = TIER_MODELS[tier]
            default_primary = next(iter(tier_suffixes))

            # User có the chọn model làm PRIMARY (label/confidence lấy từ model đó).
            # Mặc định: model đầu tiên của tier (EfficientNet-B0).
            if primary_backbone is None:
                primary_backbone = default_primary
            if primary_backbone not in tier_suffixes:
                raise ValueError(
                    f"Model '{primary_backbone}' không thuộc tier '{tier}'. "
                    f"Chọn 1 trong: {list(tier_suffixes.keys())}"
                )
            if tier == "basic" and primary_backbone != default_primary:
                raise ValueError(
                    f"Tier basic chỉ hỗ trợ primary = '{default_primary}' (ngưỡng MSP "
                    f"hiện chỉ calibrate cho model này). Model khác cần calibrate riêng: "
                    f"evaluate_ood.py --tier basic --primary-backbone <model>"
                )

            model_suffix = tier_suffixes[primary_backbone]
            # Ensemble VẪN ĐỦ BỘ tier (primary duoc loại khỏi danh sách lazy-load
            # vì logits của primary đã có sẵn khi tinh disagreement) ->
            # disagreement bất biến theo tập model, ngưỡng per-tier giữ nguyên.
            self.ensemble_backbones = [b for b in tier_suffixes if b != primary_backbone]
            self.ensemble_suffixes = [tier_suffixes[b] for b in self.ensemble_backbones]

            # Đọc ngưỡng của tier từ ood_threshold.json (nếu đã calibrate)
            if ood_threshold_path is None:
                ood_threshold_path = outputs_dir / "ood_threshold.json"
            tier_data = None
            if Path(ood_threshold_path).exists():
                with open(ood_threshold_path, encoding="utf-8") as f:
                    payload = json.load(f)
                tier_data = payload.get("tiers", {}).get(tier)
            if tier_data:
                signals = tier_data.get("signals", {})
                self.ood_threshold = signals.get("ensemble_disagreement", {}).get("threshold")
                self.msp_threshold = signals.get("msp", {}).get("threshold")
                # Gate high/low conf từ calibration (calibrated MSP) — chỉ ghi đè
                # khi gate_scale == "calibrated". Khi "raw": giữ ngưỡng goc
                # (HIGH_CONF_MSP=0.99 / LOW_CONF_MSP=0.5, hoặc giá trị bạn truyền tay)
                if self.gate_scale == "calibrated":
                    gates = tier_data.get("gates", {})
                    if gates.get("high_conf_msp") is not None:
                        self.high_conf_msp = gates["high_conf_msp"]
                    if gates.get("low_conf_msp") is not None:
                        self.low_conf_msp = gates["low_conf_msp"]
                # gate_scale == "raw": giữ self.high_conf_msp / self.low_conf_msp
                # (gần nhất ngưỡng goc, hoặc giá trị bạn truyền tay)
            else:
                print(f"Warning: chưa có ngưỡng cho tier '{tier}' trong {ood_threshold_path} "
                      f"-> chạy evaluate_ood.py --tier {tier} để calibrate. "
                      f"Tạm thời fallback: chấp nhận mọi ảnh (ood_method='fallback_no_threshold').")

        # Load model theo suffix hoặc mặc định
        if model_suffix:
            model_path = models_dir / f"best_model_{model_suffix}.pt"
            classes_path = models_dir / f"classes_{model_suffix}.json"
            model_type_path = models_dir / f"model_type_{model_suffix}.json"

            # Đọc model_type từ file
            if model_type_path.exists():
                with open(model_type_path, encoding="utf-8") as f:
                    model_type_data = json.load(f)
                    model_type = model_type_data.get("model_type", "mobilenet_v2")
            else:
                model_type = "mobilenet_v2"  # Fallback
        else:
            if model_path is None:
                model_path = models_dir / "best_model.pt"
            if classes_path is None:
                classes_path = models_dir / "classes.json"
            if model_type is None:
                model_type = cfg["train"].get("model_type", "mobilenet_v2")

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Device: {self.device}")

        # Load classes
        with open(classes_path, encoding="utf-8") as f:
            self.classes = json.load(f)
        self.num_classes = len(self.classes)
        print(f"Loaded {self.num_classes} classes")
        print(f"Model type: {model_type}")

        # Load model
        print(f"Loading model from {model_path}...")
        self.model = build_model(num_classes=self.num_classes, model_type=model_type)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()
        print("Loaded model xong")

        # Load temperature scaling — LUÔN load (gate calibrated MSP cần T của
        # primary); riêng hiển thị confidence chỉ áp T khi use_calibration=True
        self.temperature = 1.0
        self.use_calibration = use_calibration
        if model_suffix:
            temperature_path = models_dir / f"temperature_{model_suffix}.json"
        else:
            temperature_path = models_dir / "temperature.json"
        if temperature_path.exists():
            with open(temperature_path, encoding="utf-8") as f:
                temp_data = json.load(f)
                self.temperature = temp_data["temperature"]
            print(f"Loaded temperature scaling: T = {self.temperature:.4f}")
        else:
            print(f"Warning: Không tìm thấy {temperature_path}, dùng T = 1.0")
            print(f"Chạy 'python ml/src/calibration.py --find-temperature --model-suffix {model_suffix}' để tìm T tối ưu")

    def preprocess(self, image: Image.Image) -> torch.Tensor:
        """
        Chuyển ảnh PIL → tensor (batch=1).

        Args:
            image: PIL Image (RGB)

        Returns:
            Tensor shape [1, 3, 224, 224]
        """
        if image.mode != "RGB":
            image = image.convert("RGB")
        tensor = eval_transform(image)
        return tensor.unsqueeze(0)  # [1, C, H, W]

    def _ensure_ensemble_models(self) -> bool:
        """
        Lazy load các model PHỤ của tier — chỉ gọi khi ảnh rơi vào vùng lửng MSP
        (0.5 – 0.99) để tiết kiệm RAM và thời gian khởi động.

        Returns:
            True nếu đủ model phu + ngưỡng để tinh ensemble disagreement.
        """
        if self._aux_models is not None:
            return len(self._aux_models) > 0 and self.ood_threshold is not None

        self._aux_models = {}
        cfg = load_config()
        models_dir = ml_path(cfg["paths"]["models_dir"])

        for backbone, suffix in zip(self.ensemble_backbones, self.ensemble_suffixes):
            aux_model_path = models_dir / f"best_model_{suffix}.pt"
            aux_classes_path = models_dir / f"classes_{suffix}.json"
            aux_model_type_path = models_dir / f"model_type_{suffix}.json"

            if not aux_model_path.exists():
                print(f"Warning: thiếu {aux_model_path.name} — tắt ensemble, fallback MSP-only.")
                self._aux_models = {}
                return False

            with open(aux_classes_path, encoding="utf-8") as f:
                aux_classes = json.load(f)
            with open(aux_model_type_path, encoding="utf-8") as f:
                aux_model_type = json.load(f).get("model_type", "mobilenet_v2")

            aux_model = build_model(num_classes=len(aux_classes), model_type=aux_model_type)
            aux_model.load_state_dict(torch.load(aux_model_path, map_location=self.device))
            aux_model.to(self.device)
            aux_model.eval()
            self._aux_models[backbone] = aux_model
            print(f"  [Lazy load] Loaded model phu: {backbone} ({suffix})")

        self.ensemble_available = len(self._aux_models) > 0
        return self.ensemble_available and self.ood_threshold is not None

    def predict_single(self, image: Image.Image, compute_ood: bool = False) -> Dict[str, object]:
        """
        Predict cho 1 ảnh.

        Args:
            image: PIL Image (RGB)
            compute_ood: Có tinh OOD scores không (MSP, Entropy, Energy)

        Returns:
            Dict với keys:
                - label: str (tên class)
                - confidence: float (max probability)
                - all_probs: List[float] (38 probabilities theo thứ tự classes)
                - temperature: float (nếu dùng calibration)
                - ood_scores: dict (nếu compute_ood=True) với keys:
                    - msp: Max Softmax Probability
                    - entropy: Entropy score
                    - energy: Energy score
        """
        # Preprocess
        input_tensor = self.preprocess(image)
        input_tensor = input_tensor.to(self.device)

        # Inference
        with torch.no_grad():
            outputs = self.model(input_tensor)  # [1, num_classes]
            
            # Lưu logits truoc khi temperature scaling cho OOD scores
            logits_for_ood = outputs.clone()
            
            # Apply temperature scaling nếu enabled
            if self.use_calibration:
                outputs = outputs / self.temperature
            
            probs = torch.softmax(outputs, dim=1)[0]  # [num_classes]
            probs_np = probs.cpu().numpy()

        # Get prediction
        pred_idx = int(probs.argmax().item())
        confidence = float(probs[pred_idx].item())
        label = self.classes[pred_idx]
        all_probs = probs_np.tolist()

        result = {
            "label": label,
            "confidence": confidence,
            "all_probs": all_probs,
        }
        
        if self.use_calibration:
            result["temperature"] = self.temperature
        
        # Compute OOD scores nếu requested
        if compute_ood:
            ood_scores = compute_all_scores(logits_for_ood)
            result["ood_scores"] = {
                "msp": float(ood_scores["msp"].item()),
                "entropy": float(ood_scores["entropy"].item()),
                "energy": float(ood_scores["energy"].item()),
            }

        # ---- Logic 2 tầng theo tier (OOD gating) -------------------------- #
        if self.tier is not None:
            result["tier"] = self.tier
            result["ensemble_disagreement"] = None
            # Gate dùng CALIBRATED MSP: softmax(logits/T) với T của primary —
            # mọi model nằm trên cùng thang tin cậy, gate công bằng khi user
            # chọn model khác làm primary. Disagreement vẫn trên raw logits.
            with torch.no_grad():
                gate_temperature = self.temperature if self.gate_scale == "calibrated" else 1.0
                probs_cal = torch.softmax(logits_for_ood / gate_temperature, dim=1)[0]
            msp = float(probs_cal.max().item())
            result["msp_raw"] = confidence
            result["msp_calibrated"] = msp

            if self.tier == "basic":
                # Basic: chỉ 1 model — quyết định bằng ngưỡng MSP đã calibrate
                if self.msp_threshold is not None:
                    result["is_valid_leaf"] = msp >= self.msp_threshold
                    result["ood_method"] = "msp"
                    result["ood_threshold"] = self.msp_threshold
                else:
                    result["is_valid_leaf"] = True
                    result["ood_method"] = "fallback_no_threshold"
            elif msp >= self.high_conf_msp:
                # Tầng 1: model rat tự tin -> trả ngay, không load model phu
                result["is_valid_leaf"] = True
                result["ood_method"] = "high_confidence"
            elif msp < self.low_conf_msp:
                # Tầng 1: quá phân vân -> loại ngay
                result["is_valid_leaf"] = False
                result["ood_method"] = "low_confidence"
            elif self._ensure_ensemble_models():
                # Tầng 2: lazy load model phu -> tinh disagreement (reuse logits primary)
                with torch.no_grad():
                    aux_logits = [aux_model(input_tensor) for aux_model in self._aux_models.values()]
                disagreement = float(
                    compute_ensemble_disagreement([logits_for_ood] + aux_logits)[0].item()
                )
                result["ensemble_disagreement"] = disagreement
                result["ood_threshold"] = self.ood_threshold
                result["is_valid_leaf"] = disagreement <= self.ood_threshold
                result["ood_method"] = "ensemble"
            else:
                # Không có ngưỡng / thiếu model phu -> chấp nhận, danh dấu để kiểm tra
                result["is_valid_leaf"] = True
                result["ood_method"] = "fallback_no_threshold"

        return result

    def generate_gradcam(
        self,
        image: Image.Image,
        target_class: Optional[int] = None,
    ) -> Tuple[np.ndarray, int]:
        """
        Generate GradCAM heatmap cho 1 ảnh.
        
        Args:
            image: PIL Image (RGB)
            target_class: Target class index (nếu None, dùng predicted class)
        
        Returns:
            Tuple[np.ndarray, int]: (heatmap [H, W], target_class)
        """
        import cv2
        
        # Preprocess
        input_tensor = self.preprocess(image)
        input_tensor = input_tensor.to(self.device)
        
        # Get target class
        if target_class is None:
            with torch.no_grad():
                outputs = self.model(input_tensor)
                target_class = outputs.argmax(dim=1).item()
        
        # Register hooks
        gradients = None
        activations = None
        
        def forward_hook(module, input, output):
            nonlocal activations
            activations = output

        def backward_hook(module, grad_input, grad_output):
            nonlocal gradients
            gradients = grad_output[0]

        # MobileNetV2: use last feature layer
        target_layer = self.model.features[-1]
        handle_forward = target_layer.register_forward_hook(forward_hook)
        handle_backward = target_layer.register_full_backward_hook(backward_hook)
        
        # Forward pass
        self.model.eval()
        output = self.model(input_tensor)
        
        # Backward pass
        self.model.zero_grad()
        output[0, target_class].backward(retain_graph=True)
        
        # Remove hooks
        handle_forward.remove()
        handle_backward.remove()
        
        # Compute weights: global average pooling của gradients
        weights = gradients.mean(dim=[2, 3], keepdim=True)  # [1, C, 1, 1]
        
        # Weighted sum của activations
        heatmap = (weights * activations).sum(dim=1).squeeze()  # [H', W']
        
        # ReLU để chỉ giữ positive values
        heatmap = F.relu(heatmap)
        
        # Normalize về 0-255
        heatmap = heatmap - heatmap.min()
        heatmap = heatmap / (heatmap.max() + 1e-8)
        heatmap = (heatmap * 255).detach().cpu().numpy().astype(np.uint8)
        
        return heatmap, target_class

    def visualize_gradcam(
        self,
        image: Image.Image,
        heatmap: np.ndarray,
        alpha: float = 0.4,
    ) -> Image.Image:
        """
        Overlay heatmap lên ảnh goc.
        
        Args:
            image: PIL Image goc
            heatmap: Heatmap từ generate_gradcam [H, W]
            alpha: Transparency của heatmap (0-1)
        
        Returns:
            Image.Image: Ảnh với heatmap overlay
        """
        import cv2
        
        # Resize heatmap về kích thước ảnh goc
        heatmap_resized = cv2.resize(heatmap, (image.size[0], image.size[1]))
        
        # Apply colormap
        heatmap_colored = cv2.applyColorMap(heatmap_resized, cv2.COLORMAP_JET)
        heatmap_colored = cv2.cvtColor(heatmap_colored, cv2.COLOR_BGR2RGB)
        
        # Blend với ảnh goc
        image_np = np.array(image)
        overlay = cv2.addWeighted(image_np, 1 - alpha, heatmap_colored, alpha, 0)
        
        return Image.fromarray(overlay)


def load_predictor(
    model_path: Path = None,
    classes_path: Path = None,
    use_calibration: bool = False,
    model_type: str = None,
    model_suffix: str = None,
    tier: str = None,
    primary_backbone: str = None,
    gate_scale: str = "calibrated",
) -> Predictor:
    """
    Factory function để tạo Predictor instance.

    Args:
        model_path: Đường dẫn den best_model.pt (optional)
        classes_path: Đường dẫn den classes.json (optional)
        use_calibration: Có dùng temperature scaling không (optional)
        model_type: Loại model (optional)
        model_suffix: Suffix của model (ví dụ: resnet50, efficientnet_b0)
        tier: "basic" | "standard" | "advanced" (optional)
        primary_backbone: Backbone làm PRIMARY (optional)
        gate_scale: "calibrated" (mặc định) / "raw"

    Returns:
        Predictor instance
    """
    return Predictor(model_path=model_path, classes_path=classes_path,
                     use_calibration=use_calibration, model_type=model_type,
                     model_suffix=model_suffix, tier=tier,
                     primary_backbone=primary_backbone, gate_scale=gate_scale)


def main():
    """CLI test - predict 1 ảnh mẫu."""
    import argparse

    parser = argparse.ArgumentParser(description="Test predict.py với 1 ảnh")
    parser.add_argument("--image", type=str, required=True, help="Đường dẫn den ảnh test")
    parser.add_argument("--calibrate", action="store_true", help="Dùng temperature scaling calibration")
    parser.add_argument("--compute-ood", action="store_true", help="Tinh OOD scores (MSP, Entropy, Energy)")
    parser.add_argument("--gradcam", action="store_true", help="Generate GradCAM heatmap")
    parser.add_argument("--output", type=str, help="Đường dẫn để lưu heatmap (chỉ dùng với --gradcam)")
    parser.add_argument("--model-suffix", type=str, help="Suffix của model (ví dụ: resnet50, efficientnet_b0)")
    parser.add_argument("--tier", type=str, default=None, choices=list(TIER_MODELS.keys()),
                        help="Bật logic 2 tầng theo tier (basic/standard/advanced) — OOD gating")
    parser.add_argument("--primary", type=str, default=None,
                        choices=sorted({b for models in TIER_MODELS.values() for b in models}),
                        help="Model làm primary (label/confidence lấy từ model này). "
                             "Mặc định: model đầu tiên của tier (EffNet-B0)")
    args = parser.parse_args()

    # Load predictor
    predictor = load_predictor(use_calibration=args.calibrate, model_suffix=args.model_suffix,
                               tier=args.tier, primary_backbone=args.primary)

    # Load ảnh
    img_path = Path(args.image)
    if not img_path.exists():
        print(f"Lỗi: Không tìm thấy ảnh tại {img_path}")
        return

    image = Image.open(img_path)

    # Predict
    result = predictor.predict_single(image, compute_ood=args.compute_ood)

    # Print result
    print("\n=== Kết quả predict ===")
    print(f"Label: {result['label']}")
    print(f"Confidence: {result['confidence']:.4f} ({result['confidence'] * 100:.2f}%)")
    if "temperature" in result:
        print(f"Temperature: {result['temperature']:.4f}")
    if "is_valid_leaf" in result:
        print(f"\n=== Quyết định OOD (tier: {result['tier']}) ===")
        print(f"ood_method: {result['ood_method']}")
        print(f"is_valid_leaf: {result['is_valid_leaf']}")
        if "msp_calibrated" in result:
            print(f"MSP calibrated (gate): {result['msp_calibrated']:.4f} "
                  f"(raw: {result.get('msp_raw'):.4f})")
        if result.get("ensemble_disagreement") is not None:
            print(f"ensemble_disagreement: {result['ensemble_disagreement']:.4f} "
                  f"(ngưỡng {result.get('ood_threshold'):.4f})")
    print(f"So classes: {len(result['all_probs'])}")
    print(f"Top 5 probs:")
    sorted_indices = sorted(range(len(result['all_probs'])), key=lambda i: result['all_probs'][i], reverse=True)[:5]
    for idx in sorted_indices:
        print(f"  {predictor.classes[idx]}: {result['all_probs'][idx]:.4f}")
    
    # Print OOD scores nếu có
    if "ood_scores" in result:
        print(f"\n=== OOD Scores ===")
        print(f"MSP (Max Softmax Probability): {result['ood_scores']['msp']:.4f}")
        print(f"Entropy: {result['ood_scores']['entropy']:.4f}")
        print(f"Energy: {result['ood_scores']['energy']:.4f}")
        print(f"\nGiải thích:")
        print(f"  - MSP cao (> 0.9): Khả năng ID cao")
        print(f"  - Entropy cao (> 0.5): Khả năng OOD cao")
        print(f"  - Energy cao (> -1.0): Khả năng OOD cao")

    # GradCAM
    if args.gradcam:
        print("\n=== Generating GradCAM heatmap ===")
        heatmap, target_class = predictor.generate_gradcam(image)
        overlay = predictor.visualize_gradcam(image, heatmap)
        
        # Save
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = img_path.parent / f"{img_path.stem}_gradcam{img_path.suffix}"
        
        overlay.save(output_path)
        print(f"Da lưu heatmap tại {output_path}")
        print(f"Target class: {predictor.classes[target_class]}")


if __name__ == "__main__":
    main()
