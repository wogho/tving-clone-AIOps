#!/usr/bin/env python3
"""
================================================================================
TVING AIOps Platform - 실시간 리소스 & 이상 탐지 라이브 모니터링 CLI
================================================================================
"""
import os
import sys
import time
import json
import boto3
from datetime import datetime, timedelta

AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")
cw = boto3.client("cloudwatch", region_name=AWS_REGION)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_recent_metrics():
    now = datetime.utcnow()
    start_time = now - timedelta(minutes=10)
    
    queries = [
        {
            "Id": "cpu",
            "MetricStat": {
                "Metric": {
                    "Namespace": "AWS/ECS",
                    "MetricName": "CPUUtilization",
                    "Dimensions": [
                        {"Name": "ClusterName", "Value": "tving-cluster"},
                        {"Name": "ServiceName", "Value": "tving-backend-service"}
                    ]
                },
                "Period": 60,
                "Stat": "Average"
            },
            "ReturnData": True
        },
        {
            "Id": "mem",
            "MetricStat": {
                "Metric": {
                    "Namespace": "AWS/ECS",
                    "MetricName": "MemoryUtilization",
                    "Dimensions": [
                        {"Name": "ClusterName", "Value": "tving-cluster"},
                        {"Name": "ServiceName", "Value": "tving-backend-service"}
                    ]
                },
                "Period": 60,
                "Stat": "Average"
            },
            "ReturnData": True
        }
    ]
    
    try:
        res = cw.get_metric_data(
            MetricDataQueries=queries,
            StartTime=start_time,
            EndTime=now
        )
        data = {}
        for r in res.get("MetricDataResults", []):
            label = r["Id"]
            vals = r.get("Values", [])
            data[label] = vals[0] if vals else 0.0
        return data
    except Exception as e:
        return {"error": str(e)}

def get_alarm_states():
    try:
        res = cw.describe_alarms(
            AlarmNames=["tving-ecs-cpu-anomaly-alarm", "tving-ecs-memory-anomaly-alarm"]
        )
        alarms = {}
        for a in res.get("MetricAlarms", []):
            alarms[a["AlarmName"]] = {
                "state": a["StateValue"],
                "reason": a.get("StateReason", "N/A")[:70]
            }
        return alarms
    except Exception as e:
        return {"error": str(e)}

def render_bar(val, max_val=100, length=25):
    filled = int((val / max_val) * length) if max_val > 0 else 0
    filled = min(filled, length)
    bar = "█" * filled + "░" * (length - filled)
    return bar

def main():
    print("📺 TVING AIOps 실시간 모니터링 콘솔 시작 (Ctrl+C 로 종료)...")
    time.sleep(1)
    
    try:
        while True:
            clear_screen()
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            metrics = get_recent_metrics()
            alarms = get_alarm_states()
            
            cpu_val = metrics.get("cpu", 0.0)
            mem_val = metrics.get("mem", 0.0)
            
            print("=" * 70)
            print(f"  📺 TVING AIOps 실시간 서비스 & 이상 탐지 모니터링  [{now_str}]")
            print("=" * 70)
            print("  • 대상 클러스터 : tving-cluster (ECS Fargate)")
            print("  • 백엔드 서비스 : tving-backend-service")
            print("  • 대시보드 URL  : AWS CloudWatch -> tving-aiops-monitoring-dashboard")
            print("-" * 70)
            
            # 리소스 사용률 바
            cpu_bar = render_bar(cpu_val, 100)
            mem_bar = render_bar(mem_val, 100)
            
            cpu_color = "🔴" if cpu_val > 50 else ("🟡" if cpu_val > 20 else "🟢")
            mem_color = "🔴" if mem_val > 70 else ("🟡" if mem_val > 40 else "🟢")
            
            print("\n[📊 실시간 리소스 메트릭 현황]")
            print(f"  {cpu_color} CPU 사용률    : [{cpu_bar}] {cpu_val:5.2f} % (정상대역: 0~15%)")
            print(f"  {mem_color} 메모리 사용률 : [{mem_bar}] {mem_val:5.2f} % (정상대역: 0~35%)")
            
            print("\n[🚨 CloudWatch Anomaly Detection 알람 상태]")
            for name, info in alarms.items():
                if isinstance(info, dict):
                    status = info["state"]
                    icon = "✅" if status == "OK" else ("🚨" if status == "ALARM" else "⚪")
                    print(f"  {icon} {name:<28}: [{status:5}]")
                    print(f"     └─ 사유: {info['reason']}")
                else:
                    print(f"  {name}: {info}")
                    
            print("\n" + "-" * 70)
            print("💡 5초마다 자동 갱신됩니다. (부하 주입 시 CPU 바 및 알람 변화 실시간 반영)")
            print("=" * 70)
            
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n\n모니터링 콘솔을 종료합니다.")

if __name__ == "__main__":
    main()
