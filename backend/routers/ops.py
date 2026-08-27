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


class OpsLoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def ops_admin_login(req: OpsLoginRequest):
    """AIOps 관제 센터 전용 관리자 로그인 API"""
    if req.username == "admin" and req.password == "admin@1234":
        return {
            "status": "success",
            "message": "AIOps 관리자 인증 성공",
            "user": {
                "username": "admin",
                "role": "SUPER_ADMIN",
                "token": "ops-admin-session-token-761018884888"
            }
        }
    raise HTTPException(status_code=401, detail="아이디 또는 비밀번호가 올바르지 않습니다.")


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


# Knowledge Base ID 및 Lambda Tool Provider
KB_ID = os.getenv("KNOWLEDGE_BASE_ID", "CW9N0QAOGB")
KB_DATA_SOURCE_ID = os.getenv("KB_DATA_SOURCE_ID", "TPWBMJCRAO")
KB_MANUALS_BUCKET = os.getenv("KB_MANUALS_BUCKET", "kjh-aiops-manuals")
AIOPS_TOOL_LAMBDA = os.getenv("AIOPS_TOOL_LAMBDA", "aiops-agent-tools")

# Bedrock Agent & Runtime 클라이언트
try:
    bedrock_agent_client = boto3.client("bedrock-agent", region_name=AWS_REGION)
    bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)
except Exception:
    bedrock_agent_client = None
    bedrock_agent_runtime = None

# EC2, S3, Logs 클라이언트
try:
    ec2_client = boto3.client("ec2", region_name=AWS_REGION)
    s3_client = boto3.client("s3", region_name=AWS_REGION)
    logs_client = boto3.client("logs", region_name=AWS_REGION)
except Exception:
    ec2_client = None
    s3_client = None
    logs_client = None


class KBUploadRequest(BaseModel):
    filename: str
    content: str
    category: Optional[str] = "일반"


@router.get("/kb/list")
def list_kb_manuals():
    """Knowledge Base에 등록된 S3 매뉴얼 파일 목록 조회 (즉시 응답)"""
    files = []
    if s3_client:
        try:
            resp = s3_client.list_objects_v2(Bucket=KB_MANUALS_BUCKET)
            for item in resp.get("Contents", []):
                files.append({
                    "key": item["Key"],
                    "size": item["Size"],
                    "lastModified": item["LastModified"].strftime("%Y-%m-%d %H:%M:%S")
                })
        except Exception as e:
            files = [{"error": str(e)}]

    return {
        "bucket": KB_MANUALS_BUCKET,
        "knowledge_base_id": KB_ID,
        "sync_status": "READY",
        "files": files,
        "count": len(files)
    }


@router.post("/kb/upload")
def upload_kb_manual(req: KBUploadRequest):
    """새로운 운영 매뉴얼(.md)을 S3에 저장하고 Bedrock KB 동기화(Sync) 트리거"""
    if not s3_client:
        raise HTTPException(status_code=500, detail="S3 클라이언트가 초기화되지 않았습니다.")

    filename = req.filename.strip()
    if not filename.endswith(".md"):
        filename += ".md"

    # S3 업로드
    try:
        s3_client.put_object(
            Bucket=KB_MANUALS_BUCKET,
            Key=filename,
            Body=req.content.encode("utf-8"),
            ContentType="text/markdown; charset=utf-8"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"S3 업로드 실패: {str(e)}")

    # Bedrock KB Ingestion Job 트리거
    job_id = None
    job_status = "STARTED"
    if bedrock_agent_client:
        try:
            job_resp = bedrock_agent_client.start_ingestion_job(
                knowledgeBaseId=KB_ID,
                dataSourceId=KB_DATA_SOURCE_ID
            )
            job_id = job_resp.get("ingestionJob", {}).get("ingestionJobId")
            job_status = job_resp.get("ingestionJob", {}).get("status", "IN_PROGRESS")
        except Exception as e:
            job_status = f"Ingestion trigger warning: {str(e)}"

    return {
        "status": "success",
        "message": f"매뉴얼 '{filename}'이 S3에 업로드되고 Bedrock Knowledge Base 동기화가 시작되었습니다.",
        "filename": filename,
        "bucket": KB_MANUALS_BUCKET,
        "job_id": job_id,
        "job_status": job_status
    }


@router.get("/kb/sync-status")
def get_kb_sync_status():
    """Knowledge Base 최신 동기화 상태 확인"""
    if not bedrock_agent_client:
        return {"status": "UNKNOWN", "message": "Bedrock Agent client not ready"}
    try:
        jobs = bedrock_agent_client.list_ingestion_jobs(
            knowledgeBaseId=KB_ID,
            dataSourceId=KB_DATA_SOURCE_ID,
            maxResults=3
        )
        job_list = jobs.get("ingestionJobSummaries", [])
        latest = job_list[0] if job_list else None
        return {
            "knowledge_base_id": KB_ID,
            "status": latest.get("status") if latest else "NO_JOBS",
            "job_id": latest.get("ingestionJobId") if latest else None,
            "updated_at": latest.get("updatedAt").isoformat() if latest and latest.get("updatedAt") else None,
            "stats": latest.get("statistics") if latest else None
        }
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}


