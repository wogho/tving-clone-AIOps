"""
TVING AIOps Lab - Strands CLI / AgentCore Gateway MCP 비교 테스트 라우터
(순수 Strands CLI Export 및 AgentCore Gateway MCP 연동 정보 기반)
"""

import os
import time
import json
import boto3
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from config import AWS_REGION

router = APIRouter()

# ----------------------------------------------------------------------
# Bedrock AgentCore & Gateway MCP 연동 메타데이터
# ----------------------------------------------------------------------
HARNESS_ARN = "arn:aws:bedrock-agentcore:ap-northeast-2:761018884888:harness/aiops_harness-imKz42wjiX"
RUNTIME_ARN = "arn:aws:bedrock-agentcore:ap-northeast-2:761018884888:runtime/harness_aiops_harness-QbsTJoAWut"
ENDPOINT_ARN = "arn:aws:bedrock-agentcore:ap-northeast-2:761018884888:harness/aiops_harness-imKz42wjiX/harness-endpoint/DEFAULT"
GATEWAY_URL = "https://aiops-gateway-tweo0czpfr.gateway.bedrock-agentcore.ap-northeast-2.amazonaws.com/mcp"
GATEWAY_ARN = "arn:aws:bedrock-agentcore:ap-northeast-2:761018884888:gateway/aiops-gateway-tweo0czpfr"
GATEWAY_ROLE = "arn:aws:iam::761018884888:role/service-role/aiops_agentcore_gateway_role"
BEDROCK_MODEL_ID = "apac.anthropic.claude-3-5-sonnet-20240620-v1:0"
LAMBDA_FUNCTION_NAME = "aiops-agent-tools"
KB_ID = "CW9N0QAOGB"

# Bedrock Runtime & Lambda 클라이언트
try:
    bedrock_client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
except Exception:
    bedrock_client = None

try:
    lambda_client = boto3.client("lambda", region_name=AWS_REGION)
except Exception:
    lambda_client = None


class TestOpsChatRequest(BaseModel):
    message: str
    include_metrics: Optional[bool] = True


