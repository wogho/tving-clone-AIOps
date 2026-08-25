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
    초개인화 AI 콘텐츠 추천 챗봇 (AWS Bedrock RAG)

    특징:
    1. TVING 전체 콘텐츠 카탈로그 RAG 컨텍스트 구축
    2. 사용자 시청 이력(Watch History) 및 찜 목록(Wishlist) 기반 맞춤형 추천
    3. AWS Bedrock Claude 3 Haiku 모델을 통한 자연어 큐레이션 생성
    """
    user_message = request.message
    user_id = request.user_id
    
    # [Step 1] 전체 콘텐츠 카탈로그 로드 (RAG Knowledge Base)
    contents = get_all_contents_for_chat(db)
    catalogue_items = []
    for c in contents:
        synopsis_snippet = (c.synopsis[:120] + "...") if c.synopsis and len(c.synopsis) > 120 else (c.synopsis or "줄거리 정보 없음")
        catalogue_items.append(
            f"- [ID:{c.id}] {c.title} | 카테고리: {c.category} | 장르: {c.genre} | "
            f"시즌/에피소드: {c.total_seasons}시즌({c.total_episodes}화) | 줄거리: {synopsis_snippet}"
        )
    content_catalogue_text = "\n".join(catalogue_items)

    # [Step 2] 사용자 시청 이력 및 찜 목록 조회 (Personalization Context)
    is_personalized = False
    context_used = {}
    user_context_text = "비로그인 사용자 (일반 추천)"

    if user_id:
        from crud import get_watch_history, get_wishlist
        watch_histories = get_watch_history(db, user_id)
        wishlists = get_wishlist(db, user_id)
        
        history_titles = []
        for h in watch_histories[:5]:
            if h.content:
                history_titles.append(f"{h.content.title} ({h.content.genre}, {h.progress}% 시청)")
                
        wishlist_titles = []
        for w in wishlists[:5]:
            if w.content:
                wishlist_titles.append(f"{w.content.title} ({w.content.genre})")
                
        if history_titles or wishlist_titles:
            is_personalized = True
            context_used = {
                "watch_history": history_titles,
                "wishlist": wishlist_titles
            }
            user_context_text = f"""[사용자 맞춤 프로필]
• 최근 시청 이력: {', '.join(history_titles) if history_titles else '없음'}
• 찜한 콘텐츠 목록: {', '.join(wishlist_titles) if wishlist_titles else '없음'}"""

    # [Step 3] Bedrock RAG 프롬프트 구성
    import boto3
    import json

    client = boto3.client('bedrock-runtime', region_name=AWS_REGION)

    prompt = f"""당신은 국내 최고 OTT 서비스 TVING의 '초개인화 AI 콘텐츠 큐레이터'입니다.
제공된 [TVING 콘텐츠 라이브러리]와 [사용자 맞춤 프로필]을 면밀히 분석하여, 시청자의 취향에 딱 맞는 매력적인 콘텐츠를 추천해주세요.

{user_context_text}

[TVING 콘텐츠 라이브러리]
{content_catalogue_text}

[사용자 질문]
{user_message}

[답변 작성 가이드라인]
1. 사용자의 시청 이력과 찜 목록이 있다면, 해당 취향(장르, 분위기, 배우/스토리라인)을 언급하며 추천 이유를 명확하게 설명하세요.
2. TVING에 실제로 등록된 콘텐츠 중에서 가장 적합한 2~3편을 골라 작품명, 장르, 추천 포인트를 일목요연하게 안내하세요.
3. 시청자가 바로 보고 싶어지도록 친절하고 매력적인 OTT 큐레이터 톤으로 한국어로 작성하세요."""

    try:
        response = client.converse(
            modelId=BEDROCK_MODEL_ID,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 800, "temperature": 0.7}
        )
        reply = response["output"]["message"]["content"][0]["text"]
        return ChatResponse(
            reply=reply,
            personalized=is_personalized,
            context_used=context_used if is_personalized else None
        )
    except Exception as e:
        try:
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 800,
                "messages": [{"role": "user", "content": prompt}]
            })
            resp = client.invoke_model(
                modelId=BEDROCK_MODEL_ID,
                body=body,
                contentType="application/json"
            )
            result = json.loads(resp["body"].read())
            reply = result["content"][0]["text"]
            return ChatResponse(
                reply=reply,
                personalized=is_personalized,
                context_used=context_used if is_personalized else None
            )
        except Exception as err:
            return ChatResponse(
                reply=f"AI 추천을 생성하는 중 오류가 발생했습니다: {str(err)}",
                personalized=False
            )
