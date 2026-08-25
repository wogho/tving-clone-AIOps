"""
AI 챗봇 라우터 (스켈레톤) - TVING

[Day3 구현 가이드]
DB에서 콘텐츠 정보를 가져와 Bedrock FM에 전달하여 추천하는 방식입니다.
Knowledge Base 없이 DB 데이터를 직접 프롬프트 컨텍스트로 사용합니다.

사전 준비:
- AWS CLI 설정 (aws configure)
- Bedrock 모델 접근 권한 활성화
"""
from typing import Optional
from fastapi import APIRouter, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from database import get_db
from schemas import ChatRequest, ChatResponse
from crud import get_all_contents_for_chat, get_watch_history, get_wishlist
from config import AWS_REGION, BEDROCK_MODEL_ID, JWT_SECRET, JWT_ALGORITHM

router = APIRouter()
optional_security = HTTPBearer(auto_error=False)


def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)) -> Optional[int]:
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return int(payload.get("sub"))
    except Exception:
        return None


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    auth_user_id: Optional[int] = Depends(get_optional_user)
):
    """
    초개인화 AI 콘텐츠 추천 챗봇 (AWS Bedrock RAG)
    """
    user_message = request.message
    user_id = request.user_id or auth_user_id
    
    # [Step 1] 전체 콘텐츠 카탈로그 로드 (RAG Knowledge Base)
    contents = get_all_contents_for_chat(db)
    catalogue_items = []
    content_map = {}
    for c in contents:
        content_map[c.title.strip()] = c
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
- 최근 시청 이력: {', '.join(history_titles) if history_titles else '없음'}
- 찜한 콘텐츠 목록: {', '.join(wishlist_titles) if wishlist_titles else '없음'}"""

    # [Step 3] Bedrock RAG 프롬프트 구성 (이모티콘 배제, 정갈하고 전문적인 톤)
    import boto3
    import json

    client = boto3.client('bedrock-runtime', region_name=AWS_REGION)

    prompt = f"""당신은 TVING의 전문 AI 콘텐츠 큐레이터입니다.
제공된 [TVING 콘텐츠 라이브러리]와 [사용자 맞춤 프로필]을 분석하여 시청자의 취향에 부합하는 최적의 콘텐츠를 추천해주세요.

{user_context_text}

[TVING 콘텐츠 라이브러리]
{content_catalogue_text}

[사용자 질문]
{user_message}

[작성 원칙]
1. 불필요한 이모티콘은 일절 사용하지 말고, 단정하고 신뢰감 있는 전문 큐레이터 어조(한국어)로 서술하세요.
2. 사용자의 시청 이력이 있는 경우, 해당 작품과의 연관성(장르, 스토리라인, 분위기)을 구체적으로 짚으며 추천 사유를 명시하세요.
3. TVING 라이브러리에 실제 존재하는 작품 중 가장 적절한 2~3편을 선정하여 각 작품의 제목, 장르, 추천 이유를 깔끔하게 제시하세요."""

    reply_text = ""
    try:
        response = client.converse(
            modelId=BEDROCK_MODEL_ID,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={"maxTokens": 800, "temperature": 0.7}
        )
        reply_text = response["output"]["message"]["content"][0]["text"]
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
            reply_text = result["content"][0]["text"]
        except Exception as err:
            reply_text = f"AI 추천 서비스를 불러오는 중 오류가 발생했습니다: {str(err)}"

    # [Step 4] 답변에서 언급된 추천 콘텐츠 썸네일/메타데이터 자동 매칭
    recommended_items = []
    for title, c in content_map.items():
        if title in reply_text:
            recommended_items.append({
                "id": c.id,
                "title": c.title,
                "category": c.category,
                "genre": c.genre,
                "thumbnail_url": c.thumbnail_url,
                "synopsis": c.synopsis
            })

    return ChatResponse(
        reply=reply_text,
        personalized=is_personalized,
        context_used=context_used if is_personalized else None,
        recommended_items=recommended_items
    )