# Strands Exported Tool Configuration (17종 전체)
STRANDS_TOOL_CONFIG = {
    "tools": [
        {
            "toolSpec": {
                "name": "get_ec2_status",
                "description": "EC2 인스턴스의 상태 및 태그 정보를 조회합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "instance_identifier": {"type": "string", "description": "Instance ID 또는 Name Tag"}
                        }
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "list_s3_buckets",
                "description": "현재 AWS 계정에서 조회 가능한 모든 S3 Bucket 목록을 반환합니다.",
                "inputSchema": {"json": {"type": "object", "properties": {}}}
            }
        },
        {
            "toolSpec": {
                "name": "get_s3_objects",
                "description": "특정 S3 Bucket 내의 Object 목록(Key, 크기, 수정일시)을 조회합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {"bucket_name": {"type": "string", "description": "조회할 S3 버킷 이름"}},
                        "required": ["bucket_name"]
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "get_recent_logs",
                "description": "CloudWatch Logs에서 최근 로그를 실시간 검색합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "log_group": {"type": "string", "description": "로그 그룹 이름 (기본: /ecs/tving-backend)"},
                            "filter_pattern": {"type": "string", "description": "필터 패턴 (예: ERROR, WARN)"},
                            "minutes": {"type": "integer", "description": "조회 범위(분)"},
                            "limit": {"type": "integer", "description": "최대 로그 수"}
                        }
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "search_knowledge_base",
                "description": "Bedrock Knowledge Base에서 운영 매뉴얼 및 장애 조치 가이드를 RAG 검색합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {"query": {"type": "string", "description": "검색할 장애 상황 또는 키워드"}},
                        "required": ["query"]
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "analyze_traffic_by_path",
                "description": "API 경로별 요청 횟수와 트래픽 집중도를 정량 분석합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "log_group": {"type": "string", "description": "로그 그룹 (기본: /ecs/tving-backend)"},
                            "path_prefix": {"type": "string", "description": "API 경로 접두사"},
                            "minutes": {"type": "integer", "description": "분석 기간(분)"}
                        }
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "diagnose_content_popularity",
                "description": "평균 대비 급증한 화제작 콘텐츠를 자동 진단하고 대응 방안을 제시합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "log_group": {"type": "string", "description": "로그 그룹"},
                            "minutes": {"type": "integer", "description": "분석 기간(분)"}
                        }
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "get_content_info",
                "description": "콘텐츠 ID로 실제 작품 제목, 장르, 상세 정보를 조회합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {"content_id": {"type": "string", "description": "콘텐츠 ID"}},
                        "required": ["content_id"]
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "get_ecs_alarms",
                "description": "CloudWatch 경보의 현재 상태를 조회합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "alarm_name_prefix": {"type": "string", "description": "경보 접두사 (기본: tving)"},
                            "state_filter": {"type": "string", "description": "상태 필터 (ALARM/OK/ALL)"}
                        }
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "get_alarm_history",
                "description": "CloudWatch 경보의 최근 상태 변경 이력을 조회합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "alarm_name": {"type": "string", "description": "경보 이름"},
                            "hours": {"type": "integer", "description": "조회 시간(시간)"}
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
                            "log_group": {"type": "string", "description": "로그 그룹"},
                            "minutes": {"type": "integer", "description": "분석 시간(분)"}
                        }
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "diagnose_ecs_health",
                "description": "경보 상태와 5xx 에러를 종합하여 서비스 전반 건강 상태를 진단합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "log_group": {"type": "string", "description": "로그 그룹"},
                            "alarm_name_prefix": {"type": "string", "description": "경보 접두사"},
                            "minutes": {"type": "integer", "description": "분석 시간(분)"}
                        }
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "list_log_groups",
                "description": "CloudWatch 로그 그룹 목록을 조회합니다.",
                "inputSchema": {"json": {"type": "object", "properties": {"prefix": {"type": "string"}}}}
            }
        },
        {
            "toolSpec": {
                "name": "analyze_traffic_security",
                "description": "클라이언트 IP 패턴을 분석하여 정상 트래픽인지 악성 DoS 공격인지 판별하고 공격자 IP를 식별합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "log_group": {"type": "string", "description": "로그 그룹 (기본: /ecs/tving-backend)"},
                            "minutes": {"type": "integer", "description": "분석 기간(분)"}
                        }
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "block_malicious_ip",
                "description": "식별된 악성 공격자 IP를 AWS WAF IPSet(tving-blocked-ips)에 즉시 등록하여 실시간 차단합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "ip_address": {"type": "string", "description": "차단할 IP 주소"},
                            "reason": {"type": "string", "description": "차단 사유"}
                        },
                        "required": ["ip_address"]
                    }
                }
            }
        },
        {
            "toolSpec": {
                "name": "list_blocked_ips",
                "description": "현재 AWS WAF에 차단 등록된 IP 목록을 조회합니다.",
                "inputSchema": {"json": {"type": "object", "properties": {}}}
            }
        },
        {
            "toolSpec": {
                "name": "unblock_ip",
                "description": "오탐으로 차단된 IP를 AWS WAF 차단 목록에서 해제합니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {"ip_address": {"type": "string", "description": "차단 해제할 IP 주소"}},
                        "required": ["ip_address"]
                    }
                }
            }
        }
    ]
}


def execute_strands_tool(tool_name: str, tool_args: Dict[str, Any]) -> Any:
    """AgentCore Gateway MCP / Lambda 도구 실행기"""
    if tool_name == "search_knowledge_base":
        query = tool_args.get("query", "")
        try:
            agent_runtime = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)
            res = agent_runtime.retrieve(
                knowledgeBaseId=KB_ID,
                retrievalQuery={"text": query},
                retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": 3}}
            )
            results = []
            for item in res.get("retrievalResults", []):
                results.append({
                    "content": item.get("content", {}).get("text", "")[:400],
                    "score": item.get("score", 0.0),
                    "location": item.get("location", {}).get("s3Location", {}).get("uri", "")
                })
            return {"query": query, "count": len(results), "results": results}
        except Exception as e:
            return {"error": f"KB RAG 조회 실패: {str(e)}"}

    if not lambda_client:
        return {"error": "AWS Lambda 클라이언트를 사용할 수 없습니다."}

    payload = {"tool": tool_name, "arguments": tool_args}
    try:
        response = lambda_client.invoke(
            FunctionName=LAMBDA_FUNCTION_NAME,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload).encode("utf-8")
        )
        resp_payload = response["Payload"].read().decode("utf-8")
        data = json.loads(resp_payload)
        if isinstance(data, dict) and "body" in data:
            try:
                return json.loads(data["body"])
            except Exception:
                return data["body"]
        return data
    except Exception as e:
        return {"error": f"Tool 실행 실패 ({tool_name}): {str(e)}"}


