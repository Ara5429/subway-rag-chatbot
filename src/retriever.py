# 임베딩 모델 선언하기
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(model="gpt-4o", api_key=openai_api_key)
embedding = OpenAIEmbeddings(model='text-embedding-3-large')

# 언어 모델 불러오기
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
# Load Chroma store
from langchain_chroma import Chroma
print("Loading existing Chroma store")
persist_directory = r'D:\workspace\RAG\chroma_store'

vectorstore = Chroma(
    persist_directory=persist_directory, 
    embedding_function=embedding
)

# Create retriever
retriever = vectorstore.as_retriever(k=3)

# Create document chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser # 문자열 출력 파서를 불러옵니다.

question_answering_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "역사 내부 고정정보(엘리베이터, 화장실)는 제공된 context의 PDF를 우선으로 답하라.\n"
            "맛집·가게 등 가변정보는 context 중 '네이버_로컬' 또는 '네이버_블로그' 섹션을 우선 사용해 "
            "상호명과 링크를 포함한 상위 3개를 추천하라. 거리·출구와의 관계를 간단히 덧붙여라.\n"
            "모호한 조언(예: 주변을 돌아보세요)은 금지. 반드시 구체 상호명과 링크를 제시하라.\n\n"
            "{context}",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

document_chain = create_stuff_documents_chain(llm, question_answering_prompt) | StrOutputParser()

# query augmentation chain
query_augmentation_prompt = ChatPromptTemplate.from_messages(
    [
        MessagesPlaceholder(variable_name="messages"), # 기존 대화 내용
        (
            "system",
            "기존의 대화 내용을 활용하여 사용자의 아래 질문의 의도를 파악하여 명료한 한 문장의 질문으로 변환하라. 대명사나 이, 저, 그와 같은 표현을 명확한 명사로 표현하라. 원문에 등장한 지명/역명/출구 번호는 절대 생략하거나 변경하지마라 :\n\n{query}",
        ),
    ]
)

query_augmentation_chain = query_augmentation_prompt | llm | StrOutputParser()