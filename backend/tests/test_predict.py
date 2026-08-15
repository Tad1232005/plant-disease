import io
from PIL import Image


def create_dummy_image():
    file = io.BytesIO()
    image = Image.new("RGB", (224, 224), color="green")
    image.save(file, "jpeg")
    file.seek(0)
    return file


def test_predict_invalid_file_type(client):
    files = {"file": ("document.txt", b"Test data", "text/plain")}
    response = client.post("/api/v1/predict", files=files)
    assert response.status_code == 400


def test_predict_success(client):
    dummy_img = create_dummy_image()
    files = {"file": ("leaf.jpg", dummy_img, "image/jpeg")}
    response = client.post("/api/v1/predict", files=files)
    
    if response.status_code == 200:
        data = response.json()
        assert "label" in data
        assert "top_k" in data
        assert len(data["top_k"]) > 0