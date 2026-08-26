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
AIOPS_TOOL_LAMBDA = os.getenv("AIOPS_TOOL_LAMBDA", "aiops-agent-tools")

# Bedrock Agent Runtime 클라이언트
try:
    bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)
except Exception:
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
                                "description": "EC2 인스턴스 ID 또는 Name 태그"
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
                "description": "지정한 CloudWatch Logs 그룹에서 최근 N분 동안의 에러 로그(기본 패턴: ERROR)를 검색합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "log_group": {
                                "type": "string",
                                "description": "CloudWatch 로그 그룹 이름 (예: /ecs/tving-backend)"
                            },
                            "minutes": {
                                "type": "integer",
                                "description": "최근 몇 분간의 로그를 검색할지 (기본 10)"
                            },
                            "filter_pattern": {
                                "type": "string",
                                "description": "필터링할 에러 패턴 문자열 (기본 ERROR)"
                            }
                        },
                        "required": ["log_group"]
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "search_knowledge_base",
                "description": "Bedrock Knowledge Base에 저장된 클라우드 운영 매뉴얼(S3, EC2, CloudWatch 장애 대응 가이드)에서 관련 문서를 검색합니다.",
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
        }
    ]
}


def execute_tool_call(tool_name: str, tool_args: dict):
    """AIOps Harness 도구 라우터"""
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
            tool_args.get("log_group", ""),
            tool_args.get("minutes", 10),
            tool_args.get("filter_pattern", "ERROR")
        )
    elif tool_name == "search_knowledge_base":
        return tool_search_knowledge_base(tool_args.get("query", ""))
    else:
        return {"error": f"Unknown tool: {tool_name}"}


# ----------------------------------------------------------------------
# AIOps Agent Harness Chat Handler (with Multi-Turn Tool Calling)
# ----------------------------------------------------------------------

@router.post("/ai-chat")
def ops_ai_chat(request: OpsChatRequest, db: Session = Depends(get_db)):
    """
    운영자 전용 AIOps 대화형 장애 진단 및 모니터링 AI 챗봇 (aiops_harness 5대 Tool-Calling 연동)
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
사용 가능한 5가지 도구(Tool)를 적극 활용하여, 시스템 상태 확인, 장애 로그 분석, S3 버킷 및 파일 점검, Bedrock Knowledge Base 운영 매뉴얼 조회를 수행하고 정확한 근거 기반의 조치 가이드를 제공하세요.

[사용 가능한 AIOps 도구]
1. get_ec2_status: EC2 인스턴스 상태 및 헬스체크
2. list_s3_buckets: S3 버킷 목록 확인
3. get_s3_objects: 특정 S3 버킷 내부 객체 목록 확인
4. get_recent_logs: CloudWatch Logs 에러 로그 실시간 검색
5. search_knowledge_base: Bedrock Knowledge Base (KB ID: {KB_ID}) 장애 대응 매뉴얼 RAG 검색

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