# ----------------------------------------------------------------------
# AIOps Agent Tool Implementations (Harness Provider)
# ----------------------------------------------------------------------

def tool_get_ec2_status(instance_identifier: str):
    """Tool 1: EC2 상태 조회"""
    if not ec2_client:
        return {"error": "EC2 client not initialized"}
    try:
        if instance_identifier.startswith("i-"):
            filters = [{"Name": "instance-id", "Values": [instance_identifier]}]
        else:
            filters = [{"Name": "tag:Name", "Values": [instance_identifier]}]
        
        response = ec2_client.describe_instances(Filters=filters)
        reservations = response.get("Reservations", [])
        if not reservations or not reservations[0].get("Instances"):
            return {"error": f"Instance '{instance_identifier}' not found"}
        
        inst = reservations[0]["Instances"][0]
        inst_id = inst["InstanceId"]
        
        # 상태 확인
        status_resp = ec2_client.describe_instance_status(InstanceIds=[inst_id], IncludeAllInstances=True)
        status_items = status_resp.get("InstanceStatuses", [])
        inst_status = status_items[0].get("InstanceStatus", {}).get("Status") if status_items else "unknown"
        sys_status = status_items[0].get("SystemStatus", {}).get("Status") if status_items else "unknown"

        return {
            "instanceId": inst_id,
            "name": instance_identifier,
            "state": inst["State"]["Name"],
            "instanceType": inst["InstanceType"],
            "privateIp": inst.get("PrivateIpAddress"),
            "publicIp": inst.get("PublicIpAddress"),
            "instanceStatus": inst_status,
            "systemStatus": sys_status
        }
    except Exception as e:
        return {"error": str(e)}


def tool_list_s3_buckets():
    """Tool 2: S3 버킷 목록 조회"""
    if not s3_client:
        return {"error": "S3 client not initialized"}
    try:
        response = s3_client.list_buckets()
        buckets = [{"name": b["Name"], "creationDate": b["CreationDate"].isoformat()} for b in response.get("Buckets", [])]
        return {"count": len(buckets), "buckets": buckets}
    except Exception as e:
        return {"error": str(e)}


def tool_get_s3_objects(bucket_name: str, prefix: str = "", max_keys: int = 20):
    """Tool 3: S3 버킷 객체 목록 조회"""
    if not s3_client:
        return {"error": "S3 client not initialized"}
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix, MaxKeys=int(max_keys))
        objects = [{"key": item["Key"], "size": item["Size"], "lastModified": item["LastModified"].isoformat()} for item in response.get("Contents", [])]
        return {"bucket": bucket_name, "prefix": prefix, "count": len(objects), "objects": objects}
    except Exception as e:
        return {"error": str(e)}


def tool_get_recent_logs(log_group: str, minutes: int = 10, filter_pattern: str = "ERROR"):
    """Tool 4: CloudWatch Logs 검색"""
    if not logs_client:
        return {"error": "Logs client not initialized"}
    try:
        end_ms = int(time.time() * 1000)
        start_ms = end_ms - int(minutes) * 60 * 1000
        response = logs_client.filter_log_events(
            logGroupName=log_group,
            startTime=start_ms,
            endTime=end_ms,
            filterPattern=filter_pattern,
            limit=20
        )
        events = [{"timestamp": item["timestamp"], "message": item["message"], "logStreamName": item.get("logStreamName")} for item in response.get("events", [])]
        return {"logGroup": log_group, "minutes": minutes, "filterPattern": filter_pattern, "count": len(events), "events": events}
    except Exception as e:
        return {"error": str(e)}


def tool_search_knowledge_base(query: str):
    """Tool 5: Bedrock Knowledge Base 검색"""
    if not bedrock_agent_runtime:
        return {"error": "Bedrock agent runtime not initialized"}
    try:
        response = bedrock_agent_runtime.retrieve(
            knowledgeBaseId=KB_ID,
            retrievalQuery={"text": query},
            retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 4}}
        )
        results = []
        for item in response.get("retrievalResults", []):
            results.append({
                "text": item["content"]["text"],
                "score": item.get("score"),
                "source": item.get("location", {}).get("s3Location", {}).get("uri")
            })
        return {"query": query, "count": len(results), "results": results}
    except Exception as e:
        return {"error": str(e)}



