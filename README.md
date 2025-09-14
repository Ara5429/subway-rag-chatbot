🚇 subway-rag-chatbot

지하철 역 내부 정보는 RAG로, 역 주변 최신 정보는 네이버 공식 API로 — 둘을 합쳐 한 번에 답해주는 Streamlit 챗봇










화장실/엘리베이터/편의시설 같은 정적 정보는 PDF 기반 RAG,
맛집/가게 같은 동적 정보는 네이버(로컬·블로그) 공식 API로 보강합니다.

✨ 핵심 기능
범주	역할	주요 포인트
RAG	역 내부 고정 정보	Chroma + text-embedding-3-large
네이버 로컬	인근 상호/주소/링크	리뷰 많은 순, 역·출구 키워드 반영
네이버 블로그	최근 N일 후기 요약	역명 필터링 지원(다른 역 노이즈 제거)
질의 증강	aug_q 생성	대화 맥락 반영, 역/출구 불변 원칙
응답	스트리밍	문서+웹 컨텍스트 합성, 상호명+링크 우선
🧭 동작 흐름
flowchart LR
    U[User 입력] --> A[질의 증강 aug_q<br/> (역/출구 유지)]
    A --> R[RAG 검색 (Chroma)]
    A --> N1[네이버 로컬\n(장소 후보)]
    A --> N2[네이버 블로그\n(최근 N일 후기)]
    N1 --> C[컨텍스트 병합 (웹 앞쪽)]
    N2 --> C
    R --> C
    C --> L[LLM 응답 스트리밍]

🗂️ 폴더 구조
<details> <summary><b>열기/닫기</b></summary>
subway-rag-chatbot/
├─ src/
│  ├─ rag.py               # Streamlit 앱 (UI/대화/스트리밍)
│  ├─ retriever.py         # 벡터스토어/체인/질의 증강
│  └─ naver_search.py      # 네이버 로컬/블로그, 역·출구 파서
├─ data/
│  └─ subway_station_docs.pdf  # 내부 RAG 문서 (예시)
├─ chroma_store/           # Chroma persist 디렉터리 (미리 생성/인덱싱 필요)
├─ .env                    # API 키 (아래 예시)
└─ README.md

</details>
⚙️ 설치 & 실행
# 1) 의존성
pip install -U streamlit langchain langchain-openai langchain-core langchain-chroma python-dotenv requests

# 2) .env 작성 (레포 루트)
#   OPENAI_API_KEY, NAVER_CLIENT_ID, NAVER_CLIENT_SECRET
#   예시는 아래 참고

# 3) (처음 1회) PDF 임베딩 → Chroma 저장 (인덱싱 스크립트가 있다면 실행)
#   이미 chroma_store가 있다면 생략 가능

# 4) 실행
streamlit run src/rag.py


.env 예시

OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret

🧩 구현 메모 (중요 포인트만)

증강 질의 aug_q:
query_augmentation_chain으로 만든 검색용 문장.
프롬프트에 “원문에 나온 지명/역명/출구 번호는 절대 생략·변경 금지” 규칙을 넣음.

네이버 검색은 반드시 aug_q로:
parse_station_exit(aug_q) → (station, exit_no) 추출 →
build_naver_places_context(station, exit_no, keyword) / build_naver_blog_context(aug_q, station=...).

컨텍스트 순서:
docs = [네이버_로컬, 네이버_블로그] + RAG문서들 (웹을 앞쪽에 프리펜드)

응답 규칙(프롬프트):
고정정보는 PDF 우선, 맛집은 네이버 우선, 상호명+링크 상위 3개 필수.
