# 장애 대응 절차

## 1단계 - 상태 확인

-EC2 Instance State 확인
-EC2 Status Check 확인
-S3 Bucket/Object 조회 확인
-CloudWatch 최근 ERROR 로그 확인

## 2단계 - Evidence 수집

-EC2 상태 정보
-S3 Object 목록
-CloudWatch ERROR 로그
-오류 발생 시각

## 3단계 - 원인 분석

관측된 사실과 추정을 구분한다.

Evidence가 없는 내용을 장애 원인으로 단정하지 않는다.

## 4단계 - 조치 제안

AI는 조치를 추천할 수 있지만 다음 작업을 자동 수행하지 않는다.

-EC2 Instance 종료
-EC2 Instance 삭제
-S3 Object 삭제
-S3 Bucket 삭제
-IAM Policy 변경
-Security Group 변경