def tool_analyze_traffic_by_path(log_group: str = "/ecs/tving-backend", minutes: int = 10, path_prefix: str = "/api/contents"):
    """Tool 6: API 경로별 트래픽 집중도 분석"""
    if not logs_client:
        return {"error": "Logs client not initialized"}
    try:
        import re
        end_ms = int(time.time() * 1000)
        start_ms = end_ms - int(minutes) * 60 * 1000
        response = logs_client.filter_log_events(
            logGroupName=log_group,
            startTime=start_ms,
            endTime=end_ms,
            filterPattern=f'"{path_prefix}"',
            limit=5000
        )
        pattern = re.compile(r'"(?:GET|POST|PUT|DELETE)\s+(' + re.escape(path_prefix) + r'/\d+)')
        counts = {}
        for item in response.get("events", []):
            m = pattern.search(item.get("message", ""))
            if m:
                p = m.group(1)
                counts[p] = counts.get(p, 0) + 1
        sorted_paths = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return {
            "logGroup": log_group,
            "minutes": minutes,
            "totalRequests": sum(counts.values()),
            "topPaths": [{"path": p, "count": c} for p, c in sorted_paths[:10]]
        }
    except Exception as e:
        return {"error": str(e)}


def tool_diagnose_content_popularity(log_group: str = "/ecs/tving-backend", minutes: int = 10, path_prefix: str = "/api/contents", surge_multiplier: int = 3):
    """Tool 7: 신작 화제성 집중도 자동 진단"""
    data = tool_analyze_traffic_by_path(log_group, minutes, path_prefix)
    if "error" in data:
        return data
    total = data.get("totalRequests", 0)
    paths = data.get("topPaths", [])
    if total < 5 or not paths:
        return {"diagnosis": "INSUFFICIENT_DATA", "message": "최근 관측된 트래픽이 적습니다."}
    avg = total / len(paths)
    surging = [p for p in paths if p["count"] >= avg * surge_multiplier]
    if surging:
        return {"diagnosis": "CONTENT_POPULARITY_SURGE", "surgingContents": surging, "message": f"신작 화제성 트래픽 집중 감지 ({len(surging)}개 콘텐츠)"}
    return {"diagnosis": "NORMAL_DISTRIBUTED_TRAFFIC", "message": "트래픽이 고르게 분산되어 있습니다."}


def tool_get_content_info(content_id: int):
    """Tool 8: 콘텐츠 상세 메타데이터 조회"""
    try:
        import urllib.request
        req = urllib.request.Request(f"https://d33nd37o8cwhu4.cloudfront.net/api/contents/{content_id}", headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"contentId": content_id, "error": str(e)}


def tool_get_ecs_alarms(alarm_name_prefix: str = "tving", state_filter: str = "ALL"):
    """Tool 9: CloudWatch 경보 목록 조회"""
    if not cw_client:
        return {"error": "CloudWatch client not initialized"}
    try:
        kwargs = {}
        if alarm_name_prefix:
            kwargs["AlarmNamePrefix"] = str(alarm_name_prefix)
        if state_filter and state_filter != "ALL":
            kwargs["StateValue"] = state_filter
        resp = cw_client.describe_alarms(**kwargs)
        alarms = []
        for a in resp.get("MetricAlarms", []):
            alarms.append({
                "name": a["AlarmName"],
                "state": a["StateValue"],
                "reason": a["StateReason"],
                "metric": a.get("MetricName", a.get("ThresholdMetricId", "AnomalyBand")),
                "updated": a["StateUpdatedTimestamp"].isoformat()
            })
        return {"prefix": alarm_name_prefix, "count": len(alarms), "alarms": alarms}
    except Exception as e:
        return {"error": str(e)}


def tool_get_alarm_history(alarm_name_prefix: str = "tving", alarm_name: str = None, minutes: int = 1440):
    """Tool 10: CloudWatch 경보 변경 이력 조회"""
    if not cw_client:
        return {"error": "CloudWatch client not initialized"}
    try:
        end = time.time()
        start = end - int(minutes) * 60
        kwargs = {
            "StartDate": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(start)),
            "EndDate": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(end)),
            "HistoryItemType": "StateUpdate",
            "MaxRecords": 100
        }
        if alarm_name:
            kwargs["AlarmName"] = str(alarm_name)
        resp = cw_client.describe_alarm_history(**kwargs)
        items = []
        for h in resp.get("AlarmHistoryItems", []):
            aname = h.get("AlarmName", "")
            if alarm_name_prefix and not aname.startswith(str(alarm_name_prefix)) and not alarm_name:
                continue
            items.append({
                "alarmName": aname,
                "timestamp": h["Timestamp"].isoformat(),
                "summary": h.get("HistorySummary", "")
            })
        return {"minutes": minutes, "count": len(items), "history": items[:25]}
    except Exception as e:
        return {"error": str(e)}


