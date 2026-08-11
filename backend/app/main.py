from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import predict

app = FastAPI(title="Plant Disease Detection API")

# Cho phép frontend React (chạy ở port khác) gọi API — nới lỏng cho môi trường dev.
# Khi deploy thật, nên giới hạn allow_origins về đúng domain frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict.router, prefix="/api")


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Plant Disease Detection API đang chạy"}
