# Hướng dẫn Train Model trên Google Colab

## Tổng quan
Google Colab cung cấp GPU miễn phí để train model nhanh hơn so với CPU local.

## Bước 1: Chuẩn bị dữ liệu

### Option A: Upload dữ liệu lên Google Drive
1. Upload folder `data/` (chứa ảnh gốc) lên Google Drive
2. Upload folder `ml/` (code ML) lên Google Drive
3. **Nếu train nhiều model type khác nhau**: copy folder `ml/` thành `ml_resnet50/`, `ml_efficientnet/`, v.v.

### Option B: Clone từ GitHub (nếu code đã push)
```bash
!git clone https://github.com/your-username/plant-disease-detection.git
%cd plant-disease-detection/ml
```

## Bước 2: Mount Google Drive (nếu dùng Option A)

```python
from google.colab import drive
drive.mount('/content/drive')
```

Sau khi mount, đường dẫn sẽ là:
- `/content/drive/MyDrive/data/` - dữ liệu ảnh (chung cho tất cả models)
- `/content/drive/MyDrive/ml/` - code ML cho model 1 (ví dụ: MobileNetV2)
- `/content/drive/MyDrive/ml1/` - code ML cho model 2 (ví dụ: ResNet50)
- `/content/drive/MyDrive/ml2/` - code ML cho model 3 (ví dụ: EfficientNet)

## Bước 3: Cài đặt dependencies

```bash
# Đổi đường dẫn theo folder bạn đang dùng (ml, ml1, ml2, v.v.)
%cd /content/drive/MyDrive/ml1  # hoặc ml, ml2, v.v.
!pip install torch torchvision Pillow pyyaml tqdm scikit-learn opencv-python
```

## Bước 4: Chọn GPU

```python
import torch
print(f"GPU available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU name: {torch.cuda.get_device_name(0)}")
```

Nếu GPU không available: Runtime → Change runtime type → T4 GPU

## Bước 5: Cấu hình model type

Mở file `configs/config.yaml` trong folder đang dùng (ml, ml1, ml2) và đổi `model_type`:

```yaml
train:
  model_type: resnet50  # hoặc efficientnet_b0, mobilenet_v2
```

Hoặc chỉnh trực tiếp trong code:

```python
import yaml
with open('configs/config.yaml', 'r') as f:
    cfg = yaml.safe_load(f)
cfg['train']['model_type'] = 'resnet50'  # Đổi theo folder đang dùng
with open('configs/config.yaml', 'w') as f:
    yaml.dump(cfg, f)
```

**Lưu ý**: Mỗi folder (ml, ml1, ml2) có thể có `model_type` khác nhau trong config.yaml của nó.

## Bước 6: Chạy split dữ liệu (nếu chưa split)

```bash
!python src/data_split.py
```

**Lưu ý**: Chỉ cần chạy split 1 lần. Folder `data/split/` có thể dùng chung cho tất cả models (ml, ml1, ml2). Trong config.yaml của từng folder, trỏ về cùng đường dẫn `data/split/`.

## Bước 7: Train model

```bash
!python src/train.py
```

Model sẽ được lưu tại `models/best_model.pt`, `models/classes.json`, `models/model_type.json` trong folder đang dùng (ml, ml1, ml2).

## Bước 8: Evaluate model

```bash
!python src/evaluate.py
```

## Bước 9: Tải model về máy

### Option A: Download trực tiếp từ Colab
```python
from google.colab import files
files.download('models/best_model.pt')
files.download('models/classes.json')
files.download('models/model_type.json')
```

### Option B: Copy về Google Drive rồi download từ Drive
```bash
# Đổi tên file để tránh ghi đè khi train nhiều model
!cp models/best_model.pt /content/drive/MyDrive/best_model_resnet50.pt
!cp models/classes.json /content/drive/MyDrive/classes_resnet50.json
!cp models/model_type.json /content/drive/MyDrive/model_type_resnet50.json
```

## Bước 10: Copy model về backend local

Sau khi tải về máy, copy vào `backend/app/models/` với tên phù hợp:

```powershell
# Windows - đổi tên theo model type
copy best_model_resnet50.pt d:\QLPM\plant-disease-detection\backend\app\models\best_model.pt
copy classes_resnet50.json d:\QLPM\plant-disease-detection\backend\app\models\classes.json
copy model_type_resnet50.json d:\QLPM\plant-disease-detection\backend\app\models\model_type.json
```

## Bước 11: Test GradCAM với model mới

```bash
cd ml  # hoặc folder tương ứng
py src/gradcam.py --image "path/to/test/image.jpg" --output "heatmap.png"
```

## Tips quan trọng

1. **GPU T4 miễn phí** - đủ để train ResNet50/EfficientNet
2. **Session timeout** - Colab sẽ disconnect sau 90 phút không hoạt động
3. **Save checkpoint** - model tự động lưu best model, không cần lo mất progress
4. **Memory** - nếu OOM, giảm `batch_size` trong config.yaml
5. **Data location** - để data trên Drive để không bị mất khi session disconnect

## Troubleshooting

### Lỗi CUDA out of memory
Giảm `batch_size` trong `config.yaml` (từ 32 → 16 hoặc 8)

### Lỗi không tìm thấy data
Kiểm tra đường dẫn trong `config.yaml` có đúng với vị trí data trên Colab không

### Lỗi session disconnect
- Model đã được lưu, chỉ cần mount Drive lại và chạy tiếp
- Không cần train lại từ đầu