def tool_get_ecs_5xx_errors(log_group: str = "/ecs/tving-backend", minutes: int = 60, max_events: int = 20):
    """Tool 11: 5xx 에러 로그 검색"""
    return tool_get_recent_logs(log_group, minutes, "500 OR 502 OR 503 OR 504 OR Error OR Exception")


def tool_diagnose_ecs_health(log_group: str = "/ecs/tving-backend", alarm_name_prefix: str = "tving", minutes: int = 30):
    """Tool 12: ECS 헬스 종합 진단"""
    alarms = tool_get_ecs_alarms(alarm_name_prefix, "ALARM")
    errors = tool_get_ecs_5xx_errors(log_group, minutes)
    active = alarms.get("alarms", [])
    ecount = errors.get("count", 0)
    if active or ecount > 5:
        status = "DEGRADED"
        msg = f"경보 {len(active)}건 발령 중, 최근 {minutes}분간 에러 {ecount}건 감지."
    else:
        status = "HEALTHY"
        msg = "모든 경보 정상(OK), 에러 발생 없음."
    return {"status": status, "diagnosis": msg, "activeAlarms": active, "errorCount": ecount}


def tool_list_log_groups(prefix: str = "/ecs"):
    """Tool 13: CloudWatch 로그 그룹 목록"""
    if not logs_client:
        return {"error": "Logs client not initialized"}
    try:
        kwargs = {}
        if prefix:
            kwargs["logGroupNamePrefix"] = str(prefix)
        resp = logs_client.describe_log_groups(**kwargs)
        return {"logGroups": [g["logGroupName"] for g in resp.get("logGroups", [])]}
    except Exception as e:
        return {"error": str(e)}


def tool_analyze_traffic_security(log_group: str = "/ecs/tving-backend", minutes: int = 10):
    """Tool 14: 보안 트래픽 분석 (Flash Crowd vs DoS)"""
    if not logs_client:
        return {"error": "Logs client not initialized"}
    try:
        import re
        end_ms = int(time.time() * 1000)
        start_ms = end_ms - int(minutes) * 60 * 1000
        response = logs_client.filter_log_events(
            logGroupName=log_group,
            startTime=start_ms,
            endTime=end_ms,
            filterPattern="CLIENT_IP",
            limit=5000
        )
        events = response.get("events", [])
        if not events:
            return {"securityVerdict": "LEGITIMATE_TRAFFIC", "message": "수신된 트래픽이 정상 범위입니다."}
        log_regex = re.compile(r'\[CLIENT_IP:\s*([^\]]+)\]\s+([A-Z]+)\s+([^\s]+)\s+status=(\d+)\s+latency=([\d\.]+)ms')
        ip_stats = {}
        total = 0
        for item in events:
            m = log_regex.search(item.get("message", ""))
            if m:
                ip, method, path, status, latency = m.groups()
                total += 1
                if ip not in ip_stats:
                    ip_stats[ip] = {"ip": ip, "count": 0, "totalLat": 0.0, "paths": {}}
                ip_stats[ip]["count"] += 1
                ip_stats[ip]["totalLat"] += float(latency)
                ip_stats[ip]["paths"][path] = ip_stats[ip]["paths"].get(path, 0) + 1
        attackers = []
        for stat in ip_stats.values():
            avg_lat = round(stat["totalLat"] / stat["count"], 1)
            ratio = round(stat["count"] / total * 100, 1)
            if (ratio >= 40.0 and avg_lat > 1000) or any("/api/ops/" in p for p in stat["paths"]):
                attackers.append({"ip": stat["ip"], "count": stat["count"], "ratio": ratio, "avgLatency": avg_lat, "attackType": "Algorithmic DoS"})
        if attackers:
            return {"securityVerdict": "ATTACK_DETECTED", "attackers": attackers, "message": f"공격자 IP {attackers[0]['ip']}에서 DoS 공격 감지됨. block_malicious_ip 실행 필요."}
        return {"securityVerdict": "LEGITIMATE_TRAFFIC", "uniqueIPs": len(ip_stats), "message": "정상 분산 트래픽(Flash Crowd)입니다."}
    except Exception as e:
        return {"error": str(e)}


def tool_block_malicious_ip(ip_address: str, reason: str = "AIOps Automated Defense"):
    """Tool 15: AWS WAF IP 차단"""
    try:
        waf = boto3.client("wafv2", region_name=AWS_REGION)
        clean_ip = ip_address.strip()
        cidr = clean_ip if "/" in clean_ip else f"{clean_ip}/32"
        resp = waf.get_ip_set(Name="tving-blocked-ips", Scope="REGIONAL", Id="4c43ae51-3cca-43ba-8047-11ac03676794")
        lock_token = resp["LockToken"]
        addrs = resp["IPSet"].get("Addresses", [])
        if cidr not in addrs:
            addrs.append(cidr)
            waf.update_ip_set(Name="tving-blocked-ips", Scope="REGIONAL", Id="4c43ae51-3cca-43ba-8047-11ac03676794", Addresses=addrs, LockToken=lock_token)
        return {"status": "BLOCKED_SUCCESS", "blockedIp": cidr, "totalBlocked": len(addrs), "message": f"WAF 차단 완료: {cidr}"}
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