@router.get("/info")
def get_testops_info():
    """AgentCore Gateway MCP 및 Strands 연동 정보 반환"""
    return {
        "architecture": "Strands CLI Export + AgentCore Gateway MCP Direct Architecture",
        "harness_arn": HARNESS_ARN,
        "runtime_arn": RUNTIME_ARN,
        "endpoint_arn": ENDPOINT_ARN,
        "gateway_url": GATEWAY_URL,
        "gateway_arn": GATEWAY_ARN,
        "gateway_role": GATEWAY_ROLE,
        "model": BEDROCK_MODEL_ID,
        "kb_id": KB_ID,
        "tools_count": len(STRANDS_TOOL_CONFIG["tools"]),
        "status": "ready"
    }


@router.post("/ai-chat")
def testops_ai_chat(request: TestOpsChatRequest, db: Session = Depends(get_db)):
    """
    Strands CLI Export 및 AgentCore Gateway MCP 연동 테스트 챗봇 엔드포인트
    """
    user_query = request.message
    start_time = time.time()

    # Strands 시스템 프롬프트
    system_prompt = f"""너는 TVING 클론 서비스의 AWS 클라우드 운영을 총괄 지원하는 AIOps/SecOps 지능형 운영자 어시스턴트(AIOps Harness Agent - Strands CLI Exported)이다.
TVING은 OTT 스트리밍 서비스이며, 콘텐츠 인기/화제성에 따라 특정 콘텐츠 API에 트래픽이 급격히 몰리는 경우가 발생할 수 있으며, 때로는 악의적인 DoS 공격을 받을 수도 있다.
너의 역할은 이러한 트래픽 이상 상황이나 일반 장애 상황이 발생했을 때, 실제 AWS 리소스 상태와 운영 매뉴얼을 함께 조회하여 운영자에게 정확한 근거 기반 분석을 제공하는 것이다.
사용자의 요청을 분석하고 필요한 Tool을 선택하여 실제 AWS 환경과 운영 매뉴얼을 확인한다.

## 사용 가능한 Tool (총 17종)
1. get_ec2_status: EC2 Instance ID 또는 Name Tag로 현재 상태와 Instance 이름 조회
2. list_s3_buckets: 현재 AWS 계정에서 조회 가능한 S3 Bucket 목록 조회
3. get_s3_objects: 특정 S3 Bucket의 Object 목록 조회
4. get_recent_logs: CloudWatch Logs의 최근 로그 검색 (기본: /ecs/tving-backend)
5. search_knowledge_base: AWS 운영 매뉴얼 Knowledge Base (KB ID: {KB_ID}) 검색
6. analyze_traffic_by_path: API 경로별 요청 횟수 및 트래픽 집중도 정량 분석
7. diagnose_content_popularity: 평균 대비 급증한 화제작 콘텐츠 자동 진단
8. get_content_info: 콘텐츠 ID로 실제 작품 제목 조회
9. get_ecs_alarms: CloudWatch 경보 현재 상태 조회
10. get_alarm_history: CloudWatch 경보의 최근 상태 변경 이력 조회
11. get_ecs_5xx_errors: CloudWatch Logs 5xx 에러 집계
12. diagnose_ecs_health: 서비스 전반 건강 상태 진단
13. list_log_groups: CloudWatch 로그 그룹 목록 조회
14. analyze_traffic_security: 클라이언트 IP 패턴을 분석하여 정상 트래픽인지 DoS 공격인지 판별
15. block_malicious_ip: 식별된 악성 IP를 AWS WAF에 즉시 등록하여 차단
16. list_blocked_ips: 현재 AWS WAF 차단 목록 조회
17. unblock_ip: 오탐된 IP 차단 해제

## 다음 원칙을 따른다
1. 현재 AWS 리소스 상태를 질문하면 반드시 실제 조회 Tool을 사용한다. 추측으로 답하지 않는다.
2. S3 Bucket 목록 확인에는 list_s3_buckets를 사용한다.
3. 특정 S3 Bucket의 Object 확인에는 get_s3_objects를 사용한다.
4. 일반적인 에러/장애 로그 확인에는 get_recent_logs를 사용한다.
5. 장애 대응 방법이나 운영 절차를 질문하면 search_knowledge_base를 사용한다.
6. 트래픽 급증/화제성/DoS 분석 시 analyze_traffic_security 및 analyze_traffic_by_path를 사용한다.
7. Tool에서 조회한 결과는 실제 Evidence로 사용한다.

## 최종 답변 형식 (하네스 플레이북 완벽 일치 규격)
반드시 다음 형식으로 정리하여 답변한다:

분석 결과를 정리해드리겠습니다:

현재 상태:
- [현재 인프라 또는 조회/에러 발생 상황 요약]

Evidence:
- 로그 그룹 / 리소스: [대상 리소스명, 예: AWS S3, /ecs/tving-backend]
- 조회/분석 기간: [현재 시점 / 최근 N분]
[추가 Evidence 데이터 목록]

이상 여부:
- [현재 시점에서의 이상 유무 판정 (특별한 이상 없음 / 정상 트래픽 급증 / 실제 장애 / DoS 공격 감지)]

가능한 원인:
- [수집된 데이터를 바탕으로 한 원인 분석 또는 '해당 없음 (정상 조회)']

추가 확인 항목:
1. [교차 검증을 위해 추가로 살펴볼 리소스나 관련 버킷/로그]
2. [추가 모니터링 항목]

권장 대응 절차:
1. [운영자가 즉시 실행할 수 있는 구체적인 조치 방안 또는 후속 가이드]
2. [모니터링 유지 및 후속 대응 가이드]

추가적인 분석이나 다른 버킷/로그의 정보가 필요하시다면 말씀해 주세요.
"""

    if not bedrock_client:
        return {
            "reply": "⚠️ Bedrock Runtime 클라이언트 초기화에 실패했습니다.",
            "model": "error",
            "status": "error",
            "tools_used": []
        }

    conversation_messages = [
        {"role": "user", "content": [{"text": user_query}]}
    ]

    tools_used = []
    max_turns = 6
    turn_count = 0
    final_reply = ""

    while turn_count < max_turns:
        turn_count += 1
        try:
            response = bedrock_client.converse(
                modelId=BEDROCK_MODEL_ID,
                messages=conversation_messages,
                system=[{"text": system_prompt}],
                toolConfig=STRANDS_TOOL_CONFIG,
                inferenceConfig={"maxTokens": 2048, "temperature": 0.1, "topP": 0.9}
            )
        except Exception as e:
            return {
                "reply": f"❌ Strands Bedrock 호출 오류: {str(e)}",
                "model": BEDROCK_MODEL_ID,
                "status": "error",
                "tools_used": tools_used,
                "meta": {
                    "architecture": "Strands CLI Export + AgentCore Gateway MCP",
                    "harness_arn": HARNESS_ARN,
                    "gateway_url": GATEWAY_URL
                }
            }

        output_msg = response.get("output", {}).get("message", {})
        stop_reason = response.get("stopReason")
        content_blocks = output_msg.get("content", [])

        conversation_messages.append(output_msg)

        if stop_reason == "tool_use":
            tool_results_blocks = []
            for block in content_blocks:
                if "toolUse" in block:
                    tool_use = block["toolUse"]
                    tool_use_id = tool_use["toolUseId"]
                    tool_name = tool_use["name"]
                    tool_args = tool_use.get("input", {})

                    # Execute Strands tool via Gateway/Lambda
                    tool_result = execute_strands_tool(tool_name, tool_args)

                    tools_used.append({
                        "tool": tool_name,
                        "input": tool_args,
                        "output_summary": str(tool_result)[:300],
                        "source": "Strands MCP Gateway"
                    })

                    tool_results_blocks.append({
                        "toolResult": {
                            "toolUseId": tool_use_id,
                            "content": [{"json": tool_result if isinstance(tool_result, dict) else {"result": tool_result}}]
                        }
                    })

            conversation_messages.append({
                "role": "user",
                "content": tool_results_blocks
            })

        elif stop_reason in ["end_turn", "stop_sequence", "max_tokens"] or not stop_reason:
            text_chunks = [b["text"] for b in content_blocks if "text" in b]
            final_reply = "".join(text_chunks).strip()
            break

    elapsed = round(time.time() - start_time, 2)

    return {
        "reply": final_reply or "AIOps Strands 진단 결과를 생성하지 못했습니다.",
        "model": BEDROCK_MODEL_ID,
        "status": "success",
        "tools_used": tools_used,
        "latency_seconds": elapsed,
        "meta": {
            "mode": "Strands CLI Exported Runtime",
            "architecture": "Bedrock AgentCore Gateway MCP Direct Mode",
            "harness_arn": HARNESS_ARN,
            "runtime_arn": RUNTIME_ARN,
            "endpoint_arn": ENDPOINT_ARN,
            "gateway_url": GATEWAY_URL,
            "gateway_arn": GATEWAY_ARN
        }
    }
