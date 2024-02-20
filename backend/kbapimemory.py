import psycopg2
import os
from fastapi import FastAPI
from pydantic import BaseModel
import openai
from langchain import OpenAI
from langchain.text_splitter import CharacterTextSplitter

from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma

from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from fastapi_utils.tasks import repeat_every

app = FastAPI()

# PostgreSQL database configuration
#DATABASE_URL = "postgresql://kbuser:kbuser@localhost/kb"
DATABASE_URL = "postgresql://ciuvvsnkwriehf:ba88c568349bcb2ccd5580d798c2ef5637660f78cade9ad60b7fa14503eef7e7@ec2-54-156-233-91.compute-1.amazonaws.com:5432/d66n3arkk36m8k"
# Set up OpenAI API credentials
openai.api_key = "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"
os.environ["OPENAI_API_KEY"] = openai.api_key

#content, questions, context, answers, etc. are in strings

class ContentRequest(BaseModel):
    content: str


class AnswerRequest(BaseModel):
    question: str
    context:str


class AnswerResponse(BaseModel):
    answer: str

class Message(BaseModel):
    text: str

class URLRequest(BaseModel):
    extracted_text: str

@app.post("/add_content")
def add_content(request: ContentRequest):
    content = request.content #in the box
    topic = "debate"
    #if there is content in the box
    if content:
        save_content(topic, content)
        print("saved content")
        return {"message": "Content added successfully"}
    #if there is no content in the box
    return {"message": "No content provided"}

@app.post("/read_url")
def read_url(request: URLRequest):
    extracted_text = request.extracted
    topic = "debate"
    if extracted_text:
        save_url(topic, extracted_text)
        return{"message": "URL added successfully"}
    return{"message": "No content provided"}


@app.post("/get_answer", response_model=AnswerResponse)
def get_answer(request: AnswerRequest):
    try:
        # Your code here
        print("received_question"+request.question+"received_context" + request.context)
    except HTTPException as e:
        # Handle the validation error
        print("Validation error" + "detail" +str(e))
    question = request.question
    context = request.context
    print("chatting history....")
    chat_history = [(question, context)]
    #creating a chat history from the question and the context provided
    print(chat_history)
    topic = "debate"
    if question:
        qa = app.query_engine
        answer = qa({"question": question, "chat_history": chat_history})
        #saving the answers in chat_history
        print(answer)
        #answer = qa.run(question)
        if answer:
            return {"answer": answer['answer']}

        else:
            return {"answer": "No answer found"}
    return {"answer": "No question provided"}

@app.post("/debate")
def send_message(message: Message):
    context = message.text
    #using openAI integration to give a response
    text = {"role": "user", "content": context};

    #conversation is also an object
    conversation = [{"role": "system", "content": "DIRECTIVE_FOR_gpt-3.5-turbo"}]
    conversation.append(text)
    print(text)
    print(conversation)
    bot_response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=conversation)
    #use the bot response from the openAI model
    print("bot response")
    answer = bot_response.choices[0].message.content

    if answer:
        return answer

    return "No answer found"


def save_content(topic, content):
    #connect to the database
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    #saving content in a database using SQL
    cur.execute("INSERT INTO public.kb (topic, content) VALUES (%s,%s)", (topic,content,))
    conn.commit()
    cur.close()
    conn.close()

def save_url(topic, extracted_text):
    #connect to the database
    connect = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    #saving content in a database using SQL
    cur.execute("INSERT INTO public.kb (topic, content) VALUES (%s,%s)", (topic,extracted_text,))
    connect.commit()
    cursor.close()
    connect.close()

def retrieve_knowledge(topic):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT content FROM public.kb where topic='" + topic +"'")
    #get the knowledge from the rows
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
    #initializing a chain with no Memory object
    qa = ConversationalRetrievalChain.from_llm(llm,
                                         docsearch.as_retriever())
    return qa



@app.on_event("startup")
@repeat_every(seconds=300 * 1)  # 300 seconds
def initDataIndex():
    topic = "debate"
    total_content = ""
    knowledge=retrieve_knowledge(topic)
    for content in knowledge:
        total_content += f"\n- {content}"
    app.query_engine = get_engine_from_openai(total_content)




