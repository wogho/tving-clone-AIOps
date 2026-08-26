## 1. 프로젝트 개요

- **팀 구성**: 3인 1팀
- **프로젝트 주제**: AWS에 애플리케이션 배포를 위한 아키텍처를 구축하고, 생성형 AI를 활용한 AIOps 운영자동화 기능을 구현한다.
- **개발 방식**: Kiro를 활용한 바이브코딩
- **프로젝트 핵심**: 애플리케이션 자체 개발보다 AWS 운영환경 구축과 AIOps 구현에 집중한다.

이번 프로젝트에서는 애플리케이션 코드를 처음부터 개발하지 않는다.

수업에서 제공하는 애플리케이션 코드를 이용하여 AWS에 서비스 환경을 구축한 뒤, 별도의 AIOps 시스템을 직접 설계하고 구현한다.

전체 흐름은 다음과 같다.

```
제공된 애플리케이션 코드
        ↓
AWS 운영환경 구축
        ↓
ECS / RDS / API Gateway 배포
        ↓
CloudWatch 운영 데이터 수집
        ↓
AIOps Backend 개발
        ↓
Amazon Bedrock 활용
        ↓
AI 기반 장애 분석
        ↓
AIOps Dashboard 구현
```
## 2.2 Backend Private Architecture 구성

Backend는 외부에 직접 노출하지 않는다.

외부에서 Backend에 접근할 수 있는 유일한 경로는 API Gateway이다.

```
Internet
   │
   ▼
API Gateway
   │
   │ VPC Link
   ▼
Internal ALB
   │
   ▼
ECS Fargate
   │
   ▼
Application Backend
```

필수 조건:

- API Gateway를 Backend의 유일한 외부 진입점으로 사용한다.
- ALB는 Internal로 구성한다.
- ECS Task는 Private Subnet에 배치한다.
- ECS Task에 Public IP를 할당하지 않는다.
- ALB 또는 ECS Task에 외부 사용자가 직접 접근하지 않는다.
- Frontend에서는 API Gateway Endpoint만 호출한다.

## 2.3 Observability 구성

애플리케이션 운영 상태를 확인할 수 있도록 다음 데이터를 수집한다.

```
Application Logs
ECS 상태
ALB 상태
CloudWatch Alarm
RDS 상태
CloudWatch Metrics
```

---

## 2.4 AIOps 시스템 구축

애플리케이션과 별도로 AIOps용 Dashboard와 Backend를 구축한다.

AIOps 시스템은 운영 데이터를 수집하고 분석하여 운영자의 판단을 지원한다.

---

## 2.5 생성형 AI 활용

Amazon Bedrock을 이용하여 다음 기능을 구현한다.

```
로그 분석
장애 요약
장애 원인 추정
Evidence 제공
운영 매뉴얼 검색
권장 대응 방법 제안
```

# 3. 전체 프로젝트 아키텍처

프로젝트는 크게 두 영역으로 분리한다.

```
1. 서비스 애플리케이션 영역

2. AIOps 운영 영역
```

---

# 4. 서비스 애플리케이션 영역

서비스 애플리케이션은 실제 사용자에게 제공되는 서비스이다.

                         사용자
                           │
                           ▼
                       Route 53
                           │
                           ▼
                      CloudFront
                           │
                           ▼
                          S3
                       Frontend
                           │
                           │ HTTPS REST API
                           ▼
                      API Gateway
                           │
                       VPC Link
                           │
                           ▼
                     Internal ALB
                           │
                           ▼
                     ECS Fargate
                 Application Backend
                           │
                           ▼
                          RDS


# 5. 서비스 애플리케이션 구성 요소

## Frontend

```
Route 53
   ↓
CloudFront
   ↓
S3 Origin
```

Frontend 코드는 제공한다.

배포를 위해 다음 작업을 수행한다.

- S3 Bucket 생성
- Frontend 코드 업로드
- CloudFront Distribution 생성
- OAC 구성
- Route 53 사용자 도메인 연결
- Frontend API Endpoint 설정


## Backend

Backend 코드는 제공한다.

배포를 위해 다음 작업을 수행한다.

