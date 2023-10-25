import requests
import streamlit as st
import PyPDF2
from io import BytesIO
from streamlit_js_eval import streamlit_js_eval

# Backend service URL
BACKEND_URL = "https://debategptapi-4f87684ab8d9.herokuapp.com"
def is_pdf_file(file):
    return file.type == "application/pdf"

user_font = "Helvetica"
user_color = "black"
bot_font = "Helvetica"
bot_color = "green"
main_font = "Times"
main_color = "red"

def extract_pdf_text(file_content):
    pdf_reader = PyPDF2.PdfReader(file_content)
    text = ""

    for i in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[i]
        text += page.extract_text()

    return text
# Streamlit app
def main():
    title = "DebateGPT"
    st.markdown(f"<div style='font-size: 50px; font-family: {main_font}; color: {main_color};'>{title}</div>",
                unsafe_allow_html=True)
    page = st.sidebar.radio("Navigation", ["Debate", "Ask", "Contribute"])

    print("back end url is:" + BACKEND_URL)
    if page == "Contribute":
        contribute_page()
    elif page == "Ask":
        ask_page()
    elif page == "Debate":
        debate_page()


def contribute_page():
    st.header("If you have knowledge on debate strategy, tips, resolution ideas, tournament help, etc. share it here!")

    file = st.file_uploader("Upload a PDF file", type="pdf")
    if file is not None:
        if is_pdf_file(file):
            # Convert PDF to text using PyPDF2
            file_content = BytesIO(file.getvalue())
            content = extract_pdf_text(file_content)
            #content = read_pdf_file(file)
            content = st.text_area("Your knowledge",content)
        else:
            st.error("Invalid file format. Please upload a pdf file.")
    else:
        content = st.text_area("Enter your knowledge")

    if st.button("Submit"):
        if content:
            response = add_content(content)
            if response:
                st.success("Content added to the knowledge base")

            else:
                st.error("Failed to add content")
        else:
            st.warning("Please enter some content")

def debate_page():
    st.header("Debate with an AI partner!")
    #image_path = "wildcat.jpg"
    #custom_width = 100  # Specify the desired width in pixels
    #st.image(image_path, width=custom_width)

    class Message:
        def __init__(self, role, content):
            self.role = role
            self.content = content

    # initiate a "session"
    # maintains user-specific data across different interactions in a session
    # maintains conversation history
    # stores your information into a session
    # making empty lists of "messages" and "context" for the bot to refer back to
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.context = []

    if "user_input" not in st.session_state:
        st.session_state.user_input = ""

    user_input = st.text_area("Enter your input: ", value=st.session_state.user_input)



    if st.button("Debate with me") and user_input:
        # add the user's input to the lists of messages and context
        st.session_state.messages.append(Message("user", user_input))
        st.session_state.context.append(user_input)
        # add the context from previous input to this input
        context = " ".join(st.session_state.context)
        response = requests.post(BACKEND_URL + "/debate", json={"text": context})
        bot_response = response.json()
        print(bot_response)
        # add bot's response from previous input to this input
        st.session_state.messages.append(Message("bot", bot_response))
        st.session_state.context.append(bot_response)

    with st.expander("Debate History", expanded=True):
        for message in st.session_state.messages:
            if message.role == "user":
                # if you are the user, the content of your message is a text input
                your_response = "You: " + str(message.content)
                # print(your_response)
                st.markdown(f"<div style='font-family: {user_font}; color: {user_color};'>{your_response}</div>",
                            unsafe_allow_html=True)
            if message.role == "bot":
                # if you are the bot, the content of your message is a response
                bot = "Bot: " + str(message.content)
                # print(bot_response)
                st.markdown(f"<div style='font-family: {bot_font}; color: {bot_color};'>{bot}</div>",
                            unsafe_allow_html=True)
                # st.markdown(f"<span style='font-family: {bot_font}; color: {bot_color};'>{bot}</span>", unsafe_allow_html=True)

    if st.button("Reload page"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")




def ask_page():
    st.header("If you have questions about debate that you want answered, ask here!")
    question = st.text_input("Enter your question")

    if st.button("Get Answer"):
        if question:
            answer = get_answer(question)
            if answer:
                st.success(answer)
            else:
                st.error("Failed to get answer")
        else:
            st.warning("Please enter a question")


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

