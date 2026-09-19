FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
# CPU deployment: avoid pulling multi-GB CUDA libraries from the default torch wheel.
# Keep these versions aligned with requirements.txt; GPU deployment is a separate image.
RUN pip install --no-cache-dir torch==2.13.0+cpu torchvision==0.28.0+cpu --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt \
    && pip check

COPY . .

RUN groupadd --gid 10001 plant && useradd --uid 10001 --gid plant --no-create-home plant \
    && mkdir -p /app/storage/uploads /app/storage/gradcam \
    && chown -R plant:plant /app/storage

USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/ready', timeout=8).close()"

# No migrations/seeds on startup. Enable proxy headers only with explicit trusted proxies.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-proxy-headers", "--no-access-log"]
