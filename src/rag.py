from langchain.docstore.document import Document
from naver_search import parse_station_exit # ← 새로 추가# ← 새로 추가
from naver_search import build_naver_blog_context # ← 새로 추가
from naver_search import build_naver_places_context # ← 새로 추가
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
import retriever as retriever


# 모델 초기화
llm = ChatOpenAI(model="gpt-4o-mini",temperature=0)

# 사용자의 메시지 처리하기 위한 함수
def get_ai_response(messages, docs):
    response = retriever.document_chain.stream({
        "messages": messages,
        "context": docs
    })
    for chunk in response:
        yield chunk

# Streamlit 앱
st.title("💬 지하철에 대한 모든것")
# 네이버 옵션
use_naver = st.sidebar.checkbox("네이버 블로그 검색 사용", value=True)
naver_days = st.sidebar.slider("블로그 최신성(일)", min_value=7, max_value=60, step=7, value=30)


# 스트림릿 session_state에 메시지 저장
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        SystemMessage("너는 지하철 사용자, 유독 시각장애인한테 도움을 주는 지하철 전문 위치 전문가야. "),  
        AIMessage("안녕하세요! 지하철에 대해 무엇이든 물어보세요. 저는 지하철 위치 전문가입니다. 😊"),
    ]

# 스트림릿 화면에 메시지 출력
for msg in st.session_state.messages:
    if msg.content:
        if isinstance(msg, SystemMessage):
            st.chat_message("system").write(msg.content)
        elif isinstance(msg, AIMessage):
            st.chat_message("assistant").write(msg.content)
        elif isinstance(msg, HumanMessage):
            st.chat_message("user").write(msg.content)

# 사용자 입력 처리
if prompt := st.chat_input():
    st.chat_message("user").write(prompt) # 사용자 메시지 출력
    st.session_state.messages.append(HumanMessage(prompt)) # 사용자 메시지 저장
    # 1. 질의 증강
    augmented_query = retriever.query_augmentation_chain.invoke({
        "messages": st.session_state["messages"],
        "query": prompt,
    })
    # 문자열 정규화 
    try:
        aug_q = augmented_query.strip()
    except Exception:
        if isinstance(augmented_query, dict):
            aug_q = augmented_query.get("query") or ""
        else:
            aug_q = str(augmented_query or "")
    query_for_retrieval = (f"{prompt}\n{aug_q}").strip()
    print("augmented_query(type):", type(augmented_query).__name__)
    print("query_for_retrieval:", query_for_retrieval)
    
    # 관련 문서 검색
    print("관련 문서 검색")
    try:
        docs = retriever.retriever.invoke(query_for_retrieval)
    except AttributeError:
        docs = retriever.retriever.get_relevant_documents(query_for_retrieval)
    
    #네이버 블로그 검색 추가
    if use_naver:
        try:
            # ⚠️ aug_q에서 역/출구 우선 파싱 (없으면 prompt로 보조)
            station, exit_no = parse_station_exit(aug_q)
            if not station:
                station, exit_no = parse_station_exit(prompt)

        # 카테고리 추정도 aug_q 기준
            keyword = "햄버거" if any(k in aug_q for k in ["햄버거", "버거"]) else "맛집"

        # 네이버 로컬(장소) → 출구/역 키워드가 반영된 aug_q 기반
            local_ctx = build_naver_places_context(station, exit_no, keyword=keyword, top_k=5)

        # 네이버 블로그 → aug_q 자체로 검색 + 역명 포함 필터
            blog_ctx  = build_naver_blog_context(aug_q, station=station, days=naver_days, max_items=6)

            local_doc = Document(page_content=local_ctx, metadata={"source": "네이버_로컬"})
            blog_doc  = Document(page_content=blog_ctx,  metadata={"source": "네이버_블로그"})

        # 웹 컨텍스트를 앞에 둬서 모델이 우선 보게 함
            docs = [local_doc, blog_doc] + list(docs)
        except Exception as e:
            st.warning(f"네이버 검색 오류: {e}")
            
    # RAG 문서 미리보기
    for doc in docs:
        print('---------------')
        print(doc)   
        with st.expander(f"**문서:** {doc.metadata.get('source', '알 수 없음')}"):
            # 파일명과 페이지 정보 표시
            st.write(f"**page:**{doc.metadata.get('page', '')}")
            st.write(doc.page_content)
    print("===============")

    with st.spinner(f"AI가 답변을 준비 중입니다... '{augmented_query}'"):
        try:
            response = get_ai_response(st.session_state["messages"], docs)
            result = st.chat_message("assistant").write_stream(response)
        except Exception:
            # 폴백: docs를 문자열로 병합해 동기 호출
            ctx = "\n\n".join([d.page_content for d in docs])
            result = retriever.document_chain.invoke({"messages": st.session_state["messages"], "context": ctx})
            st.chat_message("assistant").write(result)
    st.session_state["messages"].append(AIMessage(result)) # AI 메시지 저장 
    