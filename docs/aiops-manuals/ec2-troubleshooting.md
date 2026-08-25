# EC2 SSH 접속 장애 대응

다음 항목을 순서대로 확인한다.

1.EC2 Instance State가 running인지 확인
2.Instance Status Check가 ok인지 확인
3.System Status Check가 ok인지 확인
4.Public IP 또는 Elastic IP 존재 여부 확인
5.Public Subnet Route Table에 0.0.0.0/0 → Internet Gateway 경로 확인
6.Security Group에서 TCP 22 허용 여부 확인
7.Source IP가 현재 접속 위치의 공인 IP와 일치하는지 확인
8.Network ACL에서 SSH 관련 트래픽 허용 여부 확인
9.올바른 Private Key 사용 여부 확인
10.AMI에 맞는 사용자 이름 확인
    -Ubuntu: ubuntu
    -Amazon Linux: ec2-user

위 항목이 모두 정상이라면 추가로 확인한다.

-EC2 System Log
-SSH 서비스 상태
-OS 방화벽
-Session Manager 사용 가능 여부