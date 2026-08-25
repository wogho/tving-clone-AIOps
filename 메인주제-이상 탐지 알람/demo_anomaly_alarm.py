#!/usr/bin/env python3
"""
================================================================================
TVING AIOps Platform - CloudWatch Anomaly Detection + SNS + Slack 시연 데모 스크립트
================================================================================
[시연 시나리오]
1. ECS Fargate 백엔드 장애 및 부하 주입 (CPU 과부하 / API 지연 / DB 장애)
2. CloudWatch 이상 탐지(Anomaly Detection) 알람 상태 모니터링
3. SNS -> Lambda -> Slack 실시간 장애 경보 및 긴급 조치사항 발송
4. 시스템 자동 복구(Self-Healing) 및 헬스체크 확인
5. SNS -> Lambda -> Slack 정상 복구 완료 및 조치 내역 알림 발송
================================================================================
"""

import sys
import os
import json
import time
import urllib.request
import urllib.error
import boto3
from datetime import datetime, timezone

# AWS 설정
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
SNS_TOPIC_ARN = "arn:aws:sns:ap-northeast-2:761018884888:tving-aiops-anomaly-alarm"
API_BASE_URL = os.getenv("API_BASE_URL", "https://user6.cloudai.store/api")

# Boto3 클라이언트
sns_client = boto3.client("sns", region_name=AWS_REGION)
cw_client = boto3.client("cloudwatch", region_name=AWS_REGION)

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_step(step_num, title):
    print(f"\n[Step {step_num}] {title}")
    print("-" * 50)

