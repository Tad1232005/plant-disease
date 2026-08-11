# ML — Train model nhận diện bệnh lá cây

## 1. Setup môi trường
```bash
cd ml
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Tải dataset PlantVillage
```bash
Dataset được sử dụng:

https://huggingface.co/datasets/mohanty/PlantVillage

Dataset có configuration `color`, chứa ảnh RGB gốc. Dataset cũng cung cấp
`leaf_id`, dùng để đảm bảo các ảnh của cùng một lá không bị chia vào
nhiều tập dữ liệu khác nhau. Điều này giúp tránh data leakage khi train/test. 

Cài dependencies:

```bash
cd ml
pip install -r requirements.txt
```

## 3. Lọc ra các lớp bệnh trong phạm vi đồ án
Mở `ml/src/download_dataset.py`, chỉnh danh sách `TARGET_CLASSES` theo scope nhóm đã chốt
(mặc định đang để sẵn 5 bệnh cà chua + khỏe mạnh làm ví dụ), sau đó chạy:
```bash
python ml/src/download_dataset.py
```
Kết quả nằm ở `ml/data/filtered/` — nhẹ hơn dataset gốc, có thể nén và up lên Google Drive/Kaggle
để chia sẻ cho các bạn còn lại (không push dataset lên GitHub).

## 4. Chia tập train/val/test (70/15/15)
> TODO: viết script `split_dataset.py` ở tuần 2 (phần EDA) — chia theo nguồn ảnh để tránh rò rỉ dữ liệu.
Sau khi chia xong, dữ liệu cần có cấu trúc:
```
ml/data/split/
├── train/<class_name>/*.jpg
├── val/<class_name>/*.jpg
└── test/<class_name>/*.jpg
```

## 5. Train model
```bash
python ml/src/train.py
```
Model tốt nhất sẽ được lưu tại `ml/models/best_model.pt`, kèm `ml/models/classes.json`
(danh sách tên lớp theo đúng thứ tự index để backend dùng khi predict).

## 6. Đánh giá model
```bash
python ml/src/evaluate.py
```
In ra classification report (precision/recall/f1 từng lớp) và lưu confusion matrix.

## 7. Đưa model sang backend
Copy 2 file sau vào `backend/app/models/`:
- `ml/models/best_model.pt`
- `ml/models/classes.json`
