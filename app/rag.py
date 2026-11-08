import os, glob
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser

load_dotenv()
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA, INDEX = os.path.join(BASE, "data"), os.path.join(BASE, "index")
emb = OpenAIEmbeddings(model=os.getenv("EMBED_MODEL", "text-embedding-3-small"))

def load_index():
    if os.path.isdir(INDEX):  # 문서를 바꾸면 index/ 폴더를 삭제하면 재생성됨
        return FAISS.load_local(INDEX, emb, allow_dangerous_deserialization=True)
    pages = []
    for f in glob.glob(f"{DATA}/*"):
        if f.endswith(".pdf"): pages += PyPDFLoader(f).load()
        elif f.endswith((".md", ".txt")): pages += TextLoader(f, encoding="utf-8").load()
    docs = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100).split_documents(pages)
    db = FAISS.from_documents(docs, emb)
    db.save_local(INDEX)
    return db

retriever = load_index().as_retriever(search_kwargs={"k": 4})

SYSTEM = """너는 일본 여행 중인 한국인 초보자를 위한 일본어 회화 코치다.
사용자의 질문(한국어)을 여행 현장에서 일본인에게 그대로 말할 수 있는 자연스러운 정중체 일본어 한 문장으로 번역하고,
일본인이 대답할 법한 유형 5개와, 연관된 추천 문구 3~5개를 만든다.
[참고 문구]에 알맞은 표현이 있으면 우선 활용하고, 없으면 직접 만든다. 지명·역명은 질문 그대로 쓴다.
한글 발음은 일본어 초보가 소리 내어 읽을 수 있게 한글로 표기한다.
이전 대화 맥락이 있으면 반영한다. 반드시 아래 JSON만 출력한다.
{{"translation":{{"jp":"","reading":"히라가나","ko_pron":"한글발음"}},
"answers":[{{"jp":"","ko_pron":"","ko":""}}],
"suggestions":[{{"jp":"","ko_pron":"","ko":""}}]}}
answers는 정확히 5개, suggestions는 3~5개."""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM),
    MessagesPlaceholder("history"),
    ("user", "[참고 문구]\n{context}\n\n[질문]\n{question}"),
])
llm = ChatOpenAI(model=os.getenv("LLM_MODEL", "gpt-4o-mini")).bind(response_format={"type": "json_object"})
chain = prompt | llm | JsonOutputParser()

async def ask(question: str, history: list) -> dict:
    ctx = "\n".join(d.page_content for d in await retriever.ainvoke(question))
    return await chain.ainvoke({"question": question, "context": ctx, "history": history})
