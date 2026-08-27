# CloudWatch vs GuardDuty 보안 영역 및 AIOps 융합 심층 비교 분석

본 문서는 **Amazon CloudWatch**와 **AWS GuardDuty**의 보안 감시 영역, 각 서비스가 지닌 고유한 오탐(False Positive) 및 미탐(False Negative) 영역을 분석하고, **TVING OTT 플랫폼의 비즈니스 시나리오**에 적합한 서비스 선택 가이드 및 **AIOps 결합 시의 시너지 효과**를 비교 정리한 기술 명세서입니다.

---

## 1. CloudWatch의 보안 영역 (Security & Observability Scope)

CloudWatch는 본래 **인프라 및 애플리케이션 가시성(Observability) 및 상태 모니터링** 도구이나, 수집되는 로그와 메트릭을 통해 **운영 레벨의 보안 이상 징후**를 실시간 감시합니다.

```text
[CloudWatch 보안 감시 영역]
├── 1. 애플리케이션 & 액세스 로그 (ALB, API Gateway, ECS Fargate 컨테이너 로그)
│      └── HTTP 4xx/5xx 에러 급증, SQL Injection/XSS 파라미터 유입, 인증 실패 반복
├── 2. 네트워크 & 감사 로그 (VPC Flow Logs, CloudTrail Logs)
│      └── 거부된 패킷(REJECT) 급증, 비인가 보안그룹 수정, Root 계정 로그인
├── 3. 메트릭 이상 탐지 (Metric Anomaly Detection - ML Band ±2σ/±3σ)
│      └── CPUUtilization, MemoryUtilization, RequestCount, Latency 비정상 스파이크
└── 4. Contributor Insights
       └── 상위 호출 IP 편중도, 특정 엔드포인트(/api/ops/*) DoS 공격성 집중도 분석
```

* **주요 탐지 메커니즘**:
  * **임계치 기반 (Static Threshold)**: 특정 지표가 고정 수치 초과 시 알람 (예: CPU > 90%).
  * **머신러닝 이상 탐지 (Anomaly Detection Band)**: 시계열 학습을 통해 일일/주간 트래픽 주기를 반영하여 기대 범위를 벗어난 이상치 탐지.
  * **필터 패턴 (Metric Filters)**: 로그 내 `ERROR`, `Unauthorized`, `AccessDenied` 키워드 빈도 추출.

---

## 2. GuardDuty의 보안 영역 (Threat Detection Scope)

GuardDuty는 AWS 계정, 워크로드 및 데이터의 **지능형 위협 탐지(Intelligent Threat Detection)** 전용 보안 서비스로, AWS 위협 인텔리전스(Threat Intelligence)와 머신러닝을 기반으로 동작합니다.

```text
[GuardDuty 보안 감시 영역]
├── 1. 계정 및 IAM 침해 (IAM/Account Compromise)
│      └── 유출된 크리덴셜 사용(InstanceCredentialExfiltration), 비정상 리전 API 호출
├── 2. 네트워크 및 인프라 침해 (EC2 / ECS / Container Threat)
│      └── C&C(명령제어) 서버 통신, Tor/악성 익명 프록시 접속, 암호화폐 채굴(CryptoCurrency)
├── 3. 데이터 저장소 위협 (S3 / RDS Protection)
│      └── 비정상 IP의 S3 대량 객체 조회/인출(Exfiltration), RDS 비인가 로그인 시도
└── 4. 정찰 및 스캔 (Reconnaissance)
       └── 포트 프로브(PortProbe), 비인가 취약점 스캔, 침투 시도 감지
```

* **주요 탐지 메커니즘**:
  * **위협 인텔리전스 피드**: AWS 자체 인텔리전스, CrowdStrike, Proofpoint 등 글로벌 악성 IP/도메인 DB 실시간 대조.
  * **행동 머신러닝**: 계정 및 IAM 사용자의 평소 행동 패턴(접속 위치, 호출 API, 활동 시간) 학습 후 이상 행위 탐지.
  * **서버리스 동작**: 에이전트 설치 없이 VPC Flow Logs, DNS Logs, CloudTrail Events를 백그라운드에서 직접 분석.

---

## 3. 두 서비스의 보안 영역 및 오탐/미탐 한계 비교

