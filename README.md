subway-rag-chatbot

지하철 역 내부 정보(화장실·엘리베이터·편의시설)는 RAG로,
역 근처 맛집/가게 등 최신 정보는 네이버(로컬·블로그) 공식 API로 가져와 하나의 답변으로 합쳐주는 Streamlit 챗봇입니다.

⚙️ RAG: Chroma 벡터스토어 + LangChain, subway_station_docs.pdf 등 내부 문서 기반

🧠 LLM: OpenAI gpt-4o / gpt-4o-mini (빠른 응답용)

🧩 질의 증강(augmented query): 대화 맥락을 반영해 검색용 문장으로 정제

🌐 네이버 검색(공식 API):

로컬(장소): 상호명·주소·링크 후보 리스트

블로그: 최근 N일 후기로 보강, 역명 필터 지원

🧵 스트리밍 응답: 문서+웹 결과를 합쳐 자연스럽게 답변


폴더 구조 
subway-rag-chatbot/
├─ src/
│  ├─ rag.py               # Streamlit 앱 (UI/대화/스트리밍)
│  ├─ retriever.py         # 벡터스토어/체인/질의 증강 설정
│  └─ naver_search.py      # 네이버 로컬/블로그, 역·출구 파서
├─ data/
│  └─ subway_station_docs.pdf  # 내부 RAG 문서 (예시)
├─ chroma_store/           # Chroma persist 디렉터리 (미리 생성/인덱스 필요)
├─ .env                    # API 키들 (아래 참고)
└─ README.md

요구사항

Python 3.10+

패키지

pip install -U streamlit langchain langchain-openai langchain-core langchain-chroma \
              python-dotenv requests


환경변수: .env

OPENAI_API_KEY=sk-xxxx
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret
