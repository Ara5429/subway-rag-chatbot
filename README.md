subway-rag-chatbot

지하철 역 내부 정보(화장실·엘리베이터 등)는 RAG로,
역 주변 맛집/가게 같은 최신 정보는 네이버 공식 API(로컬·블로그) 로 가져와 한 번에 답하는 Streamlit 챗봇.

핵심 기능

RAG: Chroma + OpenAI 임베딩(text-embedding-3-large)

질의 증강(augmented query): 대화 맥락을 반영한 검색용 문장 생성
(역/출구 번호는 절대 생략·변경 금지)

네이버 로컬: 상호/주소/링크 후보 리스트

네이버 블로그: 최근 N일 후기 요약 + 역명 필터

스트리밍 응답: 문서+웹 컨텍스트를 합쳐 자연스럽게 답변

폴더 구조
subway-rag-chatbot/
├─ src/
│  ├─ rag.py               # Streamlit 앱 (UI/대화/스트리밍)
│  ├─ retriever.py         # 벡터스토어/체인/질의 증강 설정
│  └─ naver_search.py      # 네이버 로컬/블로그, 역·출구 파서
├─ data/
│  └─ subway_station_docs.pdf  # 내부 RAG 문서(예시)
├─ chroma_store/           # Chroma persist 디렉터리(미리 생성/인덱싱 필요)
├─ .env                    # API 키 (아래 예시)
└─ README.md

설치
pip install -U streamlit langchain langchain-openai langchain-core langchain-chroma python-dotenv requests

.env 예시
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret

실행
streamlit run src/rag.py

동작 요약

사용자 입력 → 질의 증강 aug_q 생성

aug_q(또는 prompt + aug_q)로 RAG에서 문서 검색

aug_q에서 역/출구 추출 → 네이버 로컬/블로그 검색

로컬/블로그 결과를 LangChain Document로 만들고 docs 앞쪽에 추가

document_chain.stream(...)으로 스트리밍 응답

구현 포인트

naver_search.parse_station_exit(text) → ("가락시장역","2") 등 추출

build_naver_places_context(station, exit_no, keyword) → 상호/주소/링크 텍스트화

build_naver_blog_context(aug_q, station=..., days=N) → 최근 N일 후기 요약(역명 필터)

QA 프롬프트:

고정정보는 PDF 우선

맛집 등 가변정보는 네이버 우선, 상호명+링크 상위 3개 필수

트러블슈팅

깃허브에 커밋이 안 보임 → git push -u origin main (처음 1회 업스트림)

build_naver_blog_context() unexpected 'station' → naver_search.py 최신 함수 사용

정규식 에러/다른 역 섞임 → parse_station_exit 최신본 사용 + 블로그 역 필터 활성화

invoke() 에러 → get_relevant_documents() 폴백
