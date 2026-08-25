"""
TVING AI 콘텐츠 추천 챗봇 - Streamlit UI (초개인화 RAG 버전)
접속: http://localhost:8501
"""
import streamlit as st
import requests
import os

st.set_page_config(page_title="TVING AI 큐레이터", page_icon="📺", layout="centered")

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.title("📺 TVING AI 초개인화 큐레이터")
st.markdown("시청자의 **시청 이력, 찜 목록, 취향**을 Bedrock RAG로 분석하여 딱 맞는 맞춤형 콘텐츠를 추천합니다.")
st.divider()

# 사이드바 - 사용자 프로필 시뮬레이션
with st.sidebar:
    st.header("👤 사용자 프로필 선택")
    user_option = st.selectbox(
        "시청 이력 연동 모드:",
        [
            "일반 사용자 (비로그인)",
            "User 1 (스릴러/드라마 애청자 - 시그널, 비밀의 숲)",
            "User 2 (예능/로맨스 애청자 - 환승연애, 지구오락실)",
            "User 3 (신규 회원 - 찜 목록만 존재)"
        ],
        index=1
    )
    
    user_id_map = {
        "일반 사용자 (비로그인)": None,
        "User 1 (스릴러/드라마 애청자 - 시그널, 비밀의 숲)": 1,
        "User 2 (예능/로맨스 애청자 - 환승연애, 지구오락실)": 2,
        "User 3 (신규 회원 - 찜 목록만 존재)": 3
    }
    selected_user_id = user_id_map[user_option]
    
    if selected_user_id:
        st.success(f"✅ User ID `{selected_user_id}` 시청 데이터 RAG 연동 활성화")
    else:
        st.info("ℹ️ 전체 카탈로그 기반 일반 추천 모드")
        
    st.divider()
    st.header("💡 추천 질문 예시")
    st.markdown("""
    - *"내가 지금까지 본 작품들이랑 비슷한 거 추천해줘"*
    - *"주말에 정주행하기 좋은 긴장감 넘치는 스릴러"*
    - *"가볍게 밥 먹으면서 볼 만한 힐링 예능"*
    """)
    st.divider()
    if st.button("🗑️ 대화 초기화"):
        st.session_state.messages = [
            {"role": "assistant", "content": "안녕하세요! TVING AI 초개인화 큐레이터입니다. 📺\n\n회원님의 취향과 시청 이력을 분석하여 딱 맞는 작품을 추천해 드립니다. 어떤 콘텐츠를 찾으시나요?"}
        ]
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요! TVING AI 초개인화 큐레이터입니다. 📺\n\n회원님의 취향과 시청 이력을 분석하여 딱 맞는 작품을 추천해 드립니다. 어떤 콘텐츠를 찾으시나요?"}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("보고 싶은 콘텐츠나 취향을 자유롭게 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("TVING 라이브러리 및 시청 이력 RAG 분석 중..."):
            try:
                payload = {
                    "message": prompt,
                    "user_id": selected_user_id
                }
                response = requests.post(
                    f"{BACKEND_URL}/api/chat",
                    json=payload,
                    timeout=30
                )
                if response.status_code == 200:
                    data = response.json()
                    reply = data["reply"]
                    if data.get("personalized") and data.get("context_used"):
                        ctx = data["context_used"]
                        st.caption(f"✨ *시청 이력 RAG 반영됨:* {', '.join(ctx.get('watch_history', []))}")
                else:
                    reply = f"서버 오류: {response.status_code}"
            except requests.exceptions.ConnectionError:
                reply = "백엔드 서버에 연결할 수 없습니다. 백엔드가 실행 중인지 확인해주세요."
            except Exception as e:
                reply = f"오류 발생: {str(e)}"
        st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
