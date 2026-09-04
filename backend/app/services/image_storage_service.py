"""Kiểm tra upload ảnh và quản lý file ảnh lưu cục bộ."""

from dataclasses import dataclass
import io
import os
from pathlib import Path
from uuid import uuid4
import warnings

from fastapi import UploadFile, status
from PIL import Image, UnidentifiedImageError

from app.core.config import BASE_DIR, settings


_FORMAT_CONFIG = {
    "JPEG": (".jpg", {"image/jpeg", "image/jpg"}),
    "PNG": (".png", {"image/png"}),
}


class UploadValidationError(Exception):
    """Lỗi upload có HTTP status/detail an toàn để trả cho client."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


@dataclass(frozen=True)
class ValidatedImage:
    """Ảnh đã qua kiểm tra byte, định dạng và kích thước."""

    data: bytes
    extension: str
    mime_type: str
    width: int
    height: int


async def validate_upload(file: UploadFile) -> ValidatedImage:
    """Đọc upload có giới hạn và xác thực MIME bằng nội dung ảnh thật."""
    claimed_mime = (file.content_type or "").lower().split(";", 1)[0]
    allowed_mimes = {
        mime for _, mime_set in _FORMAT_CONFIG.values() for mime in mime_set
    }
    if claimed_mime not in allowed_mimes:
        raise UploadValidationError(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Chỉ hỗ trợ ảnh JPEG hoặc PNG.",
        )

    data = bytearray()
    while chunk := await file.read(1024 * 1024):
        data.extend(chunk)
        if len(data) > settings.MAX_UPLOAD_BYTES:
            raise UploadValidationError(
                status.HTTP_413_CONTENT_TOO_LARGE,
                f"Ảnh vượt quá giới hạn {settings.MAX_UPLOAD_BYTES} byte.",
            )
    if not data:
        raise UploadValidationError(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "File ảnh rỗng.",
        )

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as image:
                image_format = image.format
                width, height = image.size
                image.verify()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError,
            Image.DecompressionBombWarning) as exc:
        raise UploadValidationError(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "File không phải ảnh hợp lệ hoặc đã bị hỏng.",
        ) from exc

    if image_format not in _FORMAT_CONFIG:
        raise UploadValidationError(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Định dạng ảnh thực tế không được hỗ trợ.",
        )
    extension, actual_mimes = _FORMAT_CONFIG[image_format]
    if claimed_mime not in actual_mimes:
        raise UploadValidationError(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Content-Type không khớp định dạng ảnh thực tế.",
        )
    if width <= 0 or height <= 0 or width * height > settings.MAX_IMAGE_PIXELS:
        raise UploadValidationError(
            status.HTTP_413_CONTENT_TOO_LARGE,
            "Kích thước pixel của ảnh vượt quá giới hạn cho phép.",
        )

    return ValidatedImage(
        data=bytes(data),
        extension=extension,
        mime_type=claimed_mime,
        width=width,
        height=height,
    )


def save_image(image: ValidatedImage) -> str:
    """Ghi ảnh atomically và trả về đường dẫn tương đối lưu trong DB."""
    upload_dir = Path(settings.UPLOAD_DIR).resolve()
    upload_dir.mkdir(parents=True, exist_ok=True)
    target = upload_dir / f"{uuid4().hex}{image.extension}"
    temporary = target.with_suffix(f"{target.suffix}.tmp")
    try:
        temporary.write_bytes(image.data)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    # DB chỉ lưu logical path, không làm lộ đường dẫn filesystem của server.
    return f"storage/uploads/{target.name}"


def delete_stored_image(image_path: str) -> bool:
    """Chỉ xóa file nằm bên trong UPLOAD_DIR; từ chối path traversal."""
    upload_dir = Path(settings.UPLOAD_DIR).resolve()
    candidate = Path(image_path)
    normalized = image_path.replace("\\", "/")
    prefix = "storage/uploads/"
    if normalized.startswith(prefix):
        candidate = upload_dir / normalized.removeprefix(prefix)
    elif not candidate.is_absolute():
        candidate = BASE_DIR / candidate
    target = candidate.resolve()
    if not target.is_relative_to(upload_dir) or not target.is_file():
        return False
    target.unlink()
    return True
