"""
Debug gate_scale — kiem tra RAW vs CALIBRATED gate thuc te dung gia tri nao.
Chay: py debug_gate.py   (tu thu muc ml/)
"""
import sys
from pathlib import Path

# cho phep import predict.py tu thu muc src/
sys.path.insert(0, str(Path(__file__).parent / "src"))

import torch
from predict import load_predictor

print("=" * 70)
print("DEBUG GATE SCALE - standard tier")
print("=" * 70)

p_raw = load_predictor(tier="standard", gate_scale="raw")
p_cal = load_predictor(tier="standard", gate_scale="calibrated")

print("\n--- PREDICTOR RAW ---")
print("gate_scale     :", p_raw.gate_scale)
print("temperature    :", p_raw.temperature, "(da load tu file - KHONG dung cho gate khi raw)")
print("high_conf_msp  :", p_raw.high_conf_msp, "(ky vong 0.99 - KHONG bi JSON ghi de)")
print("low_conf_msp   :", p_raw.low_conf_msp, "(ky vong 0.5)")
print("ood_threshold  :", p_raw.ood_threshold)

print("\n--- PREDICTOR CALIBRATED ---")
print("gate_scale     :", p_cal.gate_scale)
print("temperature    :", p_cal.temperature, "(dung cho gate khi calibrated)")
print("high_conf_msp  :", p_cal.high_conf_msp, "(ky vong 0.9852 - tu ood_threshold.json)")
print("low_conf_msp   :", p_cal.low_conf_msp, "(ky vong 0.5085)")
print("ood_threshold  :", p_cal.ood_threshold, "(ky vong 0.0215 - giong raw, vi disagreement la raw)")

print("\n--- MO PHONG DUNG DONG GATE TRONG predict_single ---")
fake_logits = torch.tensor([[5.0, 1.2, 0.3, 0.1]])  # logits gia (1 anh)
print("logits gia     :", fake_logits.tolist())

# Dung y het cong thuc trong predict_single:
gate_T_raw = p_raw.temperature if p_raw.gate_scale == "calibrated" else 1.0
gate_T_cal = p_cal.temperature if p_cal.gate_scale == "calibrated" else 1.0
print("gate_temperature RAW        :", gate_T_raw)
print("gate_temperature CALIBRATED :", gate_T_cal)

msp_raw = torch.softmax(fake_logits / gate_T_raw, dim=1)[0].max().item()
msp_cal = torch.softmax(fake_logits / gate_T_cal, dim=1)[0].max().item()
print(f"MSP gate RAW        : {msp_raw:.4f}  -> so voi high={p_raw.high_conf_msp}")
print(f"MSP gate CALIBRATED : {msp_cal:.4f}  -> so voi high={p_cal.high_conf_msp}")

print("\nKET LUAN:")
ok = True
if p_raw.gate_scale == "raw" and abs(p_raw.high_conf_msp - 0.99) < 1e-9:
    print("  [OK] raw mode: gate KHONG bi JSON ghi de, gate_temperature = 1.0")
else:
    ok = False
    print("  [BUG] raw mode bi ghi de hoac gate sai - kiem tra __init__ / predict_single")
if p_cal.high_conf_msp is not None and abs(p_cal.high_conf_msp - 0.9852286577224731) < 0.001:
    print("  [OK] calibrated mode: gate = 0.9852 (p90 calibrated tu JSON), gate_temperature = T primary")
else:
    ok = False
    print("  [BUG] calibrated mode: gate khong khop JSON - kiem tra lai")
print("\nTONG KET:", "HE THONG DUNG" if ok else "CO BUG - XEM BEN TREN")