def tool_list_blocked_ips():
    """Tool 16: WAF 차단 목록 조회"""
    try:
        waf = boto3.client("wafv2", region_name=AWS_REGION)
        resp = waf.get_ip_set(Name="tving-blocked-ips", Scope="REGIONAL", Id="4c43ae51-3cca-43ba-8047-11ac03676794")
        return {"blockedIps": resp["IPSet"].get("Addresses", []), "count": len(resp["IPSet"].get("Addresses", []))}
    except Exception as e:
        return {"error": str(e)}


def tool_unblock_ip(ip_address: str):
    """Tool 17: WAF 차단 해제"""
    try:
        waf = boto3.client("wafv2", region_name=AWS_REGION)
        clean_ip = ip_address.strip()
        cidr = clean_ip if "/" in clean_ip else f"{clean_ip}/32"
        resp = waf.get_ip_set(Name="tving-blocked-ips", Scope="REGIONAL", Id="4c43ae51-3cca-43ba-8047-11ac03676794")
        lock_token = resp["LockToken"]
        addrs = [a for a in resp["IPSet"].get("Addresses", []) if a != cidr]
        waf.update_ip_set(Name="tving-blocked-ips", Scope="REGIONAL", Id="4c43ae51-3cca-43ba-8047-11ac03676794", Addresses=addrs, LockToken=lock_token)
        return {"status": "UNBLOCKED_SUCCESS", "unblockedIp": cidr}
    except Exception as e:
        return {"error": str(e)}


