"""
장애 주입 및 AIOps 테스트 라우터 - TVING
CloudWatch 메트릭/로그 발생 및 AIOps 대응 검증용 API
"""
import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db

router = APIRouter()


@router.get("/status")
def ops_status():
    """AIOps 모니터링 상태 확인"""
    return {"status": "ok", "service": "tving-backend", "timestamp": time.time()}


@router.post("/cpu-load")
def trigger_cpu_load(duration: int = 5):
    """
    [AIOps 테스트] 인위적 CPU 부하 발생
    CloudWatch CPUUtilization 메트릭 급증 유발
    """
    start_time = time.time()
    # 인위적 CPU 계산 루프
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
        # 존재하지 않는 테이블 조회로 강제 SQL 에러 유발
        db.execute(text("SELECT * FROM non_existent_tving_table_error_trigger;"))
        db.commit()
    except Exception as e:
        db.rollback()
        # 500 에러 발생시켜 CloudWatch에 ERROR 로그 남김
        raise HTTPException(
            status_code=500,
            detail=f"Database operational error triggered for AIOps: {str(e)}"
        )
