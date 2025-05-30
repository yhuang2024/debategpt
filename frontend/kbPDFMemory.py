import requests
import streamlit as st
import PyPDF2
from io import BytesIO
from streamlit_js_eval import streamlit_js_eval
import json
from bs4 import BeautifulSoup
import re
from PyPDF2 import PdfWriter

BACKEND_URL = "http://localhost:8000"
def is_pdf_file(file):
    return file.type == "application/pdf"

user_font = "Helvetica"
user_color = "black"
bot_font = "Helvetica"
bot_color = "green"
main_font = "Times"
main_color = "red"
import socket

def get_user_ip():
    try:
        return requests.get('https://ipinfo.io').json()['ip']
    except Exception as e:
        return str(e)

def get_machine_name():
    try:
        machine_name = socket.gethostname()
        return machine_name
    except Exception as e:
        return str(e)

def extract_pdf_text(file_content):
    #read text from the pdf
    pdf_reader = PyPDF2.PdfReader(file_content)
    text = ""

#get text for each page read in the pdf
    for i in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[i]
        text += page.extract_text()
    return text

def extract_text_from_website(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    text = soup.get_text(separator=' ')
    text = "\n".join(line for line in text.splitlines() if line.strip())
    return text

def main():
    title = "DebateGPT"
    st.markdown(f"<div style='font-size: 50px; font-family: {main_font}; color: {main_color};'>{title}</div>",
                unsafe_allow_html=True)
    page = st.sidebar.radio("Navigation", ["Debate", "Ask", "Contribute"])
    if page == "Contribute":
        contribute_page()
    elif page == "Ask":
        ask_page()
    elif page == "Debate":
        debate_page()

def contribute_page():
    extracted_text=""
    file_content=""
    text_content=""
    st.header("If you have knowledge on debate strategy, tips, resolution ideas, tournament help, etc. share it here!")
    file = st.file_uploader("Upload a PDF file", type="pdf")
    url = st.text_input("Enter a website URL:")
    if st.button("Read website"):
        if url:
            #read the website from URL
            extracted_text = extract_text_from_website(url)
            st.success("Website read!")
            url_content = st.text_area("Your knowledge", extracted_text)
            st.session_state.url_content=extracted_text
            print("url_content")

        else:
            st.write("Please enter a URL.")

    elif extracted_text == "" and file is not None:
        if is_pdf_file(file):
            st.session_state.url_content=""
            file_content_bytes = BytesIO(file.getvalue())
            extract_file_content = extract_pdf_text(file_content_bytes)
            file_content = st.text_area("Your knowledge",extract_file_content)
        else:
            st.error("Invalid file format. Please upload a pdf file.")
    elif extracted_text == "" and file is None:
        #otherwise it'll be blank
        text_content = st.text_area("Enter your knowledge")

    if st.button("Submit knowledge"):
        print("extract text....")
        content=""
        #none means nothing, "" is empty
        #text has to be set as ""
        #none = no value, "" = no characters
        if file_content:
            print("pdf")
            content = file_content
        elif text_content != "":
            print("text")
            content = text_content
        elif "url_content" in st.session_state and (text_content == "" or file_content is None):
            #session state maintains user input
            print("url")
            url_content = st.session_state.url_content
            content = url_content
        #print out the final content based on three different inputs
        if content:
            print("content added")
            response = add_content(content)
            if response:
                st.success("Content added to the knowledge base")
            else:
                st.error("Failed to add content")
        else:
            st.warning("Please enter some content")




def debate_page():
    st.header("Debate with an AI partner!")
    class Message:
        def __init__(self, role, content):
            self.role = role
            self.content = content

    #initiate a "session"
    #maintains user-specific data across different interactions in a session
    #maintains conversation history
    #stores your information into a session
    #making empty lists of "messages" and "context" for the bot to refer back to
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.context = []

    if "user_input" not in st.session_state:
        st.session_state.user_input = ""

    user_input = st.text_area("Enter your input: ", value=st.session_state.user_input)

    if st.button("Debate with me") and user_input:
        #add the user's input to the lists of messages and context
        st.session_state.messages.append(Message("user", user_input))
        st.session_state.context.append(user_input)
        #add the context from previous input to this input
        context = " ".join(st.session_state.context)
        response = requests.post(BACKEND_URL + "/debate", json={"text": context})
        bot_response = response.json()
        #add bot's response from previous input to this input
        st.session_state.messages.append(Message("bot", bot_response))
        st.session_state.context.append(bot_response)

    with st.expander("Debate History", expanded=True):
        for message in st.session_state.messages:
            if message.role == "user":
                your_response = "You: " + str(message.content)
                st.markdown(f"<div style='font-family: {user_font}; color: {user_color};'>{your_response}</div>",
                            unsafe_allow_html=True)
            if message.role == "bot":
                bot = "Bot: " + str(message.content)
                st.markdown(f"<div style='font-family: {bot_font}; color: {bot_color};'>{bot}</div>",
                            unsafe_allow_html=True)

    if st.button("Reload page"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")

def ask_page():
    st.header("If you have questions about debate that you want answered, ask here!")
    class Message:
        def __init__(self, role, content):
            self.role = role
            self.content = content
            
    if "ask_messages" not in st.session_state:
        st.session_state.ask_messages = []
        st.session_state.ask_context = []

    if "ask_user_input" not in st.session_state:
        st.session_state.ask_user_input = ""

    ask_user_input = st.text_area("Enter your question: ", value=st.session_state.ask_user_input)

    if st.button("Ask Question") and ask_user_input:
        st.session_state.ask_messages.append(Message("user", ask_user_input))
        st.session_state.ask_context.append(ask_user_input)
        #add the context from previous input to this input
        context = " ".join(st.session_state.ask_context)
        data = {
        "question": ask_user_input,
        "context": context
        }
        json_data = json.dumps(data)
        response = requests.post(BACKEND_URL + "/get_answer", json=data)
        bot_response = response.json()['answer']
        #add bot's response from previous input to this input
        st.session_state.ask_messages.append(Message("bot", bot_response))
        st.session_state.ask_context.append(bot_response)

    with st.expander("Conversation History", expanded=True):
        for message in st.session_state.ask_messages:
            if message.role == "user":
                your_response = "You: " + str(message.content)
                st.markdown(f"<div style='font-family: {user_font}; color: {user_color};'>{your_response}</div>",
                            unsafe_allow_html=True)
            if message.role == "bot":
                bot = "Bot: " + str(message.content)
                st.markdown(f"<div style='font-family: {bot_font}; color: {bot_color};'>{bot}</div>",
                            unsafe_allow_html=True)

    if st.button("Reload page"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")

def add_content(content):
    url = f"{BACKEND_URL}/add_content"
    data = {"content": content}
    response = requests.post(url, json=data)
    return response.status_code == 200

def get_answer(question):
    url = f"{BACKEND_URL}/get_answer"
    data = {"question": question}
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json()["answer"]
    return None

if __name__ == "__main__":
    main()
