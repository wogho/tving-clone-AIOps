# CloudWatch 로그 확인 매뉴얼

## 애플리케이션 오류 확인

다음 항목을 확인한다.

1.올바른 Log Group을 조회하고 있는지 확인한다.
2.Log Stream이 생성되어 있는지 확인한다.
3.최근 ERROR 로그가 존재하는지 확인한다.
4.HTTP 500 관련 로그가 있는지 확인한다.
5.Timeout 관련 로그가 있는지 확인한다.
6.애플리케이션 Exception 메시지를 확인한다.

## EC2 로그를 CloudWatch Logs로 전송하는 경우

다음 항목을 확인한다.

-CloudWatch Agent 설치 여부
-CloudWatch Agent 실행 상태
-Agent 설정 파일
-EC2 IAM Role
-logs:CreateLogStream 권한
-logs:PutLogEvents 권한

## 로그 분석 원칙

로그에 존재하지 않는 내용을 장애 원인으로 단정하지 않는다.

다음 정보를 Evidence로 사용한다.

-Timestamp
-Log Group
-Log Stream
-Error Message
-HTTP Status Code
-Exception