```
Docker Build
   ↓
ECR Push
   ↓
ECS Task Definition
   ↓
ECS Service
   ↓
Internal ALB
   ↓
API Gateway
```


## Database

Amazon RDS를 직접 구성한다.

예:

```
Amazon RDS MySQL 
```

또는 프로젝트 상황에 따라 PostgreSQL을 사용할 수 있다.

Backend에서 RDS에 접근한다.

```
ECS Fargate
      │
      ▼
     RDS
```

RDS는 Private Subnet에 배치한다.

tving -clone-template-main


AdministratorAccess의 자격 증명 가져오기

AdministratorAccess이(가) 있는 계정 user6(761018884888)의 액세스 권한을 생성합니다.
다음 옵션 중 하나를 사용하여 프로그래밍 방식으로 또는 AWS CLI에서 AWS 리소스에 액세스할 수 있습니다. 필요한 빈도로 자격 증명을 검색할 수 있습니다.


macOS and Linux

Windows

PowerShell
AWS IAM Identity Center 자격 증명(권장)
자격 증명의 기간을 연장하려면 aws configure sso  명령을 사용하여 자동으로 자격 증명을 검색하도록 AWS CLI를 구성하는 것이 좋습니다. 자세히 알아보기 
SSO 시작 URL

https://identitycenter.amazonaws.com/ssoins-723089322eab111a

SSO 리전

ap-northeast-2

옵션 1: AWS 환경 변수 설정
명령 프롬프트에 다음 텍스트를 붙여넣고 AWS 환경 변수를 설정합니다. 자세히 알아보기 
SET AWS_ACCESS_KEY_ID=ASIA_SAMPLE_KEY_ID_MASKED
SET AWS_SECRET_ACCESS_KEY=sample_secret_key_masked_here
SET AWS_SESSION_TOKEN=sample_session_token_masked_here

옵션 2: AWS 자격 증명 파일에 프로필 추가
다음 텍스트를 복사하여 AWS 자격 증명 파일(%USERPROFILE%\.aws\credentials)에 붙여넣습니다. 자세히 알아보기 
[761018884888_AdministratorAccess]
aws_access_key_id=ASIA_SAMPLE_KEY_ID_MASKED
aws_secret_access_key=sample_secret_key_masked_here
aws_session_token=sample_session_token_masked_here



---

# AIOps 구축 계획서

## 프로젝트명

**Amazon Bedrock 기반 TVING Clone SRE AIOps 플랫폼**

> 장애 발생 시 AI가 원인을 자동 진단(RCA)하고, 운영 매뉴얼을 RAG로 검색하여 복구 가이드를 제시하며, Lambda Tool로 자동 복구까지 실행하는 Cloud-Native AIOps 시스템

---

## 1. 핵심 컨셉

기존 CloudWatch는 **"CPU 100%", "5xx 에러 발생"** 같은 숫자만 알려줄 뿐, **왜 발생했는지(원인)** 와 **어떻게 조치해야 하는지(대응)**는 알려주지 못한다.

본 AIOps는 다음 3가지를 자동화한다.

```
1. 장애 원인 자동 진단 (Root Cause Analysis)
   "CPU가 왜 높은가? → 트래픽 폭주인가, DB 락인가, 코드 버그인가?"

2. 운영 매뉴얼 RAG 검색 (Knowledge Base)
   "이 장애 유형에 맞는 대응 절차를 사내 매뉴얼에서 찾아 제시"

3. 자동 복구 실행 (Lambda Tool)
   "Fargate Task 재시작, 오토스케일링 조정 등 즉시 실행"
```

---

## 2. 전체 아키텍처

