import io

import torch
import torch.nn.functional as F
from fastapi import APIRouter, UploadFile, File, HTTPException
from PIL import Image
from torchvision import transforms

from app.model_loader import load_model, DEVICE
from app.schemas import PredictResponse

router = APIRouter()

# Load model 1 lần khi server khởi động (không load lại mỗi request)
model, classes = load_model()

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                          std=[0.229, 0.224, 0.225]),
])


@router.post("/predict", response_model=PredictResponse)
async def predict(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File phải là ảnh (jpg/png).")

    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Không đọc được ảnh, vui lòng thử ảnh khác.")

    input_tensor = transform(image).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        outputs = model(input_tensor)
        probs = F.softmax(outputs, dim=1)[0]
        confidence, pred_idx = torch.max(probs, dim=0)

    return PredictResponse(
        label=classes[pred_idx.item()],
        confidence=round(confidence.item(), 4),
    )