# Bedrock Tool Definitions (Tool Configuration)
AIOPS_TOOL_CONFIG = {
    "tools": [
        {
            "toolSpec": {
                "name": "get_ec2_status",
                "description": "EC2 인스턴스 ID(예: i-xxx) 또는 Name 태그를 입력받아 인스턴스의 상태(running/stopped), 상태 검사, IP 등을 조회합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "instance_identifier": {
                                "type": "string",
                                "description": "EC2 인스턴스 ID 또는 Name 태그 (예: tving-dev-vm)"
                            }
                        },
                        "required": ["instance_identifier"]
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "list_s3_buckets",
                "description": "현재 AWS 계정에서 조회 가능한 모든 S3 Bucket 목록을 반환합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "get_s3_objects",
                "description": "특정 S3 Bucket 내의 Object 목록(Key, 크기, 수정일시)을 조회합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "bucket_name": {
                                "type": "string",
                                "description": "조회할 S3 버킷 이름"
                            },
                            "prefix": {
                                "type": "string",
                                "description": "검색할 Object prefix (선택)"
                            },
                            "max_keys": {
                                "type": "integer",
                                "description": "조회할 최대 개수 (기본 20)"
                            }
                        },
                        "required": ["bucket_name"]
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "get_recent_logs",
                "description": "지정한 CloudWatch Logs 그룹(기본: /ecs/tving-backend)에서 최근 N분 동안의 에러 로그(기본: ERROR)를 검색합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "log_group": {
                                "type": "string",
                                "description": "CloudWatch 로그 그룹 이름 (기본: /ecs/tving-backend)"
                            },
                            "minutes": {
                                "type": "integer",
                                "description": "최근 몇 분간의 로그를 검색할지 (기본 10)"
                            },
                            "filter_pattern": {
                                "type": "string",
                                "description": "필터링할 에러 패턴 문자열 (기본 ERROR)"
                            }
                        }
                    }
                }
            }
        },

        {
            "toolSpec": {
                "name": "search_knowledge_base",
                "description": "Bedrock Knowledge Base(CW9N0QAOGB)에 저장된 클라우드 운영 매뉴얼(EC2, S3, CloudWatch 장애 대응 가이드)에서 관련 문서를 검색합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "검색할 장애 상황 또는 질의 키워드"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "analyze_traffic_security",
                "description": "TVING CloudWatch 로그(/ecs/tving-backend)를 심층 분석하여 정상적인 신작 오픈 트래픽(Flash Crowd)인지 특정 공격자 IP의 DoS 공격인지 진단하고 공격자 IP를 식별합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "log_group": {
                                "type": "string",
                                "description": "분석할 로그 그룹 (기본: /ecs/tving-backend)"
                            },
                            "minutes": {
                                "type": "integer",
                                "description": "분석할 최근 시간(분, 기본: 10)"
                            }
                        }
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "block_malicious_ip",
                "description": "식별된 악성 공격자 IP를 AWS WAF IPSet(tving-blocked-ips)에 즉시 등록하여 실시간으로 영구 격리/차단합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "ip_address": {
                                "type": "string",
                                "description": "차단할 공격자 IP 주소 (예: 198.51.100.23)"
                            },
                            "reason": {
                                "type": "string",
                                "description": "차단 사유"
                            }
                        },
                        "required": ["ip_address"]
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "list_blocked_ips",
                "description": "현재 AWS WAF(tving-blocked-ips)에 의해 격리/차단된 악성 IP 목록과 보안 상태를 조회합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "unblock_ip",
                "description": "오탐으로 차단된 IP를 AWS WAF 차단 목록에서 제거하여 정상 트래픽으로 복구합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "ip_address": {
                                "type": "string",
                                "description": "차단 해제할 IP 주소"
                            }
                        },
                        "required": ["ip_address"]
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "diagnose_content_popularity",
                "description": "신작 공개 시 각 콘텐츠(ID)별 트래픽 집중도와 화제성을 진단하여 Flash Crowd 여부를 판정합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "log_group": {
                                "type": "string",
                                "description": "로그 그룹 이름 (기본: /ecs/tving-backend)"
                            },
                            "minutes": {
                                "type": "integer",
                                "description": "분석 시간(분, 기본: 10)"
                            }
                        }
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "get_content_info",
                "description": "특정 콘텐츠 ID의 상세 정보(제목, 카테고리, 장르)를 조회합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "content_id": {
                                "type": "integer",
                                "description": "콘텐츠 ID 번호"
                            }
                        },
                        "required": ["content_id"]
                    }
                }
            }
        }, 
                {
            "toolSpec": {
                "name": "analyze_traffic_by_path",
                "description": "CloudWatch Logs에서 API 경로(콘텐츠)별 요청 횟수를 집계하여 트래픽 집중도를 분석합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "log_group": {"type": "string", "description": "로그 그룹 이름"},
                            "minutes": {"type": "integer", "description": "분석 시간(분)"},
                            "path_prefix": {"type": "string", "description": "분석할 경로 접두사 (기본 /api/contents)"}
                        },
                        "required": ["log_group"]
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "get_ecs_alarms",
                "description": "CloudWatch 경보(Alarm)의 현재 상태를 조회합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "alarm_name_prefix": {"type": "string", "description": "경보 이름 접두사 필터"},
                            "state_filter": {"type": "string", "description": "상태 필터 (ALARM/OK/ALL)"}
                        }
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "get_ecs_5xx_errors",
                "description": "CloudWatch Logs에서 5xx 에러를 검색하고 상태코드별로 집계합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "log_group": {"type": "string", "description": "로그 그룹 이름"},
                            "minutes": {"type": "integer", "description": "분석 시간(분)"},
                            "max_events": {"type": "integer", "description": "최대 조회 개수"}
                        },
                        "required": ["log_group"]
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "diagnose_ecs_health",
                "description": "경보 상태와 5xx 에러를 종합하여 ECS 서비스의 전반적인 건강 상태를 진단합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "log_group": {"type": "string", "description": "로그 그룹 이름"},
                            "alarm_name_prefix": {"type": "string", "description": "경보 이름 접두사"},
                            "minutes": {"type": "integer", "description": "분석 시간(분)"}
                        },
                        "required": ["log_group"]
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "list_log_groups",
                "description": "CloudWatch에 존재하는 로그 그룹 목록을 조회합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "prefix": {"type": "string", "description": "로그 그룹 이름 접두사 필터"}
                        }
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "get_alarm_history",
                "description": "CloudWatch 경보의 최근 상태 변경 이력(ALARM 전환 등)을 조회합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "alarm_name_prefix": {"type": "string", "description": "경보 이름 접두사"},
                            "minutes": {"type": "integer", "description": "조회할 시간 범위(분)"}
                        }
                    }
                }
            }
        }

    ]
}


def call_lambda_agent_tool(tool_name: str, tool_args: dict):
    """aiops-agent-tools Lambda 함수 직접 호출 (파라미터 안전 기본값 적용)"""
    # Safe defaults for TVING infrastructure
    if "log_group" in tool_args:
        if not tool_args["log_group"] or "my-ecs" in tool_args["log_group"] or tool_args["log_group"] == "/aws/ecs/containerinsights":
            tool_args["log_group"] = "/ecs/tving-backend"
    elif tool_name in ["get_recent_logs", "analyze_traffic_security", "diagnose_ecs_health", "diagnose_content_popularity", "get_ecs_5xx_errors"]:
        tool_args["log_group"] = "/ecs/tving-backend"

    if "alarm_name_prefix" in tool_args and not tool_args["alarm_name_prefix"]:
        tool_args["alarm_name_prefix"] = "tving"

    payload = {"tool_name": tool_name, **tool_args}
    try:
        lambda_client = boto3.client("lambda", region_name=AWS_REGION)
        resp = lambda_client.invoke(
            FunctionName=AIOPS_TOOL_LAMBDA,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload).encode("utf-8")
        )
        resp_payload = resp["Payload"].read().decode("utf-8")
        return json.loads(resp_payload)
    except Exception as e:
        return {"error": f"Lambda Tool execution failed: {str(e)}"}