```
                         사용자
                           │
                           ▼
                       Route 53
                           │
                           ▼
                      CloudFront
                      ┌────┴────┐
                      ▼         ▼
               S3 (Frontend)  API Gateway (/api/*)
                                │
                            VPC Link
                                │
                                ▼
                          Internal ALB
                                │
                                ▼
                          ECS Fargate
                     (TVING Backend - FastAPI)
                                │
                                ▼
                          RDS PostgreSQL
                                │
         ┌──────────────────────┴──────────────────────┐
         ▼                                              ▼
  CloudWatch Logs                              CloudWatch Metrics
  (Application Logs, ALB Logs)                 (CPU, Memory, ALB Latency)
         │                                              │
         └──────────────────┬───────────────────────────┘
                            │
                            ▼
                  ┌─────────────────────┐
                  │  Bedrock AIOps 엔진  │
                  │                     │
                  │  Agent (Claude 3.5)  │
                  │  + Knowledge Base   │
                  │    (운영 매뉴얼 RAG)  │
                  │  + Lambda Tools     │
                  └────────┬────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
       장애 원인 진단   매뉴얼 RAG    자동 복구
       (RCA 리포트)    (대응 가이드)  (Task 재시작)
```

---

## 3. 사용 가능한 기존 리소스 (이미 준비된 것)

### 3.1 장애 주입 테스트 API (백엔드 템플릿에 추가 필요)

| Method | Endpoint | 설명 | 장애 유형 |
| --- | --- | --- | --- |
| POST | `/ops/cpu-load` | 인위적 CPU 부하 발생 | CPU 과부하 |
| POST | `/ops/delay` | 인위적 응답 지연 발생 | API 응답 지연 |
| POST | `/ops/db-error` | DB Connection 에러 강제 발생 | DB 장애 |

### 3.2 운영 매뉴얼 (S3 → Knowledge Base 업로드용)

```
aiops-manuals/
├── ec2-troubleshooting.md        ← EC2 SSH 접속 장애 대응 절차
├── cloudwatch-troubleshooting.md ← CloudWatch 로그 확인 매뉴얼
├── s3-troubleshooting.md         ← S3 장애 대응 매뉴얼
└── incident-response.md          ← 장애 대응 절차 (4단계)
```

### 3.3 AI 챗봇 (Streamlit + FastAPI `/api/chat`)

- Streamlit UI (`:8501`) → FastAPI → Bedrock으로 콘텐츠 추천
- `chat.py`에 TODO 주석 해제하여 Bedrock 연동

---

## 4. AIOps Lambda Tool 설계

Bedrock Agent가 호출할 Lambda Tool 목록:

### Tool 1: `get_fargate_status`
- **기능**: ECS Fargate Service/Task 상태 조회 (Running/Stopped/Pending)
- **사용 시점**: 장애 발생 시 현재 서비스 상태 확인
- **Boto3**: `ecs.describe_services()`, `ecs.describe_tasks()`

### Tool 2: `get_recent_logs`
- **기능**: CloudWatch Logs에서 최근 N분간 ERROR/WARN 로그 조회
- **사용 시점**: 장애 원인 파악을 위한 로그 수집
- **Boto3**: `logs.filter_log_events()`

### Tool 3: `get_metrics`
- **기능**: CloudWatch Metrics에서 CPU/Memory/ALB Latency 조회
- **사용 시점**: 리소스 병목 여부 확인
- **Boto3**: `cloudwatch.get_metric_statistics()`

### Tool 4: `search_knowledge_base`
- **기능**: Bedrock Knowledge Base에서 운영 매뉴얼 검색 (RAG)
- **사용 시점**: 장애 유형에 맞는 대응 절차 검색
- **Boto3**: `bedrock_agent_runtime.retrieve()`

### Tool 5: `restart_fargate_task`
- **기능**: 문제가 있는 Fargate Task를 강제 종료 (ECS가 자동으로 새 Task 재생성)
- **사용 시점**: AIOps가 Task 재시작이 필요하다고 판단한 경우
- **Boto3**: `ecs.stop_task()` → ECS Desired Count에 의해 자가치유(Self-Healing)

---

## 5. 데모 시나리오 (10분 발표)

### Act 1. 서비스 시연 + RAG 챗봇 (0~2분)

- TVING 클론 서비스 정상 동작 시연 (콘텐츠 목록, 상세 조회)
- Streamlit AI 챗봇으로 콘텐츠 추천 시연
  - "범죄 스릴러 장르 추천해줘" → Bedrock이 DB 데이터 기반 추천

### Act 2. CPU 과부하 장애 → AIOps 자동 진단 & 복구 (2~5분)

