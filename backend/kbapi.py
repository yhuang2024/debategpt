import psycopg2
import os
from fastapi import FastAPI
from pydantic import BaseModel
import openai
from langchain import OpenAI
from langchain.text_splitter import CharacterTextSplitter

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma

from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from fastapi_utils.tasks import repeat_every

app = FastAPI()

# PostgreSQL database configuration
#DATABASE_URL = "postgresql://kbuser:kbuser@localhost/kb"
DATABASE_URL = "postgresql://ciuvvsnkwriehf:ba88c568349bcb2ccd5580d798c2ef5637660f78cade9ad60b7fa14503eef7e7@ec2-54-156-233-91.compute-1.amazonaws.com:5432/d66n3arkk36m8k"
# Set up OpenAI API credentials
openai.api_key = ""
os.environ["OPENAI_API_KEY"] = openai.api_key

class ContentRequest(BaseModel):
    content: str


class AnswerRequest(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    answer: str

class Message(BaseModel):
    text: str


@app.post("/add_content")
def add_content(request: ContentRequest):
    content = request.content
    topic = "debate"
    if content:
        save_content(topic, content)
        return {"message": "Content added successfully"}
    return {"message": "No content provided"}


@app.post("/get_answer", response_model=AnswerResponse)
async def get_answer(request: AnswerRequest):
    question = request.question
    topic = "debate"
    if question:
        qa = app.query_engine
        answer = qa.run(question)
        if answer:
            return {"answer": answer}

        else:
            return {"answer": "No answer found"}
    return {"answer": "No question provided"}

@app.post("/debate")
def send_message(message: Message):
    context = message.text
    #using openAI integraton to give a response
    text = {"role": "user", "content": context};

    #conversation is also an object
    conversation = [{"role": "system", "content": "DIRECTIVE_FOR_gpt-3.5-turbo"}]
    conversation.append(text)
    print(text)
    print(conversation)
    bot_response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=conversation)
    print("bot response")
    answer = bot_response.choices[0].message.content

    if answer:
        return answer

    return "No answer found"


def save_content(topic, content):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("INSERT INTO public.kb (topic, content) VALUES (%s,%s)", (topic,content,))
    conn.commit()
    cur.close()
    conn.close()


def retrieve_knowledge(topic):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT content FROM public.kb where topic='" + topic +"'")
    rows = cur.fetchall()
    knowledge = [row[0] for row in rows]
    cur.close()
    conn.close()
    return knowledge

def get_engine_from_openai(text):
    text_splitter = CharacterTextSplitter("\n",
        chunk_size=250,
        chunk_overlap=0
    )
    docs = text_splitter.create_documents([text])
    print(docs)
    print(len(docs))
    embeddings = OpenAIEmbeddings(openai_api_key=os.environ['OPENAI_API_KEY'])

    docsearch = Chroma.from_documents(docs, embeddings)
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
    #qa = VectorDBQA.from_chain_type(llm=llm, chain_type="stuff", vectorstore=docsearch)
    qa = RetrievalQA.from_chain_type(llm=llm,
                                     chain_type="stuff",
                                     retriever=docsearch.as_retriever())
    return qa



@app.on_event("startup")
@repeat_every(seconds=300 * 1)  # 300 seconds
def initDataIndex():
    topic = "debate"
    total_content = ""
    knowledge = retrieve_knowledge(topic)
    for content in knowledge:
        total_content += f"\n- {content}"
    app.query_engine =get_engine_from_openai(total_content)