| 구분 | Amazon CloudWatch | AWS GuardDuty |
| :--- | :--- | :--- |
| **핵심 목적** | **인프라 가용성(SRE) 및 로그/메트릭 상태 모니터링** | **클라우드 계정 침해 및 사이버 위협 전용 탐지(SecOps)** |
| **탐지 기준** | 수치적 임계치, 에러율, 머신러닝 이상 탐지 밴드 | 글로벌 위협 인텔리전스, IAM/네트워크 악성 행위 시그니처 |
| **분석 대상** | ECS/RDS 메트릭, 앱 로그, API 호출량, 지연시간 | CloudTrail, VPC Flow Logs, DNS Logs, S3/RDS Data Events |
| **대응 영역** | 리소스 확장(Auto-Scaling), 장애 복구, 트래픽 제어 | 악성 IP 차단(WAF/SG), IAM 세션 무효화, 침해 인스턴스 격리 |

### ⚠️ 오탐(False Positive) 및 미탐(False Negative) 심층 분석

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. CloudWatch의 오탐 & 미탐 영역                                                        │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 🚨 오탐 (False Positive):                                                              │
│    • TVING 인기 신작/콘서트 티켓팅 오픈 시 정상 팬들의 대량 유입(Flash Crowd)으로 인한     │
│      CPU 95% 스파이크를 "DDoS 공격" 또는 "시스템 치명적 결함"으로 오판하여 불필요한 차단 유발.│
│                                                                                        │
│ ❌ 미탐 (False Negative):                                                              │
│    • 공격자가 정상적인 HTTP 문법과 분산 IP를 사용하여 CPU 30% 수준으로 천천히 DB 데이터를  │
│      인출(BOLA 공격)하거나, 유출된 IAM 키로 몰래 백업본을 복제하는 "저부하 은닉 공격" 감지 불가. │
└────────────────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 2. GuardDuty의 오탐 & 미탐 영역                                                         │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 🚨 오탐 (False Positive):                                                              │
│    • 운영팀이 새로운 리전에서 점검 작업을 하거나, 신규 CI/CD 배포 파이프라인에서 정상적인    │
│      API 대량 호출을 수행할 때 "비인가 API 호출(UnusualBehavior)"로 경보 발령 (Alert Fatigue). │
│                                                                                        │
│ ❌ 미탐 (False Negative):                                                              │
│    • "비즈니스 로직 공격(Business Logic Attack)": 쿼리 버그를 유발하는 고비용 검색 파라미터   │
│      반복 호출(Algorithmic DoS)이나, 애플리케이션의 N+1 쿼리 버그로 인한 DB 고갈은        │
│      네트워크/IAM 침해가 아니므로 GuardDuty는 아무런 경보도 발생시키지 않음.                 │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. TVING 플랫폼 시나리오별 적합 서비스 분석

OTT 스트리밍 서비스(TVING)의 실제 운영 환경에서 발생하는 **3대 대표 시나리오**별로 적합한 서비스를 매핑한 결과입니다:

```text
                                [TVING 플랫폼 실무 시나리오]
                                              │
         ┌────────────────────────────────────┼────────────────────────────────────┐
         │                                    │                                    │
         ▼                                    ▼                                    ▼
[시나리오 1: 신작 동시 공개]           [시나리오 2: RDS CPU 95%]            [시나리오 3: 지능형 다단계 침해]
(Flash Crowd 트래픽 폭증)             (3대 원인 가설 교차 검증)            (정찰 ➔ SSRF ➔ DB 유출)
         │                                    │                                    │
         ▼                                    ▼                                    ▼
【적합: CloudWatch + AIOps】          【적합: CloudWatch + AIOps】          【적합: GuardDuty + AIOps】
 • CPU/Mem/RPM 이상탐지 밴드           • Performance Insights Top SQL       • 비정상 PortProbe 감지
 • 정상 트래픽 오탐 정제               • 배포 이력 대조 (N+1 버그)          • SSRF 악성 IP 통신 탐지
 • ECS Fargate 즉시 스케일아웃        • Algorithmic DoS 파라미터 판정      • WAF IP 차단 및 태스크 격리
```

### 상세 시나리오별 적합성 분석

1. **시나리오 1: N개 신작 동시 공개 시 특정 콘텐츠 대량 트래픽 인입 (Flash Crowd)**
   * **최적 서비스**: **CloudWatch + AIOps**
   * **이유**: 실시간 분당 요청 수(RPM), ECS 컨테이너 CPU/Memory 사용률, ALB 지연시간 추적은 CloudWatch의 고유 영역입니다. AIOps가 결합되어 정상 유저의 트래픽 폭증을 DDoS로 오판하지 않고 **SRE 자율 스케일아웃(1대 ➔ 4대)**을 실행합니다.

2. **시나리오 2: RDS CPU 95% 발생 시 3대 원인 분류 (Algorithmic DoS vs 쿼리 버그 vs 인기작 유입)**
   * **최적 서비스**: **CloudWatch (Logs/Metrics/Performance Insights) + AIOps**
   * **이유**: GuardDuty는 DB 내부 쿼리 부하나 애플리케이션 배포 이슈를 인지하지 못합니다. CloudWatch의 DB 커넥션 수치, 쿼리 레이턴시, 앱 에러 로그를 AIOps LLM이 교차 분석하여 정확한 원인을 진단합니다.