```
1. /ops/cpu-load 호출 → Fargate CPU 급증
2. CloudWatch 알람 발생
3. AIOps 엔진 자동 투입:
   - Tool 호출: get_metrics() → "CPU 95%, 정상 범위 초과"
   - Tool 호출: get_recent_logs() → "애플리케이션 에러 로그 없음, 외부 부하"
   - Tool 호출: search_knowledge_base() → "운영 매뉴얼: CPU 과부하 시 Task 재시작 권장"
4. AIOps 판정: "외부 부하로 인한 CPU 과부하. Task 재시작으로 복구 가능."
5. Tool 호출: restart_fargate_task() → Fargate 자가치유(Self-Healing)
6. 대시보드에 RCA 리포트 표출
```

### Act 3. DB 장애 → AIOps 자동 진단 & 매뉴얼 제시 (5~8분)

```
1. /ops/db-error 호출 → DB Connection 에러 발생 → 500 에러
2. AIOps 엔진 자동 투입:
   - Tool 호출: get_recent_logs() → "sqlalchemy.exc.OperationalError: connection refused"
   - Tool 호출: get_metrics() → "CPU 정상, DB 커넥션 수 0"
   - Tool 호출: search_knowledge_base() → "장애 대응 절차 4단계 매뉴얼"
3. AIOps 판정: "DB 커넥션 장애. RDS 상태 확인 및 보안그룹 점검 필요."
4. 자연어 RCA 리포트 + 운영 매뉴얼 기반 복구 가이드 자동 생성
```

### 마무리: 아키텍처 설명 + Q&A (8~10분)

---

## 6. 3일 구축 일정

### Day 1: 서비스 배포 (인프라 구축)

