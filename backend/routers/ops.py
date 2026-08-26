"""
장애 주입 및 AIOps 테스트/운영자 챗봇 라우터 - TVING
CloudWatch 메트릭/로그 발생 및 AIOps Bedrock 기반 지능형 운영 진단 API
"""
import os
import json
import time
import boto3
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from config import AWS_REGION, BEDROCK_MODEL_ID

router = APIRouter()

# Bedrock Runtime 클라이언트
try:
    bedrock_client = boto3.client(
        service_name="bedrock-runtime",
        region_name=AWS_REGION
    )
except Exception:
    bedrock_client = None

# CloudWatch 클라이언트
try:
    cw_client = boto3.client("cloudwatch", region_name=AWS_REGION)
except Exception:
    cw_client = None


class OpsChatRequest(BaseModel):
    message: str
    include_metrics: Optional[bool] = True


@router.get("/status")
def ops_status():
    """AIOps 모니터링 상태 확인"""
    return {
        "status": "ok",
        "service": "tving-backend",
        "region": AWS_REGION,
        "bedrock_model": BEDROCK_MODEL_ID,
        "timestamp": time.time()
    }


@router.get("/metrics")
def get_ops_metrics(db: Session = Depends(get_db)):
    """AIOps 대시보드용 실시간 인프라 헬스 메트릭"""
    db_status = "healthy"
    db_latency_ms = 0.0
    try:
        t0 = time.time()
        db.execute(text("SELECT 1;"))
        db_latency_ms = round((time.time() - t0) * 1000, 2)
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S KST", time.localtime()),
        "ecs": {
            "cluster": "tving-cluster",
            "service": "tving-backend-service",
            "status": "ACTIVE",
            "task_definition": "tving-backend-task:4"
        },
        "database": {
            "engine": "PostgreSQL 16",
            "status": db_status,
            "latency_ms": db_latency_ms
        },
        "aiops_engine": {
            "bedrock_status": "ONLINE" if bedrock_client else "OFFLINE",
            "model": BEDROCK_MODEL_ID,
            "region": AWS_REGION
        }
    }


@router.post("/ai-chat")
def ops_ai_chat(request: OpsChatRequest, db: Session = Depends(get_db)):
    """
    운영자 전용 AIOps 대화형 장애 진단 및 모니터링 AI 챗봇 (Amazon Bedrock)
    """
    user_query = request.message

    # 실시간 인프라 컨텍스트 수집
    db_ok = True
    db_latency = 0.0
    try:
        t0 = time.time()
        db.execute(text("SELECT 1;"))
        db_latency = round((time.time() - t0) * 1000, 2)
    except Exception:
        db_ok = False

    infra_context = f"""
[실시간 TVING 클라우드 인프라 상태]
- 대상 서비스: TVING OTT 플랫폼 (user6.cloudai.store)
- 리전: AWS Asia Pacific (Seoul, ap-northeast-2)
- ECS Cluster: tving-cluster | Service: tving-backend-service (ECS Fargate)
- RDS PostgreSQL: tving-postgres (Status: {'HEALTHY' if db_ok else 'UNHEALTHY'}, Latency: {db_latency}ms)
- Internal ALB: tving-internal-alb (Target Group: tving-backend-tg:8000, tving-streamlit-tg:8501)
- CDN/DNS: CloudFront (E1D9AUK8PXTXMF) + Route 53 (user6.cloudai.store, ops.user6.cloudai.store)
- AI 모니터링: CloudWatch Anomaly Detection (CPU / Memory ±2σ Band) + Amazon Bedrock SecOps/SRE Engine
"""

    system_prompt = f"""당신은 TVING OTT 클라우드 인프라를 총괄하는 전문 SRE/SecOps AIOps 지능형 운영자 어시스턴트입니다.
운영자의 장애 진단, 시스템 상태 질문, 원인 분석 요청에 대해 정확하고 신속하며 전문적인 엔지니어링 가이드를 제공하세요.

답변 가이드라인:
1. 항상 마크다운 형식으로 깔끔하게 정리하여 답변하세요.
2. 실시간 인프라 지표와 연계하여 진단 근거(Evidence)와 긴급 조치사항(Action Items)을 명확히 제시하세요.
3. CPU 과부하, 슬로우 쿼리, 보안 침해 이상 징후 발생 시 SRE/SOAR 자율 대응 플레이북 절차를 안내하세요.

{infra_context}
"""

    if not bedrock_client:
        return {
            "reply": f"🤖 [AIOps Mock Agent]\n\n현재 시스템 상태는 정상입니다.\n- DB 상태: {'정상' if db_ok else '오류'}\n- 지연 시간: {db_latency}ms\n- 질의: {user_query}",
            "model": "local-fallback"
        }

    try:
        converse_response = bedrock_client.converse(
            modelId=BEDROCK_MODEL_ID,
            messages=[
                {
                    "role": "user",
                    "content": [{"text": user_query}]
                }
            ],
            system=[{"text": system_prompt}],
            inferenceConfig={
                "maxTokens": 1024,
                "temperature": 0.3,
                "topP": 0.9
            }
        )
        reply = converse_response["output"]["message"]["content"][0]["text"]
        return {
            "reply": reply,
            "model": BEDROCK_MODEL_ID,
            "status": "success"
        }
    except Exception as e:
        return {
            "reply": f"AIOps 진단 엔진 분석 중 오류 발생: {str(e)}",
            "model": BEDROCK_MODEL_ID,
            "status": "error"
        }


@router.post("/cpu-load")
def trigger_cpu_load(duration: int = 5):
    """
    [AIOps 테스트] 인위적 CPU 부하 발생
    CloudWatch CPUUtilization 메트릭 급증 유발
    """
    start_time = time.time()
    count = 0
    while time.time() - start_time < min(duration, 15):
        for i in range(1000000):
            count += i * i

    return {
        "status": "completed",
        "message": f"{duration}초간 CPU 부하 테스트를 수행했습니다.",
        "duration_seconds": round(time.time() - start_time, 2)
    }


@router.post("/delay")
def trigger_delay(seconds: int = 3):
    """
    [AIOps 테스트] 인위적 응답 지연 발생
    ALB TargetResponseTime 지연 유발
    """
    sleep_time = min(seconds, 10)
    time.sleep(sleep_time)
    return {
        "status": "completed",
        "message": f"{sleep_time}초간 응답을 지연시켰습니다."
    }


@router.post("/db-error")
def trigger_db_error(db: Session = Depends(get_db)):
    """
    [AIOps 테스트] DB Connection/Query 에러 강제 발생
    CloudWatch Logs에 500 에러 및 Traceback 기록 유발
    """
    try:
        db.execute(text("SELECT * FROM non_existent_tving_table_error_trigger;"))
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database operational error triggered for AIOps: {str(e)}"
        )

