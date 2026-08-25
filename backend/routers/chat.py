"""
AI 챗봇 라우터 (스켈레톤) - TVING

[Day3 구현 가이드]
DB에서 콘텐츠 정보를 가져와 Bedrock FM에 전달하여 추천하는 방식입니다.
Knowledge Base 없이 DB 데이터를 직접 프롬프트 컨텍스트로 사용합니다.

사전 준비:
- AWS CLI 설정 (aws configure)
- Bedrock 모델 접근 권한 활성화
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas import ChatRequest, ChatResponse
from crud import get_all_contents_for_chat
from config import AWS_REGION, BEDROCK_MODEL_ID

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    AI 콘텐츠 추천 챗봇 (AWS Bedrock)

    사용 예시:
    - "요즘 인기 있는 드라마 추천해줘"
    - "범죄 스릴러 장르로 뭐 볼 게 있어?"
    - "주말에 볼 만한 예능 추천"
    """
    user_message = request.message
    
    # [Step 1] DB에서 콘텐츠 정보 가져오기
    contents = get_all_contents_for_chat(db)
    content_info = "\n".join([
        f"- {c.title} (카테고리: {c.category}, 장르: {c.genre}, 시즌: {c.total_seasons}, 에피소드: {c.total_episodes}편)"
        for c in contents
    ])

    # [Step 2] AWS Bedrock 연동
    import boto3
    import json

    client = boto3.client('bedrock-runtime', region_name=AWS_REGION)

    prompt = f"""당신은 TVING의 AI 콘텐츠 추천 전문가입니다.
아래 콘텐츠 목록을 참고하여 시청자의 취향에 맞는 콘텐츠를 친절하게 추천해주세요.
장르, 분위기, 카테고리를 고려하여 흥미롭게 추천합니다.

[보유 콘텐츠 목록]
{content_info}

[고객 질문]
{user_message}

친절하고 매력적인 톤으로 한국어로 답변해주세요."""

    try:
        response = client.converse(
            modelId=BEDROCK_MODEL_ID,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 600, "temperature": 0.7}
        )
        reply = response["output"]["message"]["content"][0]["text"]
        return ChatResponse(reply=reply)
    except Exception as e:
        # Fallback to invoke_model
        try:
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 600,
                "messages": [{"role": "user", "content": prompt}]
            })
            resp = client.invoke_model(
                modelId=BEDROCK_MODEL_ID,
                body=body,
                contentType="application/json"
            )
            result = json.loads(resp["body"].read())
            reply = result["content"][0]["text"]
            return ChatResponse(reply=reply)
        except Exception as err:
            return ChatResponse(
                reply=f"AI 추천을 생성하는 중 오류가 발생했습니다: {str(err)}"
            )
