# 🚇 subway-rag-chatbot

지하철 **역 내부 정보**(화장실·엘리베이터·편의시설)는 **RAG**로,  
역 **주변 맛집/가게 같은 최신 정보**는 **네이버 공식 API(로컬·블로그)** 로 가져와 **한 번에 답하는** Streamlit 챗봇입니다.

---

## ✨ 핵심 기능
- **RAG**: Chroma + OpenAI 임베딩(`text-embedding-3-large`)
- **LLM**: OpenAI `gpt-4o` / `gpt-4o-mini`
- **질의 증강(augmented query)**: 대화 맥락을 반영한 검색용 문장 생성  
  *(역/출구 번호는 절대 생략·변경 금지 규칙 포함)*
- **네이버 로컬**: 상호/주소/링크 후보 리스트
- **네이버 블로그**: 최근 **N일** 후기 요약 + **역명 필터**
- **스트리밍 응답**: 문서 + 웹 컨텍스트를 합쳐 자연스럽게 답변

## 🧰 요구 사항
- Python 3.10+
- 패키지:
```bash
pip install -U streamlit langchain langchain-openai langchain-core langchain-chroma python-dotenv requests