- [ ] VPC / Subnet / Security Group 구성
- [ ] RDS PostgreSQL 생성 및 데이터 투입 (init.sql, seed.sql)
- [ ] Backend Docker Build → ECR Push
- [ ] ECS Fargate Task Definition & Service 생성
- [ ] Internal ALB 생성 및 Target Group 연결
- [ ] API Gateway + VPC Link 구성
- [ ] Frontend S3 + CloudFront 배포
- [ ] /ops/* 장애 주입 엔드포인트 추가 (cpu-load, delay, db-error)

### Day 2: AIOps 엔진 구축

- [ ] 운영 매뉴얼 S3 업로드 → Bedrock Knowledge Base 생성
- [ ] Lambda Tool 함수 작성 (get_fargate_status, get_recent_logs, get_metrics, search_knowledge_base, restart_fargate_task)
- [ ] Lambda Execution Role 생성 (IAM)
- [ ] Bedrock Agent 생성 (Claude 3.5 Sonnet)
- [ ] Agent에 Tool 연결 (AgentCore Gateway 또는 직접 Lambda 연동)
- [ ] AI 챗봇 (chat.py) Bedrock 연동 활성화
- [ ] AIOps 파이프라인 테스트 (장애 주입 → 진단 → 매뉴얼 검색)

### Day 3: 대시보드 & 데모 안정화

- [ ] AIOps 대시보드 UI 구성 (Streamlit 또는 별도 프론트엔드)
- [ ] 데모 시나리오 리허설 (Act 1, Act 2, Act 3)
- [ ] 발표 자료(PPT) 아키텍처 다이어그램 제작
- [ ] 10분 라이브 데모 최종 점검

---

## 7. 확장 고려사항 (여유 시 추가)

Day 2~3에 핵심 기능이 안정적으로 동작한 이후, 여유가 있다면 다음 기능을 추가로 검토한다.

| 우선순위 | 확장 기능 | 설명 |
| --- | --- | --- |
| P1 | 트래픽 패턴 분석 | ALB 로그에서 특정 IP 편중 호출 감지 → 정상 트래픽 vs 비정상 공격 분류 |
| P2 | Slack/SNS 알림 연동 | AIOps 진단 결과를 Slack 채널 또는 SNS로 자동 전송 |
| P3 | 배포 직후 오탐 억제 | Fargate Task 시작 시간과 배포 이력 대조 → 워밍업 알람 자동 기각 |
| P4 | 보안 AIOps | GuardDuty 연동, API 호출 패턴 기반 이상 탐지 |

---

# 8. 구축 완료된 AWS 리소스 목록 (1~5단계)

### 1. DNS & CDN (Frontend 진입점)
- **서비스**: Route 53 (호스팅 영역)
  - **리소스명**: `user6.cloudai.store` (ID: `Z01237461U76PLXNFBH5M`)
- **서비스**: Route 53 (A 레코드)
  - **리소스명**: `tving.user6.cloudai.store`, `user6.cloudai.store`
- **서비스**: CloudFront (배포)
  - **리소스명**: `d33nd37o8cwhu4.cloudfront.net` (ID: `E1D9AUK8PXTXMF`)

### 2. Frontend 정적 호스팅
- **서비스**: S3 버킷
  - **리소스명**: `tving-frontend-761018884888`

### 3. API Gateway & VPC Link (Backend 진입점)
- **서비스**: API Gateway (HTTP API)
  - **리소스명**: `tving-api` (ID: `45yz97o406`)
  - **엔드포인트**: `https://45yz97o406.execute-api.ap-northeast-2.amazonaws.com`
- **서비스**: API Gateway VPC Link
  - **리소스명**: `tving-vpc-link` (ID: `rjgsp9`)

### 4. 로드 밸런서 (Internal ALB & Target Group)
- **서비스**: Application Load Balancer (Internal)
  - **리소스명**: `tving-internal-alb`
- **서비스**: ALB 대상 그룹 (Backend)
  - **리소스명**: `tving-backend-tg` (Port: 8000)
- **서비스**: ALB 대상 그룹 (Streamlit)
  - **리소스명**: `tving-streamlit-tg` (Port: 8501)

### 5. 컨테이너 & 컴퓨팅 (ECR & ECS Fargate)
- **서비스**: ECR 리포지토리
  - **리소스명**: `tving-backend` (`761018884888.dkr.ecr.ap-northeast-2.amazonaws.com/tving-backend`)
  - **리소스명**: `tving-streamlit` (`761018884888.dkr.ecr.ap-northeast-2.amazonaws.com/tving-streamlit`)
- **서비스**: ECS 클러스터
  - **리소스명**: `tving-cluster`
- **서비스**: ECS 서비스
  - **리소스명**: `tving-backend-service`
  - **리소스명**: `tving-streamlit-service`
- **서비스**: ECS 작업 정의 (Task Definition)
  - **리소스명**: `tving-backend-task`
  - **리소스명**: `tving-streamlit-task`

### 6. 데이터베이스 (Database)
- **서비스**: RDS (PostgreSQL 인스턴스)
  - **리소스명**: `tving-postgres`
  - **엔드포인트**: `tving-postgres.czsesi44seki.ap-northeast-2.rds.amazonaws.com`

### 7. 네트워크 및 보안 (VPC & Security Groups)
- **서비스**: VPC
  - **리소스명**: `vpc-0e3526aca56d3f9eb`
- **서비스**: 보안 그룹 (Security Group)
  - **리소스명**: `bedrock-ecs-alb-sg` (`sg-08a068d0642b71bb4`)
  - **리소스명**: `bedrock-ecs-task-sg` (`sg-015393c2ee9cb5be2`)
  - **리소스명**: `tving-rds-sg` (`sg-03fc4c8dfc0604231`)
  - **리소스명**: `bedrock-endpoint-sg` (`sg-0061915c09b8dc015`)
  - **리소스명**: `bedrock-pub-sg-01` (`sg-0967e94a9af2a4dc5`)
  - **리소스명**: `bedrock-pri-sg-01` (`sg-04f145d9d77f36959`)

---

# 9. 3. AIOps 영역 (운영/모니터링) 전용 독립 인프라 구축 완료 내역

서비스 애플리케이션 영역(2번)과 100% 분리된 **AIOps 전용 독립 인프라 스택**을 구축 완료했습니다.

```text
                                [운영자 (Operator)]
                                         │
                                         ▼
                             Route 53 (ops.user6.cloudai.store)
                                         │
                                         ▼
                      AIOps 전용 CloudFront (d1iiges96q9wvx.cloudfront.net)
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   │                                           │ (/api/*)
                   ▼                                           ▼
      AIOps 전용 S3 Dashboard                  AIOps 전용 API Gateway (tving-aiops-api)
 (tving-aiops-dashboard-761018884888)                          │
                                                               ▼ (AIOps VPC Link: zdyees)
                                                  AIOps 전용 Internal ALB
                                                (tving-aiops-internal-alb)
                                                               │
                                                               ▼ (Port: 8000)
                                                    AIOps 전용 ECS Fargate
                                                (tving-aiops-backend-service)
                                                               │
                                  ┌────────────────────────────┴────────────────────────────┐
                                  ▼                                                         ▼
                      [모니터링 / 데이터 수집]                                      [AI / 분석 서비스]
        • CloudWatch Metrics / Logs Anomaly Detection                • Amazon Bedrock (Claude 3 Haiku / 3.5 Sonnet)
        • RDS / ECS / ALB 헬스체크 및 슬로우 쿼리 진단                 • SRE & SecOps AIOps 대화형 어시스턴트
```

---

### 1. DNS & CDN (AIOps 전용 진입점)
- **Route 53 A 레코드**: `ops.user6.cloudai.store` ➔ AIOps 전용 CloudFront 배포 Alias
- **CloudFront 배포 (AIOps 전용 신규 생성)**:
  - **배포 ID**: `E2M3JJB7O2UE4O`
  - **도메인**: `d1iiges96q9wvx.cloudfront.net`
  - **CNAME (Alias)**: `ops.user6.cloudai.store`
  - **ACM 인증서**: `arn:aws:acm:us-east-1:761018884888:certificate/955cd3f4-0959-4a3c-861d-1649418d3d00`

### 2. AIOps Dashboard (AIOps 전용 S3 호스팅)
- **S3 버킷 (AIOps 전용 신규 생성)**: `tving-aiops-dashboard-761018884888`
- **CloudFront OAC**: `E383X8QDQIGVOT` (`tving-aiops-oac`)
- **접속 URL**: `https://ops.user6.cloudai.store` (또는 `https://ops.user6.cloudai.store/pages/ops.html`)
- **주요 기능**:
  - **실시간 인프라 헬스 패널**: ECS Fargate, RDS PostgreSQL 레이턴시, CloudWatch Anomaly Detection (±2σ Band), Amazon Bedrock 엔진 상태 실시간 조회
  - **Bedrock AIOps 지능형 운영자 챗봇 (AI Chatbot UI)**: 운영자의 장애 진단 질의, 원인 분석 요청, 복구 가이드라인 실시간 생성
  - **AIOps 장애 시뮬레이션 패널**: CPU 부하(`/api/ops/cpu-load`), 응답 지연(`/api/ops/delay`), 500 DB 에러(`/api/ops/db-error`) 원클릭 트리거 및 복구 검증

### 3. API Gateway & VPC Link (AIOps 전용 Backend 진입점)
- **API Gateway HTTP API (AIOps 전용 신규 생성)**:
  - **API ID**: `52fj3dpe8f` (`tving-aiops-api`)
  - **엔드포인트**: `https://52fj3dpe8f.execute-api.ap-northeast-2.amazonaws.com`
- **VPC Link (AIOps 전용 신규 생성)**:
  - **VPC Link ID**: `zdyees` (`tving-aiops-vpc-link`)
  - **연결 서브넷**: `subnet-094eaab9b9f052ef2`, `subnet-0a68af96e075544b8` (Private Subnets)
  - **보안 그룹**: `sg-08a068d0642b71bb4` (`bedrock-ecs-alb-sg`)

### 4. 로드 밸런서 (AIOps 전용 Internal ALB & Target Groups)
- **Application Load Balancer (AIOps 전용 신규 생성)**:
  - **ALB 이름**: `tving-aiops-internal-alb` (Internal, Private Subnet)
  - **DNS**: `internal-tving-aiops-internal-alb-126748483.ap-northeast-2.elb.amazonaws.com`
- **ALB 대상 그룹 (AIOps 전용 신규 생성)**:
  - **Backend TG**: `tving-aiops-backend-tg` (Port: 8000, Target: IP, Health: `/health`)
  - **Streamlit TG**: `tving-aiops-streamlit-tg` (Port: 8501, Target: IP, Health: `/_stcore/health`)
- **ALB Listeners**:
  - Port 80 ➔ `tving-aiops-backend-tg`
  - Port 8501 ➔ `tving-aiops-streamlit-tg`

### 5. 컴퓨팅 (AIOps 전용 ECS Fargate Service)
- **ECS 클러스터**: `tving-cluster`
- **ECS 서비스 (AIOps 전용 신규 생성)**:
  - **서비스명**: `tving-aiops-backend-service`
  - **작업 정의**: `tving-backend-task:4`
  - **태스크 수**: 1 (Fargate, Private Subnets, Public IP Disabled)

---

# 10. 서비스 영역(2번) vs AIOps 영역(3번) 독립 인프라 비교표

| 구분 | 2. 서비스 애플리케이션 영역 (User) | 3. AIOps 영역 (Operator / Monitoring) |
| :--- | :--- | :--- |
| **사용자 대상** | 일반 시청자 / 사용자 | 인프라 운영자 / SRE / SecOps 엔지니어 |
| **진입 도메인 (Route 53)** | `user6.cloudai.store`, `tving.user6.cloudai.store` | **`ops.user6.cloudai.store`** |
| **CloudFront 배포** | `E1D9AUK8PXTXMF` (`d33nd37o8cwhu4`) | **`E2M3JJB7O2UE4O` (`d1iiges96q9wvx`) [전용 배포]** |
| **S3 Dashboard/Web 버킷** | `tving-frontend-761018884888` | **`tving-aiops-dashboard-761018884888` [전용 버킷]** |
| **API Gateway** | `45yz97o406` (`tving-api`) | **`52fj3dpe8f` (`tving-aiops-api`) [전용 API]** |
| **VPC Link** | `rjgsp9` (`tving-vpc-link`) | **`zdyees` (`tving-aiops-vpc-link`) [전용 VPC Link]** |
| **Internal ALB** | `tving-internal-alb` | **`tving-aiops-internal-alb` [전용 Internal ALB]** |
| **ECS Fargate Service** | `tving-backend-service`, `tving-streamlit-service` | **`tving-aiops-backend-service` [전용 ECS Service]** |
| **주요 역할** | OTT 영상 콘텐츠 스트리밍 및 AI 추천 | 실시간 메트릭 수집, Bedrock AIOps 장애 진단 & 자율 격리 |

---

# 11. AIOps Harness 연동 구조 및 5대 도구 명세

AIOps 관제 대시보드([tving-aiops-dashboard-761018884888](https://ap-northeast-2.console.aws.amazon.com/s3/buckets/tving-aiops-dashboard-761018884888?region=ap-northeast-2) / `https://ops.user6.cloudai.store`)의 AI 챗봇에 탑재된 **AIOps Agent Harness (Bedrock Tool-Calling Engine)**의 연동 구조입니다.

### 1. Harness 아키텍처 흐름도 (End-to-End Flow)

```text
[운영자 질의 입력] (예: "S3 버킷 목록과 kjh-aiops-manuals 버킷 파일 확인해줘")
       │
       ▼
[AIOps Dashboard 챗봇 UI] (https://ops.user6.cloudai.store)
       │
       ▼ (HTTPS POST /api/ops/ai-chat)
[AIOps API Gateway (52fj3dpe8f) ➔ VPC Link (zdyees) ➔ Internal ALB]
       │
       ▼ (Port: 8000)
[FastAPI 백엔드 AIOps Harness Engine (backend/routers/ops.py)]
       │
       ▼ (Converse API with Tool Configuration)
[Amazon Bedrock (Claude 3 Haiku / 3.5 Sonnet)]
       │
       ├── [Tool 1 자율 호출] ➔ list_s3_buckets() ➔ S3 API 실행 결과 주입
       ├── [Tool 2 자율 호출] ➔ get_s3_objects("kjh-aiops-manuals") ➔ S3 버킷 파일 목록 주입
       ├── [Tool 3 자율 호출] ➔ search_knowledge_base("S3 AccessDenied") ➔ Bedrock KB (CW9N0QAOGB) RAG 검색
       ├── [Tool 4 자율 호출] ➔ get_ec2_status("i-xxx" or "Name") ➔ EC2 인스턴스/상태검사 조회
       └── [Tool 5 자율 호출] ➔ get_recent_logs("/ecs/tving-backend") ➔ CloudWatch Logs ERROR 검색
       │
       ▼ (모든 도구 실행 결과를 종합 추론하여 마크다운 포맷팅)
[최종 응답 생성] ➔ 🛠️ AIOps Harness 도구 실행 이력 뱃지(Tool Trace) + 원인 분석 및 대응 가이드 표출
```

---

### 2. AIOps Harness 5대 도구 (Tools) 상세 명세

| 도구명 (Tool Name) | 파라미터 (Parameters) | 역할 및 기능 | 대상 AWS 서비스 |
| :--- | :--- | :--- | :--- |
| **`list_s3_buckets`** | *(없음)* | 현재 AWS 계정에 존재하는 전체 S3 Bucket 목록 및 생성일 반환 | Amazon S3 (`s3:ListAllMyBuckets`) |
| **`get_s3_objects`** | `bucket_name` (필수), `prefix` (선택), `max_keys` (기본 20) | 특정 S3 버킷 내의 객체(Key, 크기, 수정일시) 목록 조회 | Amazon S3 (`s3:ListObjectsV2`) |
| **`search_knowledge_base`** | `query` (필수, 검색 키워드) | Bedrock Knowledge Base에 등록된 클라우드 운영 매뉴얼(S3/EC2/CloudWatch 장애 가이드) RAG 검색 | Amazon Bedrock Agent Runtime (`Retrieve`) |
| **`get_ec2_status`** | `instance_identifier` (ID 또는 Name) | EC2 인스턴스의 상태(running/stopped), 인스턴스/시스템 상태 검사, IP 조회 | Amazon EC2 (`DescribeInstances`, `DescribeInstanceStatus`) |
| **`get_recent_logs`** | `log_group` (필수), `minutes` (기본 10), `filter_pattern` (기본 ERROR) | 지정한 CloudWatch Logs 그룹에서 최근 N분간의 에러 로그 검색 | Amazon CloudWatch Logs (`FilterLogEvents`) |

---

### 3. Bedrock Knowledge Base (KB) 및 S3 매뉴얼 동기화 현황
- **Knowledge Base ID**: `CW9N0QAOGB` (`kjh-ops-manuals`)
- **데이터 소스 ID**: `TPWBMJCRAO` (`kjh-ops-manuals-source`)
- **S3 매뉴얼 버킷**: `s3://kjh-aiops-manuals/`
  - `s3-troubleshooting.md`: S3 버킷 확인 및 AccessDenied 트러블슈팅 가이드
  - `ec2-troubleshooting.md`: EC2 인스턴스 장애 대응 가이드
  - `cloudwatch-troubleshooting.md`: CloudWatch 메트릭/로그 이상 징후 분석 가이드
  - `incident-response.md`: 인프라 장애 긴급 대응 절차
- **IAM 실행 역할 해결**: `AmazonBedrockExecutionRoleForKnowledgeBase_qo8uu`의 S3 정책을 `arn:aws:s3:::kjh-aiops-manuals/*`로 전체 허용하여 `AccessDenied` 없이 Ingestion Job 동기화 완료 (`status: COMPLETE`).

---

### 4. AIOps 대시보드 UI 연동 기능
- **도구 실행 이력 시각화 (Tool Execution Trace)**: 챗봇이 답변 시 호출한 도구명과 입력값을 상단 파란색 뱃지로 투명하게 표시
- **원클릭 빠른 질의 (Quick Prompts)**:
  - `🗄️ S3 버킷 & 파일 확인`: `list_s3_buckets`, `get_s3_objects` 자동 실행
  - `📖 S3 KB 매뉴얼 검색`: `search_knowledge_base` 자동 실행
  - `🖥️ EC2/인프라 상태 점검`: `get_ec2_status` 자동 실행
  - `📜 에러 로그 검색`: `get_recent_logs` 자동 실행
  - `🔍 전체 헬스체크`: 시스템 종합 진단 리포트 생성