3. **시나리오 3: 애플리케이션 경유 다단계 은닉 공격 및 인프라 침투**
   * **최적 서비스**: **GuardDuty + AIOps**
   * **이유**: 비표준 포트 정찰, 주거용 프록시 경유, SSRF를 통한 내부 메타데이터(IMDS) 탈취 등은 GuardDuty의 위협 인텔리전스만이 정확하게 포착할 수 있습니다. AIOps가 분산된 LOW~MEDIUM Finding을 킬체인으로 묶어 **SOAR 자율 격리**를 수행합니다.

---

## 5. CloudWatch + AIOps vs GuardDuty + AIOps 비교

두 서비스에 **Amazon Bedrock AIOps Engine**이 결합되었을 때의 기능 및 시너지 비교입니다.

| 비교 항목 | ⚡ CloudWatch + AIOps (SRE 지향) | 🛡️ GuardDuty + AIOps (SecOps 지향) |
| :--- | :--- | :--- |
| **주요 역할** | **가용성 보장 및 성능 병목/오탐 해소** | **지능형 침해사고 판정 및 자율 격리(SOAR)** |
| **AIOps의 역할** | • 트래픽 급증 시 정상 유저(Flash Crowd) 판정<br>• RDS CPU 95%의 근본 원인(Root Cause) 분류<br>• 에러 로그 맥락 분석 및 긴급 조치 가이드 제시 | • 하루 수백 건의 경보 중 노이즈/오탐 필터링<br>• 다단계 저위험 Finding 묶어 공격 킬체인 추론<br>• 침해 영향도 평가 및 공격자 의도 분석 |
| **입력 데이터** | CPU/Mem 이상탐지 밴드, RPM, 앱 에러 로그, Top SQL | GuardDuty Finding JSON, CloudTrail Event, VPC Flow |
| **자율 실행 액션** | • ECS Fargate Auto-Scaling (태스크 증설)<br>• WAF Rate-Limit 오차단 방지/해제<br>• Redis 캐시 TTL 연장 및 DB 풀 안정화 | • 공격자 IP WAF 영구 차단 (IPSet)<br>• 침해된 IAM Role / JWT 세션 즉시 취소<br>• 감염된 ECS 컨테이너 강제 격리 및 재생성 |
| **알림 출력** | ⚡ Slack SRE 성능 최적화 및 스케일아웃 리포트 | 🚨 Slack SecOps 보안 침해 및 SOAR 격리 리포트 |

---

## 6. 최종 결론: TVING 플랫폼을 위한 하이브리드 SecAIOps & SRE 융합 아키텍처

> **"CloudWatch와 GuardDuty는 양자택일의 관계가 아니며, 두 서비스를 상호 보완적으로 융합할 때 완벽한 AIOps 플랫폼이 완성됩니다."**

```text
                                  [통합 AIOps 하네스 엔진 (Amazon Bedrock)]
                                                     │
                     ┌───────────────────────────────┴───────────────────────────────┐
                     ▼                                                               ▼
        [CloudWatch Observability]                                       [GuardDuty Intelligence]
  • 인프라 메트릭 & 1분 주기 이상 탐지                                  • 계정/네트워크 위협 탐지 및 인텔리전스
  • 앱 로그 & Performance Insights 분석                                 • IMDSv2/SSRF 침해 및 악성 IP 식별
                     │                                                               │
                     ▼                                                               ▼
        【SRE AIOps (성능 & 가용성)】                                     【SOAR AIOps (보안 & 자율격리)】
  • 신작 공개 트래픽 폭증 ➔ 자율 스케일아웃                                • 킬체인 은닉 공격 ➔ WAF/세션 즉시 격리
  • DB 고갈 ➔ 3대 가설 교차검증 & 복구                                    • 유출된 토큰 무효화 & 포렌식 보고
```

1. **상시 인프라 가용성 및 성능 방어 (CloudWatch + AIOps)**:
   * TVING 서비스의 대규모 트래픽 인입, 신작 공개, DB 슬로우 쿼리 발생 시 **서비스 다운타임을 0으로 유지**하고 정상 고객의 이탈을 방지.
2. **지능형 침해사고 및 계정 방어 (GuardDuty + AIOps)**:
   * 은닉된 해킹 시도, 크리덴셜 탈취, 악성 IP 접속 시 **LLM이 공격 킬체인을 자율 판정하여 수 초 내에 자동 격리(SOAR)** 수행.
