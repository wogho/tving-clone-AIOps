# S3 장애 대응 매뉴얼

## S3 Object가 보이지 않는 경우

다음 항목을 확인한다.

1.올바른 Bucket을 조회하고 있는지 확인한다.
2.Object Prefix가 올바른지 확인한다.
3.IAM Role에 s3:ListBucket 권한이 있는지 확인한다.
4.Object 접근이 필요한 경우 s3:GetObject 권한이 있는지 확인한다.
5.Bucket Policy에서 접근을 차단하고 있지 않은지 확인한다.
6.다른 AWS 계정의 Bucket인지 확인한다.

## AccessDenied가 발생하는 경우

다음 항목을 확인한다.

-IAM Policy
-Bucket Policy
-Explicit Deny 존재 여부
-Object ARN 범위
-Bucket ARN 범위

## 운영 원칙

AI가 Object나 Bucket을 자동 삭제하지 않는다.

조회 및 분석만 수행하고,
삭제 작업은 운영자의 승인을 거쳐 수행한다.