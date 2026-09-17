"""
Module tính các OOD (Out-of-Distribution) score — dùng chung cho predict.py
và evaluate_ood.py.

4 phương pháp:
    1. MSP (Max Softmax Probability) — Hendrycks & Gimpel, 2017
       Baseline chuẩn: confidence càng thấp -> càng khả nghi OOD.
    2. Entropy — đo độ "phân tán" của cả phân phối xác suất, không chỉ top-1.
       Bắt được trường hợp model phân vân đều giữa nhiều lớp (MSP có thể bỏ sót).
    3. Energy — Liu et al., NeurIPS 2020 ("Energy-based Out-of-distribution Detection")
       Dùng logits TRƯỚC softmax, không bị bóp méo bởi chuẩn hóa softmax.
       Energy càng cao (ít âm hơn) -> càng khả nghi OOD.
    4. Ensemble disagreement — Lakshminarayanan et al., NeurIPS 2017 ("Deep Ensembles")
       Đo mức độ bất đồng giữa nhiều model độc lập (ở đây: 3 backbone đã train).
       Bất đồng cao -> khả nghi OOD (mỗi model "đoán bừa" theo hướng khác nhau).

Lưu ý quan trọng:
    Temperature scaling (calibration.py) tối ưu cho ID calibration, KHÔNG tối ưu
    cho phân tách ID/OOD (đã được chỉ ra trong paper ODIN, Liang et al. 2018 —
    họ dùng T rất lớn, khác hẳn T dùng để calibrate ID). Vì vậy các hàm dưới đây
    mặc định KHÔNG áp dụng temperature đã calibrate, trừ khi truyền vào rõ ràng.
"""

import numpy as np
import torch
import torch.nn.functional as F


def compute_msp(logits: torch.Tensor) -> torch.Tensor:
    """
    Max Softmax Probability — càng thấp càng khả nghi OOD.

    Args:
        logits: [N, C] logits trước softmax

    Returns:
        [N] MSP score, khoảng (0, 1]
    """
    probs = F.softmax(logits, dim=1)
    msp, _ = probs.max(dim=1)
    return msp


def compute_entropy(logits: torch.Tensor, normalize: bool = True) -> torch.Tensor:
    """
    Entropy của phân phối xác suất — càng CAO càng khả nghi OOD
    (ngược hướng với MSP, cần đảo dấu nếu muốn dùng chung 1 chiều "càng cao càng ID").

    Args:
        logits: [N, C] logits trước softmax
        normalize: chia cho log(C) để entropy nằm trong [0, 1], dễ so sánh giữa
            các bộ dữ liệu có số lớp khác nhau.

    Returns:
        [N] entropy score
    """
    probs = F.softmax(logits, dim=1)
    log_probs = torch.log(probs.clamp(min=1e-12))
    entropy = -(probs * log_probs).sum(dim=1)
    if normalize:
        num_classes = logits.shape[1]
        entropy = entropy / np.log(num_classes)
    return entropy


def compute_energy(logits: torch.Tensor, temperature: float = 1.0) -> torch.Tensor:
    """
    Energy score (Liu et al. 2020) — E(x) = -T * logsumexp(logits / T)
    Energy càng CAO (ít âm hơn) càng khả nghi OOD.

    Args:
        logits: [N, C] logits trước softmax
        temperature: T dùng riêng cho energy, KHÔNG phải T từ calibration.py
            (paper gốc thường để T=1.0 mặc định, có thể tune riêng nếu cần)

    Returns:
        [N] energy score (số âm, giá trị càng lớn/ít âm càng khả nghi OOD)
    """
    energy = -temperature * torch.logsumexp(logits / temperature, dim=1)
    return energy