def execute_tool_call(tool_name: str, tool_args: dict):
    """AIOps Harness 도구 실행기 (모든 도구를 Lambda aiops-agent-tools로 동적 위임)"""
    # 1. Lambda Tool 직접 호출
    res = call_lambda_agent_tool(tool_name, tool_args)
    if "error" not in res:
        return res
    if not str(res.get("error", "")).startswith("Lambda Tool execution failed"):
        return res

    # 2. Lambda 자체 호출 실패 시 로컬 Fallback
    if tool_name == "get_ec2_status":
        return tool_get_ec2_status(tool_args.get("instance_identifier", ""))
    elif tool_name == "list_s3_buckets":
        return tool_list_s3_buckets()
    elif tool_name == "get_s3_objects":
        return tool_get_s3_objects(
            tool_args.get("bucket_name", ""),
            tool_args.get("prefix", ""),
            tool_args.get("max_keys", 20)
        )
    elif tool_name == "get_recent_logs":
        return tool_get_recent_logs(
            tool_args.get("log_group", "/ecs/tving-backend"),
            tool_args.get("minutes", 10),
            tool_args.get("filter_pattern", "ERROR")
        )
    elif tool_name == "search_knowledge_base":
        return tool_search_knowledge_base(tool_args.get("query", ""))
    elif tool_name == "analyze_traffic_by_path":
        return tool_analyze_traffic_by_path(
            tool_args.get("log_group", "/ecs/tving-backend"),
            tool_args.get("minutes", 10),
            tool_args.get("path_prefix", "/api/contents")
        )
    elif tool_name == "diagnose_content_popularity":
        return tool_diagnose_content_popularity(
            tool_args.get("log_group", "/ecs/tving-backend"),
            tool_args.get("minutes", 10),
            tool_args.get("path_prefix", "/api/contents")
        )
    elif tool_name == "get_content_info":
        return tool_get_content_info(tool_args.get("content_id", 1))
    return res


# ----------------------------------------------------------------------
# AIOps Agent Harness Chat Handler (with Multi-Turn Tool Calling)
# ----------------------------------------------------------------------

