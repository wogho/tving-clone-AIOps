import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from routers import auth, items, chat, ops, testops

# 로거 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tving.access")

app = FastAPI(
    title="TVING 클론 API",
    description="CJ AI 클라우드 엔지니어 부트캠프 - TVING 클론 백엔드 API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_client_requests(request: Request, call_next):
    start_time = time.time()
    
    # 💡 1. 쿼리 파라미터 client_ip 최우선 확인 (k6 가상 IP 완벽 지원)
    client_ip = (
        request.query_params.get("client_ip") or
        request.headers.get("x-client-ip") or
        request.headers.get("x-user-ip") or
        request.headers.get("x-custom-ip") or
        (request.headers.get("x-forwarded-for", "").split(",")[0].strip() if request.headers.get("x-forwarded-for") else None) or
        (request.client.host if request.client else "unknown")
    )
        
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    # 💡 CloudWatch 및 AIOps 하네스가 즉시 파싱할 수 있는 표준 로그 포맷
    logger.info(
        f"[CLIENT_IP: {client_ip}] {request.method} {request.url.path} "
        f"status={response.status_code} latency={process_time:.1f}ms"
    )
    return response

app.include_router(auth.router, prefix="/api/auth", tags=["인증"])
app.include_router(items.router, prefix="/api", tags=["콘텐츠/찜/시청기록"])
app.include_router(chat.router, prefix="/api", tags=["AI 챗봇"])
app.include_router(ops.router, prefix="/api/ops", tags=["AIOps 테스트"])
app.include_router(ops.router, prefix="/ops", tags=["AIOps 테스트"])
app.include_router(testops.router, prefix="/api/testops", tags=["Strands TestOps"])
app.include_router(testops.router, prefix="/testops", tags=["Strands TestOps"])

@app.get("/")
def root():
    return {"message": "TVING 클론 API 서버가 실행 중입니다!", "docs": "/docs"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