def compute_ensemble_disagreement(list_of_logits: list) -> torch.Tensor:
    """
    Độ bất đồng giữa nhiều model (ensemble) — dùng trung bình KL-divergence
    giữa từng cặp phân phối xác suất so với phân phối trung bình.
    Càng CAO càng khả nghi OOD (các model "cãi nhau").

    Args:
        list_of_logits: list gồm N_models tensor, mỗi tensor shape [N, C]
            (logits của cùng 1 batch ảnh, từ N_models model khác nhau)

    Returns:
        [N] disagreement score
    """
    probs_list = [F.softmax(logits, dim=1) for logits in list_of_logits]
    stacked = torch.stack(probs_list, dim=0)  # [N_models, N, C]
    mean_probs = stacked.mean(dim=0)  # [N, C] — phân phối trung bình

    # KL(model_i || mean) trung bình qua các model
    kl_divs = []
    for probs in probs_list:
        log_ratio = torch.log(probs.clamp(min=1e-12)) - torch.log(mean_probs.clamp(min=1e-12))
        kl = (probs * log_ratio).sum(dim=1)
        kl_divs.append(kl)

    disagreement = torch.stack(kl_divs, dim=0).mean(dim=0)  # [N]
    return disagreement


def compute_all_scores(
    logits: torch.Tensor,
    ensemble_logits: list = None,
    energy_temperature: float = 1.0,
    confidence_temperature: float = None,
) -> dict:
    """
    Tính tất cả score cùng lúc cho 1 batch, dùng trong predict.py hoặc benchmark.

    Args:
        logits: [N, C] logits từ model chính (vd ResNet50)
        ensemble_logits: list logits từ các model khác (để tính ensemble
            disagreement). Nếu None, bỏ qua ensemble score.
        energy_temperature: T riêng cho energy score
        confidence_temperature: T temperature-scaling của model (từ
            calibration.py). Nếu truyền, MSP/Entropy tính trên
            softmax(logits/T) — confidence đã hiệu chỉnh, giúp mọi model
            nằm trên cùng thang tin cậy khi so với gate. Ensemble
            disagreement VẪN tính trên raw logits (T calibrate cho ID
            không giúp bắt OOD — ODIN, Liang et al. 2018).

    Returns:
        dict với keys: msp, entropy, energy, (ensemble_disagreement nếu có)
    """
    if confidence_temperature is not None and confidence_temperature > 0:
        logits_conf = logits / confidence_temperature
    else:
        logits_conf = logits

    scores = {
        "msp": compute_msp(logits_conf),
        "entropy": compute_entropy(logits_conf),
        "energy": compute_energy(logits, temperature=energy_temperature),
    }

    if ensemble_logits:
        all_logits = [logits] + ensemble_logits  # raw logits — giữ nguyên cho disagreement
        scores["ensemble_disagreement"] = compute_ensemble_disagreement(all_logits)

    return scores


# --------------------------------------------------------------------------- #
# Cấu hình tier (Basic / Standard / Advanced) — dùng chung cho evaluate_ood.py
# (calibrate ngưỡng) và predict.py (inference 2 tầng).
# Primary của mọi tier là model ĐẦU TIÊN (EfficientNet-B0); các model còn lại
# chỉ được lazy-load khi ảnh rơi vào "vùng lửng" MSP (0.5 – 0.99).
# --------------------------------------------------------------------------- #
TIER_MODELS = {
    "basic": {
        "efficientnet_b0": "efficientnet_b0_f",
    },
    "standard": {
        "efficientnet_b0": "efficientnet_b0_f",
        "mobilenet_v2": "mobilenet_v2_f",
    },
    "advanced": {
        "efficientnet_b0": "efficientnet_b0_f",
        "mobilenet_v2": "mobilenet_v2_f",
        "resnet50": "resnet50_f",
    },
}

# Ngưỡng MSP cho logic 2 tầng:
#   - MSP >= HIGH_CONF_MSP : model rất tự tin -> chấp nhận ngay, không chạy ensemble
#   - MSP <  LOW_CONF_MSP  : model quá phân vân -> loại ngay, không chạy ensemble
#   - còn lại ("vùng lửng") -> lazy load model phụ, tính ensemble disagreement
HIGH_CONF_MSP = 0.99
LOW_CONF_MSP = 0.5