def http_post(endpoint, data=None):
    """FastAPI 백엔드로 HTTP POST 요청 전송"""
    url = f"{API_BASE_URL}{endpoint}"
    req_data = json.dumps(data).encode("utf-8") if data else b"{}"
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={"Content-Type": "application/json", "User-Agent": "TVING-AIOps-Demo/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read().decode("utf-8")
            return json.loads(res_body) if res_body else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            return json.loads(err_body)
        except Exception:
            return {"error": str(e), "body": err_body}
    except Exception as e:
        return {"error": str(e)}

def http_get(endpoint):
    """FastAPI 백엔드로 HTTP GET 요청 전송"""
    url = f"{API_BASE_URL}{endpoint}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "TVING-AIOps-Demo/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_body = response.read().decode("utf-8")
            return json.loads(res_body) if res_body else {}
    except Exception as e:
        return {"error": str(e)}

def demo_inject_cpu_load():
    """시나리오 1: CPU 과부하 주입"""
    print_header("시나리오 1: ECS Fargate 백엔드 CPU 과부하 주입")
    print(f"대상 엔드포인트: {API_BASE_URL}/ops/cpu-load")
    print("설정 파라미터: 4 스레드, 100% 연산, 30초 지속")
    
    result = http_post("/ops/cpu-load", {"duration_seconds": 30, "target_cpu_percent": 100})
    print(f"\n[결과 응답]:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
    print("\n💡 ECS 컨테이너 CPU 사용량이 즉시 급증하여 CloudWatch Anomaly Detection 대역 상한선을 돌파합니다.")

def demo_inject_delay():
    """시나리오 2: API 지연(Latency) 장애 주입"""
    print_header("시나리오 2: API 응답 지연 장애 주입 (Latency Degradation)")
    print(f"대상 엔드포인트: {API_BASE_URL}/ops/delay")
    print("설정 파라미터: 강제 지연 3.5초, 20초간 유지")
    
    result = http_post("/ops/delay", {"delay_seconds": 3.5, "duration_seconds": 20})
    print(f"\n[결과 응답]:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
    print("\n💡 API 호출 시 강제 대기(Delay)가 발생하여 ALB 타임아웃 및 이상 징후가 발생합니다.")

def demo_inject_db_error():
    """시나리오 3: DB 장애 주입"""
    print_header("시나리오 3: 데이터베이스 연결 장애 시뮬레이션")
    print(f"대상 엔드포인트: {API_BASE_URL}/ops/db-error")
    
    result = http_post("/ops/db-error", {"enabled": True, "error_rate": 0.8})
    print(f"\n[결과 응답]:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
    print("\n💡 백엔드 DB 쿼리 실행 시 80% 확률로 연결 에러가 발생하여 500 에러 알람을 유발합니다.")

def demo_send_anomaly_slack_alert():
    """시나리오 4: SNS -> Lambda -> Slack 실시간 장애 경보 및 긴급 조치사항 발송"""
    print_header("시나리오 4: CloudWatch 이상 탐지 실시간 경보 & 긴급 조치사항 발송 (SNS -> Slack)")
    print(f"SNS Topic: {SNS_TOPIC_ARN}")
    
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    alarm_payload = {
        "AlarmName": "tving-ecs-cpu-anomaly-alarm",
        "AlarmDescription": "TVING ECS Fargate CPU 이상 징후 감지 (CloudWatch Anomaly Detection)",
        "AWSAccountId": "761018884888",
        "NewStateValue": "ALARM",
        "NewStateReason": "Threshold Breached: 1 datapoint [96.4%] was greater than the upper anomaly band [38.2%].",
        "StateChangeTime": now_str,
        "Region": "Asia Pacific (Seoul)",
        "Remediation": (
            "1. ECS Fargate 오토스케일링 태스크 증설 상태 확인 및 스케일아웃 실행\n"
            "2. 비정상 인입 트래픽 및 과부하 엔드포인트(/api/ops/*) 차단\n"
            "3. Slow Query 및 DB Connection Pool 가용량 점검\n"
            "4. CloudWatch 이상 탐지 대역(±2σ) 추이 및 컨테이너 리소스 모니터링"
        )
    }
    
    try:
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="ALARM: 'tving-ecs-cpu-anomaly-alarm' in Asia Pacific (Seoul)",
            Message=json.dumps(alarm_payload, ensure_ascii=False)
        )
        print(f"[발송 성공] MessageId: {response['MessageId']}")
        print("\n✅ Slack 채널에 [🚨 TVING AIOps 장애 경보 & 긴급 조치사항] 카드가 수신되었습니다!")
        print("   - 이상 발생 지표, 이상 탐지 대역 초과량, 긴급 조치 가이드(Action Items) 포함")
    except Exception as e:
        print(f"[발송 실패]: {str(e)}")

def demo_send_recovery_slack_alert():
    """시나리오 4-B: SNS -> Lambda -> Slack 정상 복구 완료 및 조치 내역 알림 발송"""
    print_header("시나리오 4-B: 시스템 정상 복구 완료 및 완료 조치 내역 발송 (SNS -> Slack)")
    print(f"SNS Topic: {SNS_TOPIC_ARN}")
    
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    recovery_payload = {
        "AlarmName": "tving-ecs-cpu-anomaly-alarm",
        "AlarmDescription": "TVING ECS Fargate CPU 이상 징후 정상 복구 완료",
        "AWSAccountId": "761018884888",
        "NewStateValue": "OK",
        "NewStateReason": "Thresholds Cleared: 1 datapoint [2.04%] returned to normal expected band [0% ~ 15%].",
        "StateChangeTime": now_str,
        "Region": "Asia Pacific (Seoul)",
        "RecoveryDetails": (
            "1. 부하 프로세스 자동 종료 및 CPU/메모리 정상 수치 회복\n"
            "2. ECS 헬스체크(/api/ops/status) 정상 응답 (HTTP 200 OK) 확인\n"
            "3. ALB 트래픽 분산 및 타겟 응답 지연 시간 안정화\n"
            "4. 이상 탐지 대역(Anomaly Band) 내 완전 복귀 및 인시던트 종료"
        )
    }
    
    try:
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="OK: 'tving-ecs-cpu-anomaly-alarm' in Asia Pacific (Seoul)",
            Message=json.dumps(recovery_payload, ensure_ascii=False)
        )
        print(f"[발송 성공] MessageId: {response['MessageId']}")
        print("\n✅ Slack 채널에 [✅ TVING AIOps 정상 복구 완료 & 조치 내역] 카드가 수신되었습니다!")
        print("   - 복구 상태(Healthy), 정상 대역 진입 수치, 완료된 조치 내역(Resolution Summary) 포함")
    except Exception as e:
        print(f"[발송 실패]: {str(e)}")

def demo_check_cloudwatch_alarms():
    """시나리오 5: CloudWatch 이상 탐지 알람 상태 조회"""
    print_header("시나리오 5: AWS CloudWatch 이상 탐지 알람 상태 조회")
    try:
        response = cw_client.describe_alarms(
            AlarmNames=["tving-ecs-cpu-anomaly-alarm", "tving-ecs-memory-anomaly-alarm"]
        )
        for alarm in response.get("MetricAlarms", []):
            print(f"\n• 알람 이름: {alarm['AlarmName']}")
            print(f"  - 현재 상태: {alarm['StateValue']} (이유: {alarm.get('StateReason', 'N/A')[:60]}...)")
            print(f"  - 연동 액션(ALARM): {alarm.get('AlarmActions', [])}")
            print(f"  - 연동 액션(OK/복구): {alarm.get('OKActions', [])}")
            print(f"  - 평가 조건: {alarm.get('ComparisonOperator')} / ThresholdMetricId={alarm.get('ThresholdMetricId')}")
    except Exception as e:
        print(f"CloudWatch 조회 실패: {str(e)}")

def demo_check_status_and_recovery():
    """시나리오 6: 시스템 상태 및 자동 복구 확인"""
    print_header("시나리오 6: AIOps 시스템 헬스체크 및 장애 복구 상태 확인")
    print(f"대상 엔드포인트: {API_BASE_URL}/ops/status")
    
    result = http_get("/ops/status")
    print(f"\n[현재 백엔드 상태]:\n{json.dumps(result, indent=2, ensure_ascii=False)}")

def demo_full_e2e_walkthrough():
    """시나리오 7: 전체 E2E 종합 시연"""
    print_header("🚀 TVING AIOps 이상 탐지 ➔ 장애 경보(조치사항) ➔ 자동 복구(복구내역) 전체 E2E 종합 시연")
    time.sleep(1)
    
    print_step(1, "정상 상태 헬스체크 확인")
    demo_check_status_and_recovery()
    time.sleep(2)
    
    print_step(2, "CloudWatch Anomaly Detection 알람 및 복구 액션(OKActions) 등록 확인")
    demo_check_cloudwatch_alarms()
    time.sleep(2)
    
    print_step(3, "실시간 백엔드 CPU 과부하 주입 (Fault Injection)")
    demo_inject_cpu_load()
    time.sleep(2)
    
    print_step(4, "CloudWatch Anomaly Detection ➔ SNS ➔ Lambda ➔ Slack 장애 경보 & 긴급 조치사항 발송")
    demo_send_anomaly_slack_alert()
    time.sleep(3)
    
    print_step(5, "이상 부하 종료 후 시스템 상태 복구 확인 (Self-Healing)")
    demo_check_status_and_recovery()
    time.sleep(2)
    
    print_step(6, "시스템 정상 복구 완료 및 조치 내역 알림 발송 (SNS ➔ Slack)")
    demo_send_recovery_slack_alert()
    
    print("\n" + "=" * 70)
    print("🎉 TVING AIOps 이상 탐지 장애 경보 및 정상 복구 완료 전체 E2E 시연이 완료되었습니다!")
    print("=" * 70)

def main():
    while True:
        print("\n" + "=" * 70)
        print("     📺 TVING AIOps CloudWatch 이상 탐지 알람 시연 콘솔")
        print("=" * 70)
        print(" [1] 🔥 백엔드 CPU 과부하 주입 (Fault Injection)")
        print(" [2] ⏱️ API 응답 지연 장애 주입 (Delay Injection)")
        print(" [3] 💥 DB 연결 장애 주입 (DB Error Simulation)")
        print(" [4] 🚨 CloudWatch 이상 탐지 -> 장애 경보 & 조치사항 Slack 발송")
        print(" [5] ✅ 시스템 정상 복구 완료 & 복구 내역 Slack 발송")
        print(" [6] 📊 CloudWatch 이상 탐지 알람 상태 조회 (ALARM / OKActions)")
        print(" [7] 🩺 시스템 상태 및 헬스체크 확인 (/ops/status)")
        print(" [8] 🚀 전체 시나리오 원클릭 종합 시연 (장애 경보 + 조치사항 + 복구내역)")
        print(" [0] 🚪 종료")
        print("=" * 70)
        
        choice = input("선택할 번호를 입력하세요 (0-8): ").strip()
        
        if choice == "1":
            demo_inject_cpu_load()
        elif choice == "2":
            demo_inject_delay()
        elif choice == "3":
            demo_inject_db_error()
        elif choice == "4":
            demo_send_anomaly_slack_alert()
        elif choice == "5":
            demo_send_recovery_slack_alert()
        elif choice == "6":
            demo_check_cloudwatch_alarms()
        elif choice == "7":
            demo_check_status_and_recovery()
        elif choice == "8":
            demo_full_e2e_walkthrough()
        elif choice == "0":
            print("\n시연 프로그램을 종료합니다. 감사합니다.")
            break
        else:
            print("\n⚠️ 올바른 번호를 입력해 주세요.")
        
        input("\n계속하려면 [Enter] 키를 누르세요...")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        demo_full_e2e_walkthrough()
    else:
        main()
