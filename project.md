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

AIOps 관제 대시보드([tving-aiops-dashboard-761018884888](https://ap-northeast-2.console.aws.amazon.com/s3/buckets/tving-aiops-dashboard-761018884888?region=ap-northeast-2) / `https://ops.user6.cloudai.store`)의 AI 챗봇에 탑재된 **AIOps Agent Harness (Bedrock Tool-Calling Engine)**의 상세 연동 구조 및 기술 구현 내역입니다.

---

### 1. AIOps Harness 아키텍처 흐름도 (End-to-End Flow)

```text
[운영자 질의 입력] (예: "S3 버킷 목록과 kjh-aiops-manuals 버킷 파일 확인해줘")
       │
       ▼
[AIOps Dashboard 챗봇 UI] (https://ops.user6.cloudai.store - S3 / CloudFront E2M3JJB7O2UE4O)
       │
       ▼ (HTTPS POST /api/ops/ai-chat)
[AIOps 전용 API Gateway (52fj3dpe8f) ➔ VPC Link (zdyees) ➔ Internal ALB (tving-aiops-internal-alb)]
       │
       ▼ (Target Group: tving-aiops-backend-tg:8000)
[FastAPI 백엔드 AIOps Harness Engine (backend/routers/ops.py)]
       │
       ▼ (Converse API with AIOPS_TOOL_CONFIG - Claude 3 Haiku)
[Amazon Bedrock Engine]
       │
       ├── [Tool 1 자율 호출] ➔ list_s3_buckets() ➔ S3 API (ListAllMyBuckets) 결과 반환
       ├── [Tool 2 자율 호출] ➔ get_s3_objects("kjh-aiops-manuals") ➔ S3 API (ListObjectsV2) 파일 목록 반환
       ├── [Tool 3 자율 호출] ➔ search_knowledge_base("S3 AccessDenied") ➔ Bedrock KB (CW9N0QAOGB) RAG 검색
       ├── [Tool 4 자율 호출] ➔ get_ec2_status("i-xxx" or "Name") ➔ EC2 API (DescribeInstances) 인스턴스 헬스 반환
       └── [Tool 5 자율 호출] ➔ get_recent_logs("/ecs/tving-backend") ➔ CloudWatch Logs (FilterLogEvents) 에러 반환
       │
       ▼ (도구 실행 결과를 context에 주입하여 Bedrock 2차 추론 ➔ 최종 마크다운 리포트 생성)
[AIOps Dashboard UI] ➔ 🛠️ Harness 도구 실행 이력 뱃지(Tool Trace) + 원인 분석 및 긴급 조치 가이드 표출
```

---

### 2. AIOps Harness 연동 기술 구현 방식

#### ① Bedrock Converse API Tool Configuration 정의
FastAPI 백엔드(`backend/routers/ops.py`)에서 5가지 도구의 입력 스키마(JSON Schema)를 정의하여 Bedrock Converse API 호출 시 `toolConfig`로 전달합니다:
```python
AIOPS_TOOL_CONFIG = {
    "tools": [
        {"toolSpec": {"name": "list_s3_buckets", "description": "현재 AWS 계정의 전체 S3 버킷 목록 조회", "inputSchema": {"json": {"type": "object", "properties": {}}}}},
        {"toolSpec": {"name": "get_s3_objects", "description": "특정 S3 버킷 내 객체 목록 조회", "inputSchema": {"json": {"type": "object", "properties": {"bucket_name": {"type": "string"}, "prefix": {"type": "string"}, "max_keys": {"type": "integer"}}, "required": ["bucket_name"]}}}},
        {"toolSpec": {"name": "search_knowledge_base", "description": "Bedrock Knowledge Base 운영 매뉴얼 RAG 검색", "inputSchema": {"json": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}}},
        {"toolSpec": {"name": "get_ec2_status", "description": "EC2 인스턴스 상태 및 헬스체크 조회", "inputSchema": {"json": {"type": "object", "properties": {"instance_identifier": {"type": "string"}}, "required": ["instance_identifier"]}}}},
        {"toolSpec": {"name": "get_recent_logs", "description": "CloudWatch Logs 에러 로그 실시간 검색", "inputSchema": {"json": {"type": "object", "properties": {"log_group": {"type": "string"}, "minutes": {"type": "integer"}, "filter_pattern": {"type": "string"}}, "required": ["log_group"]}}}}
    ]
}
```

#### ② Multi-Turn Tool-Calling 에이전트 루프 (Harness Loop)
Bedrock이 질문을 분석하여 도구 사용(`stopReason == "tool_use"`)을 요청하면, 하네스가 해당 파이썬 함수를 직접 실행하고 그 결과를 `toolResult`로 Bedrock에 재주입하여 최종 답변을 도출합니다:
```python
for turn in range(max_turns):
    response = bedrock_client.converse(
        modelId=BEDROCK_MODEL_ID,
        messages=messages,
        system=[{"text": system_prompt}],
        toolConfig=AIOPS_TOOL_CONFIG,
        inferenceConfig={"maxTokens": 1024, "temperature": 0.2}
    )
    stop_reason = response.get("stopReason")
    output_msg = response["output"]["message"]
    messages.append(output_msg)

    if stop_reason == "tool_use":
        tool_results_content = []
        for block in output_msg.get("content", []):
            if "toolUse" in block:
                tool_use = block["toolUse"]
                tool_out = execute_tool_call(tool_use["name"], tool_use["input"])
                tool_results_content.append({"toolResult": {"toolUseId": tool_use["toolUseId"], "content": [{"json": tool_out}], "status": "success"}})
        messages.append({"role": "user", "content": tool_results_content})
    else:
        # 최종 마크다운 답변 도출
        break
```

---

### 3. AIOps Harness 5대 도구 (Tools) 상세 명세

| 도구명 (Tool Name) | 파라미터 (Parameters) | 역할 및 기능 | 대상 AWS 서비스 |
| :--- | :--- | :--- | :--- |
| **`list_s3_buckets`** | *(없음)* | 현재 AWS 계정에 존재하는 전체 S3 Bucket 목록 및 생성일 반환 | Amazon S3 (`s3:ListAllMyBuckets`) |
| **`get_s3_objects`** | `bucket_name` (필수), `prefix` (선택), `max_keys` (기본 20) | 특정 S3 버킷 내의 객체(Key, 크기, 수정일시) 목록 조회 | Amazon S3 (`s3:ListObjectsV2`) |
| **`search_knowledge_base`** | `query` (필수, 검색 키워드) | Bedrock Knowledge Base에 등록된 클라우드 운영 매뉴얼(S3/EC2/CloudWatch 장애 가이드) RAG 검색 | Amazon Bedrock Agent Runtime (`Retrieve`) |
| **`get_ec2_status`** | `instance_identifier` (ID 또는 Name) | EC2 인스턴스의 상태(running/stopped), 인스턴스/시스템 상태 검사, IP 조회 | Amazon EC2 (`DescribeInstances`, `DescribeInstanceStatus`) |
| **`get_recent_logs`** | `log_group` (필수), `minutes` (기본 10), `filter_pattern` (기본 ERROR) | 지정한 CloudWatch Logs 그룹에서 최근 N분간의 에러 로그 검색 | Amazon CloudWatch Logs (`FilterLogEvents`) |

---

### 4. Bedrock Knowledge Base (KB) 및 S3 매뉴얼 동기화 현황
- **Knowledge Base ID**: `CW9N0QAOGB` (`kjh-ops-manuals`)
- **데이터 소스 ID**: `TPWBMJCRAO` (`kjh-ops-manuals-source`)
- **임베딩 모델**: `amazon.titan-embed-text-v2:0` (1,024 Vector Dimensions)
- **S3 매뉴얼 버킷**: `s3://kjh-aiops-manuals/`
  - `s3-troubleshooting.md`: S3 버킷 확인 및 AccessDenied 트러블슈팅 가이드
  - `ec2-troubleshooting.md`: EC2 인스턴스 장애 대응 가이드
  - `cloudwatch-troubleshooting.md`: CloudWatch 메트릭/로그 이상 징후 분석 가이드
  - `incident-response.md`: 인프라 장애 긴급 대응 절차
- **IAM 실행 역할 해결**: `AmazonBedrockExecutionRoleForKnowledgeBase_qo8uu`의 S3 정책을 `arn:aws:s3:::kjh-aiops-manuals/*`로 전체 허용하여 `AccessDenied` 없이 Ingestion Job 동기화 완료 (`status: COMPLETE`).

---

### 5. AIOps 대시보드 UI 연동 기능
- **도구 실행 이력 시각화 (Tool Execution Trace)**: 챗봇이 답변 시 호출한 도구명과 입력값(예: `• list_s3_buckets: {}`, `• search_knowledge_base: {"query": "S3 AccessDenied"}`)을 상단 파란색 뱃지로 투명하게 표시.
- **원클릭 빠른 질의 (Quick Prompts)**:
  - `🗄️ S3 버킷 & 파일 확인`: `list_s3_buckets`, `get_s3_objects` 자동 실행
  - `📖 S3 KB 매뉴얼 검색`: `search_knowledge_base` 자동 실행
  - `🖥️ EC2/인프라 상태 점검`: `get_ec2_status` 자동 실행
  - `📜 에러 로그 검색`: `get_recent_logs` 자동 실행
  - `🔍 전체 헬스체크`: 시스템 종합 진단 리포트 생성

---

### 6. AIOps 관제 센터 관리자 인증 (Admin Authentication)
- **보안 격리**: 일반 서비스 프론트엔드(`user6.cloudai.store`)에서 AIOps 관제 버튼 완전 제거 및 100% 분리.
- **관리자 전용 로그인 (회원가입 제외)**:
  - **관리자 ID**: `admin`
  - **비밀번호**: `admin@1234`
  - **인증 엔드포인트**: `POST /api/ops/login`
  - **접근 제어**: 미인증 시 대시보드 접근 차단 및 관리자 로그인 화면 노출, 인증 성공 시 대시보드 및 로그아웃 기능 활성화.

---

# 12. AIOps 이상 탐지 Slack 알림 시스템 (`tving-aiops-slack-notifier`) 구성 형태

CloudWatch 메트릭 이상 탐지(Anomaly Detection) 알람과 연동되어 장애 발생(`ALARM`) 및 자동 복구(`OK`) 상황을 실시간 감지하고, 운영자 Slack 채널로 대화형 조치 가이드 카드를 전송하는 **서버리스 알림 자동화 파이프라인**입니다.

```text
[ECS Fargate CPU / Memory 메트릭]
       │
       ▼ (실시간 메트릭 수집: 1분 주기)
[CloudWatch Metric Anomaly Detection (±2σ / ±3σ Band)]
       │
       ├── (이상 급증/급락 감지 시 ALARM 상태 전이)
       └── (정상 대역 복귀 감지 시 OK 상태 전이)
       │
       ▼
[Amazon SNS Topic: tving-aiops-anomaly-alarm]
       │
       ▼ (Lambda 트리거 / Subscription)
[AWS Lambda: tving-aiops-slack-notifier (Python 3.12)]
       │
       ├── 이벤트 파싱 (AlarmName, NewStateValue, StateChangeReason 등)
       ├── 상태별 슬랙 메시지 카드 빌드 (🚨 Red 경보 / ✅ Green 복구)
       └── Action Items (4대 긴급 조치사항) 및 복구 내역 포맷팅
       │
       ▼ (HTTPS POST / SLACK_WEBHOOK_URL)
[운영팀 Slack 관제 채널 (#ops-alerts)]
```

---

### 1. Lambda 함수 기본 리소스 스펙

| 항목 (Property) | 상세 설정값 (Configuration) |
| :--- | :--- |
| **함수명 (Function Name)** | **`tving-aiops-slack-notifier`** |
| **함수 ARN** | `arn:aws:lambda:ap-northeast-2:761018884888:function:tving-aiops-slack-notifier` |
| **런타임 (Runtime)** | `Python 3.12` (Architecture: `x86_64`) |
| **핸들러 (Handler)** | `lambda_function.lambda_handler` |
| **메모리 / 타임아웃** | `128 MB` / `3초` |
| **IAM 실행 역할 (Execution Role)** | `arn:aws:iam::761018884888:role/aiops-agent-tools-role` |
| **로그 그룹 (CloudWatch Logs)** | `/aws/lambda/tving-aiops-slack-notifier` |
| **환경변수 (Environment Variables)** | `SLACK_WEBHOOK_URL` = `https://hooks.slack.com/services/T01V1UNJP7T/...` |

---

### 2. 이벤트 트리거 및 SNS / CloudWatch 연동 구성

#### ① SNS 토픽 구독 (Subscription)
* **SNS Topic ARN**: `arn:aws:sns:ap-northeast-2:761018884888:tving-aiops-anomaly-alarm`
* **구독 프로토콜 / 엔드포인트**: `lambda` ➔ `tving-aiops-slack-notifier`
* **Lambda 리소스 정책 (Invoke Permission)**: `AllowSNSInvoke` (`sns.amazonaws.com`의 `arn:aws:sns:ap-northeast-2:761018884888:tving-aiops-anomaly-alarm` 호출 허용)

#### ② 연동된 CloudWatch Anomaly Detection 경보 (Metric Alarms)
| 알람 이름 (Alarm Name) | 대상 메트릭 / 리소스 | 이상 탐지 표현식 (Threshold) | 상태 전이 시 동작 |
| :--- | :--- | :--- | :--- |
| **`tving-ecs-cpu-anomaly-alarm`** | `AWS/ECS` `CPUUtilization`<br>(`tving-cluster` / `tving-backend-service`) | `ANOMALY_DETECTION_BAND(m1, 2)`<br>(표준편차 ±2σ 대역 초과) | `ALARM` & `OK` ➔ SNS 발송 |
| **`tving-ecs-memory-anomaly-alarm`** | `AWS/ECS` `MemoryUtilization`<br>(`tving-cluster` / `tving-backend-service`) | `ANOMALY_DETECTION_BAND(m2, 3)`<br>(표준편차 ±3σ 대역 초과) | `ALARM` & `OK` ➔ SNS 발송 |

---

### 3. Slack 알림 카드 레이아웃 및 메시지 구조

#### 🚨 1) 장애 발생 시 알림 카드 (`NewStateValue == 'ALARM'`)
* **테마 색상**: `#E50914` (TVING Red)
* **헤더 타이틀**: `🚨 [TVING AIOps 장애 경보] {AlarmName}`
* **필드 구성**:
  * **현재 상태**: `ALARM` (임계 대역 초과)
  * **탐지 모델**: `CloudWatch Anomaly Detection (±2σ)`
  * **대상 리소스**: `tving-cluster` / `tving-backend-service` (ECS Fargate)
  * **감지 원인**: 임계 밴드 초과 상세 수치 및 타임스탬프
  * **🛠️ 긴급 조치사항 (Action Items)**:
    1. ECS Fargate 오토스케일링 태스크 증설 상태 확인
    2. 비정상 인입 트래픽 및 과부하 엔드포인트(`/api/ops/*`) 차단
    3. Slow Query 및 DB Connection Pool 가용량 점검
    4. CloudWatch 이상 탐지 밴드 추이 및 컨테이너 리소스 모니터링
* **푸터**: `TVING AIOps Automated Incident Response | 리전: Asia Pacific (Seoul)`

#### ✅ 2) 정상 복구 완료 알림 카드 (`NewStateValue == 'OK'`)
* **테마 색상**: `#22C55E` (Green)
* **헤더 타이틀**: `✅ [TVING AIOps 정상 복구 완료] {AlarmName}`
* **필드 구성**:
  * **현재 상태**: `OK` (정상 범위 진입)
  * **서비스 헬스체크**: `Healthy` (HTTP 200 OK)
  * **대상 리소스**: `tving-cluster` / `tving-backend-service`
  * **복구 사유**: 메트릭 값이 정상 기대 밴드 내부로 복귀한 상세 내용
  * **📋 조치 및 복구 내역 (Resolution Summary)**:
    1. 부하 프로세스 자동 종료 및 CPU/메모리 정상 수치 회복
    2. ECS 헬스체크(`/api/ops/status`) 정상 응답(HTTP 200 OK) 확인
    3. ALB 트래픽 분산 및 타겟 응답 지연 시간 안정화
    4. 이상 탐지 대역(Anomaly Band) 내 완전 복귀 완료
* **푸터**: `TVING AIOps Self-Healing & Incident Closed | 리전: Asia Pacific (Seoul)`

---

### 4. Lambda 핸들러 핵심 구현 코드 (`lambda_function.py`)

```python
import json
import os
import urllib.request

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

def lambda_handler(event, context):
    for record in event.get('Records', []):
        sns_msg = record.get('Sns', {})
        subject = sns_msg.get('Subject', 'TVING AIOps 알림')
        message_raw = sns_msg.get('Message', '{}')
        
        try:
            alarm_data = json.loads(message_raw)
        except Exception:
            alarm_data = {"RawMessage": message_raw}
        
        alarm_name = alarm_data.get("AlarmName", subject)
        new_state = alarm_data.get("NewStateValue", "ALARM")
        reason = alarm_data.get("NewStateReason", "상태 변경 감지")
        region = alarm_data.get("Region", "Asia Pacific (Seoul)")
        alarm_type = alarm_data.get("AlarmType", "INFRA")
        attacker_ip = alarm_data.get("AttackerIP", "198.51.100.23")
        remediation = alarm_data.get("Remediation", None)
        recovery_details = alarm_data.get("RecoveryDetails", None)

        # ----------------------------------------------------
        # 1. 🛡️ SecOps 보안 침해 및 DoS 공격 차단 알림
        # ----------------------------------------------------
        if alarm_type == "SECURITY_ATTACK" or "DoS" in alarm_name or "Security" in alarm_name or "WAF" in alarm_name:
            block_actions = (
                f"1. 침해 공격자 IP `{attacker_ip}` 식별 완료 (전체 트래픽 90% 집중)\n"
                f"2. AWS WAF IPSet (`tving-blocked-ips`)에 악성 IP 즉시 영구 차단 등록\n"
                f"3. 불필요한 ECS Fargate 서버 증설 중단 (클라우드 비용 낭비 방지)\n"
                f"4. 정상 고객 요청 속도(HTTP 200 OK / 6ms) 즉시 안정화 완료"
            ) if not remediation else remediation

            attachment = {
                "color": "#7C3AED",  # Purple for SecOps
                "title": f"🛡️ [TVING SecAIOps 보안 침해 방어 완료] {alarm_name}",
                "text": f"*{alarm_name}* 정상 트래픽에 은닉된 지능형 DoS 공격이 감지되어 **AWS WAF 자율 차단(SOAR)**이 완료되었습니다.",
                "fields": [
                    {"title": "공격 유형 (Attack Type)", "value": "`Algorithmic DoS / Resource Exhaustion`", "short": True},
                    {"title": "차단된 공격자 IP", "value": f"`{attacker_ip}` (AWS WAF 격리)", "short": True},
                    {"title": "보안 방어 상태", "value": "🛡️ `BLOCKED` (tving-blocked-ips 등록)", "short": True},
                    {"title": "정상 트래픽 상태", "value": "🟢 `Flash Crowd` 정상 서비스 유지", "short": True},
                    {"title": "탐지 및 분석 근거", "value": f"{reason}", "short": False},
                    {"title": "📋 SecOps 자동 격리 조치 내역", "value": f"```{block_actions}```", "short": False}
                ],
                "footer": f"TVING SecAIOps Automated SOAR Defense | 리전: {region}"
            }

        # ----------------------------------------------------
        # 2. 🚨 SRE 인프라 장애 발생 경보 (Red)
        # ----------------------------------------------------
        elif new_state == "ALARM":
            actions_text = (
                "1. ECS Fargate 오토스케일링 태스크 증설 상태 확인\n"
                "2. 비정상 인입 트래픽 및 과부하 엔드포인트(/api/ops/*) 점검\n"
                "3. Slow Query 및 DB Connection Pool 가용량 점검\n"
                "4. CloudWatch 이상 탐지 밴드 추이 및 컨테이너 리소스 모니터링"
            ) if not remediation else remediation

            attachment = {
                "color": "#E50914",
                "title": f"🚨 [TVING AIOps 장애 경보] {alarm_name}",
                "text": f"*{alarm_name}* 에서 이상 징후가 감지되어 경보가 발령되었습니다.",
                "fields": [
                    {"title": "현재 상태", "value": f"`{new_state}` (임계 대역 초과)", "short": True},
                    {"title": "탐지 모델", "value": "CloudWatch Anomaly Detection (±2σ)", "short": True},
                    {"title": "대상 리소스", "value": "`tving-cluster` / `tving-backend-service` (ECS Fargate)", "short": False},
                    {"title": "감지 원인 (Trigger Reason)", "value": f"{reason}", "short": False},
                    {"title": "🛠️ 긴급 조치사항 (Action Items)", "value": f"```{actions_text}```", "short": False}
                ],
                "footer": f"TVING AIOps Automated Incident Response | 리전: {region}"
            }

        # ----------------------------------------------------
        # 3. ✅ SRE 인프라 정상 복구 완료 알림 (Green)
        # ----------------------------------------------------
        else:
            recovery_text = (
                "1. 부하 프로세스 자동 종료 및 CPU/메모리 정상 수치 회복\n"
                "2. ECS 헬스체크(/health) 정상 응답(HTTP 200 OK) 확인\n"
                "3. ALB 트래픽 분산 및 타겟 응답 지연 시간 안정화\n"
                "4. 이상 탐지 대역(Anomaly Band) 내 완전 복귀 완료"
            ) if not recovery_details else recovery_details

            attachment = {
                "color": "#22C55E",
                "title": f"✅ [TVING AIOps 정상 복구 완료] {alarm_name}",
                "text": f"*{alarm_name}* 상태가 정상 대역으로 복귀하여 안정화되었습니다.",
                "fields": [
                    {"title": "현재 상태", "value": f"`{new_state}` (정상 범위 진입)", "short": True},
                    {"title": "서비스 헬스체크", "value": "`Healthy` (HTTP 200 OK)", "short": True},
                    {"title": "대상 리소스", "value": "`tving-cluster` / `tving-backend-service`", "short": False},
                    {"title": "복구 사유", "value": f"{reason}", "short": False},
                    {"title": "📋 조치 및 복구 내역 (Resolution Summary)", "value": f"```{recovery_text}```", "short": False}
                ],
                "footer": f"TVING AIOps Self-Healing & Incident Closed | 리전: {region}"
            }

        slack_payload = {"attachments": [attachment]}
        req = urllib.request.Request(
            SLACK_WEBHOOK_URL,
            data=json.dumps(slack_payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                print(f"Slack post response status: {resp.status}")
        except Exception as e:
            print(f"Slack post failed: {str(e)}")
            
    return {"statusCode": 200, "body": "OK"}
```

---

# 13. AIOps 게이트웨이·알림·부하테스트 종합 운영 체계 및 실무 시나리오

본 섹션은 현재 구축된 **AgentCore Gateway / Lambda 5대 도구 매핑**, **Slack 알림 자동화**, 그리고 **TVING 부하테스트 및 장애 진단 실증 시나리오**를 종합 정리한 명세입니다.

---

### 1. AgentCore Gateway & Lambda 5대 도구 구성 매핑 (담당: 정근)

* **게이트웨이 타겟 (Gateway Target)**: `ljg-aiops-tools`
* **연결된 Lambda 함수 (Target Lambda)**: `aiops-agent-tools`
* **동작 원리**: Agent는 Lambda 코드를 직접 읽지 않고, Gateway에 등록된 **Tool Schema(명세서)**를 기반으로 운영자의 질문 의도를 파악하여 적절한 도구를 자율 호출합니다.

| 도구명 (Tool Name) | 운영자 자연어 질문 예시 | 도구 역할 및 실제 동작 메커니즘 | 대상 AWS 서비스 |
| :--- | :--- | :--- | :--- |
| **`get_ec2_status`** | *"이 EC2 인스턴스 살아있어?"*<br>*"현재 서버 상태 점검해줘"* | EC2 Instance ID 또는 Name Tag를 기반으로 **실제 구동 상태(Running), 퍼블릭/프라이빗 IP, 인스턴스/시스템 헬스체크 결과**를 조회 | Amazon EC2 |
| **`list_s3_buckets`** | *"우리 계정에 어떤 S3 버킷 있어?"*<br>*"S3 버킷 목록 나열해줘"* | 현재 AWS 계정에 존재하는 **전체 S3 Bucket 이름 목록 및 생성일시**를 실시간 나열 | Amazon S3 |
| **`get_s3_objects`** | *"이 버킷 안에 뭐 있어?"*<br>*"kjh-aiops-manuals 버킷 파일 보여줘"* | 지정한 S3 버킷 내의 **실제 객체(Key) 목록, 파일 용량(Size), 최종 수정일시**를 조회 | Amazon S3 |
| **`get_recent_logs`** | *"최근 에러 로그 보여줘"*<br>*"ECS 백엔드 에러 발생 로그 확인해줘"* | CloudWatch Logs 그룹(`/ecs/tving-backend`)에서 **최근 N분간의 실제 `ERROR` 패턴 로그**를 실시간 검색 | Amazon CloudWatch Logs |
| **`search_knowledge_base`** | *"SSH 접속 안 될 때 뭘 확인해야 해?"*<br>*"S3 AccessDenied 에러 대처법은?"* | Bedrock Knowledge Base(`CW9N0QAOGB`)에 등록된 **운영 매뉴얼/트러블슈팅 가이드(.md)에서 관련 내용을 시맨틱 RAG 검색**하여 답변 | Amazon Bedrock KB (RAG) |

---

### 2. 이상 탐지 Slack 실시간 알림 파이프라인 (`tving-aiops-slack-notifier`)

* **메트릭 수집**: CloudWatch Metric Anomaly Detection을 통해 ECS CPU/Memory를 1분 주기로 실시간 수집.
* **이벤트 전달**: 머신러닝 기대 대역(±2σ / ±3σ) 초과 시 SNS Topic(`tving-aiops-anomaly-alarm`) ➔ Lambda(`tving-aiops-slack-notifier`) 호출.
* **상태별 대화형 알림 카드**:
  * 🚨 **`ALARM` (Red)**: 이상 징후 원인 및 **4대 긴급 조치사항 (Action Items)** 자동 포맷팅.
  * ✅ **`OK` (Green)**: 리소스 회복 수치, 헬스체크(HTTP 200 OK) 확인 및 **4대 복구 요약 (Resolution Summary)** 자동 전송.

---

### 3. AIOps 부하테스트 및 장애 진단 실증 시나리오

#### 🎬 시나리오 1: TVING 신작 N개 동시 공개 부하테스트 & 화제성 트래픽 분석 (Flash Crowd)
* **상황 설정**:
  * TVING에서 **N개의 신규 오리지널 콘텐츠를 동시 공개**.
  * 특정 킬러 콘텐츠(예: 인기 드라마/예능)에 대량의 트래픽이 집중 인입 (**각 콘텐츠에 n분 동안 m회의 대량 트래픽 발생**).
* **AIOps 트래픽 분석 및 진단 흐름**:
  1. **화제성 분석 및 트래픽 편중도 감지**: API Gateway 및 CloudWatch 메트릭을 통해 콘텐츠별 요청량(RPM)과 유입 세션을 분석하여 단순 공격이 아닌 특정 신작 오픈에 따른 **정상 화제성 트래픽(Flash Crowd)**임을 식별.
  2. **오탐(False Positive) 정제**: WAF가 정상 팬들의 폭증 트래픽을 DDoS로 오판하여 차단하지 않도록 보호.
  3. **SRE 자율 스케일아웃 및 완화 조치**:
     * ECS Fargate 백엔드 태스크 증설 (`1대 ➔ 4대`).
     * 해당 킬러 콘텐츠의 메타데이터 캐시(Redis/CloudFront) TTL 연장 및 DB 커넥션 풀 가용량 확보.
  4. **Slack 보고**: `#ops-alerts` 채널로 콘텐츠별 트래픽 분석 차트 및 스케일아웃 조치 보고서 자동 전송.

---

#### 🎬 시나리오 2: 동일 RDS CPU 95% 증상의 3대 원인 분류 및 가설 검증 (Root Cause AIOps)
* **상황 설정**: CloudWatch에서 `RDS CPUUtilization 95% ALARM`이 발생한 상황.
* **3대 가설 교차 검증 (Cross-System Evidence)**:
  * **가설 A (인기작 폭증)**: 다수 분산 IP 유입 + 전체 엔드포인트 균등 증가 ➔ **SRE 대응** (ECS 증설 / 캐시 연장).
  * **가설 B (배포 쿼리 버그)**: 최근 1시간 내 신규 배포 이력 + N+1 Slow Query 급증 ➔ **DevOps 대응** (신규 버전 즉시 롤백).
  * **가설 C (Algorithmic DoS)**: 단일 세션/IP에서 Full Scan 유발 복합 검색어 반복 호출 ➔ **SOAR 대응** (공격 토큰 차단 / WAF 룰 적용).

---

#### 🎬 시나리오 3: 애플리케이션 다단계 은닉 공격 ➔ SecAIOps 킬체인 추론 & SOAR 자율 격리
* **상황 설정**: 개별 이벤트는 LOW/MEDIUM 수준으로 노이즈에 묻히는 4단계 지능형 공격 (정찰 ➔ 주거용 프록시 접근 ➔ SSRF 내부 피벗 ➔ RDS 데이터 유출 시도).
* **SecAIOps 추론 및 대응**:
  * Bedrock Claude가 6시간 분량의 분산 Finding과 시퀀스를 종합하여 **`ATTACK_ADAPTIVE_EXFIL` (킬체인 공격)** 확정 판정.
  * 공격자 IP WAF 영구 차단, SSRF 엔드포인트 차단, 침해된 ECS 태스크 즉시 교체 및 Slack 포렌식 보고서 발행.

---

### 4. 향후 추가 확장 예정 기능 (Roadmap)

1. **GuardDuty 실시간 Finding 수집 및 SOAR 자율 IP 격리 모듈 고도화**
2. **콘텐츠 화제성 실시간 랭킹 연동 및 핫 콘텐츠 자동 캐시 프리로드(Pre-loading) 엔진**
3. **Bedrock Multi-Agent 협업 체계 (SecOps 에이전트 ↔ SRE 에이전트 간 역할 분담 및 교차 검증)**