@router.post("/ai-chat")
def ops_ai_chat(request: OpsChatRequest, db: Session = Depends(get_db)):
    """
    운영자 전용 AIOps 대화형 장애 진단 및 모니터링 AI 챗봇 (aiops_harness 전용 Tool-Calling 연동)
    """
    user_query = request.message

    # 실시간 DB 헬스
    db_ok = True
    db_latency = 0.0
    try:
        t0 = time.time()
        db.execute(text("SELECT 1;"))
        db_latency = round((time.time() - t0) * 1000, 2)
    except Exception:
        db_ok = False

    system_prompt = f"""당신은 TVING OTT 클라우드 인프라를 총괄하는 전문 SRE/SecOps AIOps 지능형 운영자 어시스턴트(AIOps Harness)입니다.
TVING은 콘텐츠 인기/화제성에 따라 특정 콘텐츠 API에 트래픽이 급격히 몰릴 수 있으며, 때로는 악의적인 DoS 공격을 받을 수도 있습니다.
사용 가능한 도구를 적극 활용하여 시스템 상태 확인, 장애 로그 분석, 보안 위협 분석, S3/EC2 점검, Bedrock Knowledge Base 조회를 수행하고 정확한 근거 기반의 조치 가이드를 제공하세요.

[사용 가능한 AIOps 도구]
1. get_ec2_status: EC2 인스턴스 상태 및 헬스체크
2. list_s3_buckets: S3 버킷 목록 확인
3. get_s3_objects: 특정 S3 버킷 내부 객체 목록 확인
4. get_recent_logs: CloudWatch Logs 에러 로그 실시간 검색
5. search_knowledge_base: Bedrock Knowledge Base (KB ID: {KB_ID}) 장애 대응 매뉴얼 RAG 검색
6. analyze_traffic_by_path: API 경로(콘텐츠)별 요청 집계, 어떤 콘텐츠에 트래픽이 몰렸는지 확인
7. diagnose_content_popularity: 평균 대비 급증한 화제작을 자동 진단하고 조치 추천
8. get_content_info: 콘텐츠 ID로 실제 제목/카테고리 조회
9. analyze_traffic_security: 클라이언트 IP 패턴을 분석하여 정상 트래픽(화제성)인지 DoS 공격인지 판별
10. block_malicious_ip / list_blocked_ips / unblock_ip: WAF를 통한 공격자 IP 차단/조회/해제
11. get_ecs_alarms / get_alarm_history: CloudWatch 경보 현재 상태 및 이력 조회
12. get_ecs_5xx_errors / diagnose_ecs_health: 5xx 에러 및 서비스 전반 건강 상태 진단
13. list_log_groups: CloudWatch 로그 그룹 목록 조회

[트래픽 이상 판단 원칙 - 중요]
운영자가 "뭐가 문제야?", "지금 상황 어때?", "트래픽 이상 있어?" 처럼 막연하게 물어보면,
다음 순서로 스스로 판단하여 답하십시오.

1. 먼저 analyze_traffic_security를 호출하여 클라이언트 IP 분포를 확인합니다.
   - securityVerdict가 "ATTACK_DETECTED"이면: 보안 공격(DoS)입니다.
     공격자 IP와 공격 유형을 명시하고, block_malicious_ip 사용을 권장하십시오.
   - securityVerdict가 "LEGITIMATE_TRAFFIC"이면: 정상 트래픽입니다.
     이어서 analyze_traffic_by_path 또는 diagnose_content_popularity를 호출하여
     어떤 콘텐츠에 트래픽이 몰렸는지 분석하고, get_content_info로 실제 제목을 확인하여
     "OO 콘텐츠의 화제성 때문입니다"라고 답하십시오.
2. 운영자가 Tool 이름을 직접 언급하지 않아도, 이 판단 순서에 따라 스스로 적절한 Tool들을 연쇄적으로 호출하십시오.
3. 보안 공격과 화제성 트래픽을 혼동하지 않도록, analyze_traffic_security의 결과를 최우선 판단 기준으로 삼으십시오.

[실시간 기본 환경 정보]
- 서비스: TVING OTT 플랫폼 (user6.cloudai.store / ops.user6.cloudai.store)
- 리전: ap-northeast-2 (서울)
- RDS PostgreSQL: tving-postgres (Status: {'HEALTHY' if db_ok else 'UNHEALTHY'}, Latency: {db_latency}ms)
- ECS Cluster: tving-cluster | Backend Service: tving-backend-service / tving-aiops-backend-service

답변 작성 시:
- 도구를 호출한 경우 어떤 도구로 어떤 데이터를 확인했는지 명시하세요.
- 마크다운 형식으로 명확하고 체계적으로 정리하여 답변하세요.
"""


    if not bedrock_client:
        return {
            "reply": f"🤖 [AIOps Mock Agent]\n\n현재 시스템 상태는 정상입니다.\n- DB 상태: {'정상' if db_ok else '오류'}\n- 지연 시간: {db_latency}ms\n- 질의: {user_query}",
            "model": "local-fallback",
            "tools_used": []
        }

    messages = [
        {
            "role": "user",
            "content": [{"text": user_query}]
        }
    ]

    tools_used_history = []
    max_turns = 3

    try:
        for _ in range(max_turns):
            response = bedrock_client.converse(
                modelId=BEDROCK_MODEL_ID,
                messages=messages,
                system=[{"text": system_prompt}],
                toolConfig=AIOPS_TOOL_CONFIG,
                inferenceConfig={"maxTokens": 1024, "temperature": 0.2, "topP": 0.9}
            )

            stop_reason = response.get("stopReason")
            output_msg = response["output"]["message"]
            messages.append(output_msg)

            if stop_reason == "tool_use":
                # Tool Use 처리 루프
                tool_results_content = []
                for content_block in output_msg.get("content", []):
                    if "toolUse" in content_block:
                        tool_use = content_block["toolUse"]
                        tool_id = tool_use["toolUseId"]
                        tool_name = tool_use["name"]
                        tool_input = tool_use["input"]

                        # 도구 실행
                        tool_output = execute_tool_call(tool_name, tool_input)
                        tools_used_history.append({
                            "tool": tool_name,
                            "input": tool_input,
                            "output_summary": str(tool_output)[:200]
                        })

                        tool_results_content.append({
                            "toolResult": {
                                "toolUseId": tool_id,
                                "content": [{"json": tool_output}],
                                "status": "success"
                            }
                        })

                # 도구 실행 결과를 메시지에 추가
                messages.append({
                    "role": "user",
                    "content": tool_results_content
                })
            else:
                # 최종 응답 도달
                final_text = ""
                for block in output_msg.get("content", []):
                    if "text" in block:
                        final_text += block["text"]

                return {
                    "reply": final_text,
                    "model": BEDROCK_MODEL_ID,
                    "status": "success",
                    "tools_used": tools_used_history
                }

        return {
            "reply": "AIOps Harness 도구 호출 최대 턴을 초과했습니다.",
            "status": "partial",
            "tools_used": tools_used_history
        }

    except Exception as e:
        return {
            "reply": f"AIOps Harness 실행 중 오류 발생: {str(e)}",
            "model": BEDROCK_MODEL_ID,
            "status": "error",
            "tools_used": tools_used_history
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

