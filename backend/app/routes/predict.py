import io

from fastapi import APIRouter, File, HTTPException, UploadFile

try:
    from PIL import Image
    import torch
    import torch.nn.functional as F
    from torchvision import transforms
except ModuleNotFoundError:  # pragma: no cover - optional for auth-only setups
    Image = None
    torch = None
    F = None
    transforms = None

try:
    from app.model_loader import DEVICE, load_model
except ModuleNotFoundError:  # pragma: no cover - optional for auth-only setups
    DEVICE = None
    load_model = None

from app.schemas import PredictResponse

router = APIRouter()

if transforms is not None:
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
else:
    transform = None


@router.post("/predict", response_model=PredictResponse)
async def predict(file: UploadFile = File(...)):
    if torch is None or F is None or transform is None or Image is None or load_model is None:
        raise HTTPException(status_code=503, detail="ML dependencies are not installed.")

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File phải là ảnh (jpg/png).")

    try:
        model, classes = load_model()
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Không đọc được ảnh, vui lòng thử ảnh khác.") from exc

    input_tensor = transform(image).unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        outputs = model(input_tensor)
        probs = F.softmax(outputs, dim=1)[0]
        confidence, pred_idx = torch.max(probs, dim=0)

    return PredictResponse(
        label=classes[pred_idx.item()],
        confidence=round(confidence.item(), 4),
    )
