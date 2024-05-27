import html
import time
from PIL import Image
import streamlit as st
from streamlit_modal import Modal
import streamlit.components.v1 as component

from src.utils import is_debug

feedback_modal = Modal('Feedback', 'feedback')

def render_logo():
    logo = Image.open("./claudia_demos.png")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.empty()
    with col2:
        st.image(logo)
    with col3:
        st.empty()
    
def get_query_params():
    query_params = st.experimental_get_query_params()
    project_name = query_params.get('project_name', [''])[0]
    return project_name

def render_header(company_name):
    copy_url = f'https://use-claudia.streamlit.app?project_name={st.session_state.project_name}&language={st.session_state.language}&company_name={st.session_state.company_name}'

    render_logo()
    if get_query_params() != '':
        st.title(f"{company_name} - ClaudIA is online! 🤖")
        
        component.html("""
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Source+Sans+3&display=swap');

                .container {
                    background: #ffdaa9;
                    border-radius: 4px;
                    border: 1px solid #e1b273;
                    padding: 10px 15px;
                    font-family: 'Source Sans 3';
                    color: #333;
                }

                .content {
                    margin-bottom: 20px;
                }

                .button {
                    background: #2168a7;
                    color: #fff;
                    border: 1px solid #154a79;
                    border-radius: 4px;
                    padding: 5px 10px;
                    cursor: pointer;
                }

                .button:hover {
                    background: #1e5d95;
                }

                .button:active {
                    background: #195489;
                }
            </style>
        """ + f"""
            <div class="container"> 
                <div class="content">
                    <b>Hello there! 👋</b><br /><br />
                    This demo is all yours! Save this URL and send it to your friends and coworkers 🙂
                </div>

                <button onclick="var textarea = document.createElement('textarea'); textarea.value = '{copy_url}'; textarea.style.position = 'fixed'; document.body.appendChild(textarea); textarea.select(); document.execCommand('copy'); document.body.removeChild(textarea);" class="button">Copy this demo to clipboard 🔗</button>
            </div>
        """, height=150)

        st.markdown("""
            **📌 Keep in mind when engaging with ClaudIA:**
        """, unsafe_allow_html=True)        
        component.html("""
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Source+Sans+3&display=swap');
                
                .container {
                    font-family: 'Source Sans 3', sans-serif; 
                    color: rgb(49, 51, 63);
                }

                li {
                    margin-top: 5px;
                }

                a {
                    text-decoration: underline;
                    opacity: .9;
                    cursor: pointer;
                    color: inherit;
                }

                a:hover {
                    opacity: 1;
                }

                a:visited {
                    color: inherit
                }
            </style>
        """ + f"""
            <div class="container">
                <ul>
                    <li>Try typing “I want to talk to a human” after the conversation to see how ClaudIA would escalate internally 🔀</li>
                    <li>Whenever you feel like starting a new conversation, click on "clear conversation" on the bottom left</li>
                </ul>

                We're connected to over 20 helpdesks. Get in touch if you want to test it in your existing support setup: 
                <ul>
                    <li><b>Email:</b> <a href="mailto:bruno@cloudhumans.com">bruno@cloudhumans.com</a></li>
                    <li><b>Text / WhatsApp:</b> <a href="https://api.whatsapp.com/send?phone=3322486906" target="_blank">+1 (332) 248 6906</a></li>
                </ul>
            </div>
        """, height=240)
        st.divider()

def render_content(handle_question):
    if get_query_params() != '':
        with st.form("my_form", clear_on_submit=True):
            query = st.text_input(
                "**Start talking to ClaudIA!**",
                placeholder="For example: I need help!",
            )

            submitted = st.form_submit_button("Submit")

            if submitted:
                handle_question(query)

def set_feedback(id):
    st.session_state["current_feedback_id"] = id
    feedback_modal.open()

def render_conversation(clear_chat):
    if len(st.session_state.generated) > 0:
        with st.expander("Conversation", expanded=True):
            for i in range(len(st.session_state.generated) - 1, -1, -1):
                with st.container():
                    generated_content = st.session_state.generated[i]
                        
                    st.info(st.session_state.past[i], icon="🧐")
                    
                    response_text = html.escape(generated_content.get('text', '')).replace("$", r"\$")
                    if(generated_content['is_handover']):
                        response_note = html.escape(generated_content.get('summary_prompt', '')).replace("$", r"\$")

                    if generated_content['project_not_found']:
                        st.error("Your IDS has expired! Our demo link has a time limit of **3 days**. To generate a new demo environment, please click [here](https://www.cloudhumans.com/claudia-demo).", icon="⏳")
                    elif generated_content['is_handover']:
                        st.success(response_text, icon="🤖")
                        st.warning("*This represents a simulated private note, showcasing what your agents would receive when claudIA escalates an issue.*\n\n--------\n\n" + response_note, icon="⚠️")
                    else:
                        st.success(response_text, icon="🤖")
                    if i:
                        st.divider()

        st.button("Clear Conversation", on_click=clear_chat)


def render_upload(handle_file_upload):
    if get_query_params() == '':
        st.title("Upload your content in 2~3 minutes 🚀")
        st.markdown("""
            📎 Simply upload a *.PDF or *.DOCX file with your FAQ content and watch ClaudIA work her magic! 🧙🏽 Observe ClaudIA responding to your inquiries in the tone you've tailored!

            **Important notes:**
            - [The ideal format for the FAQ is Q&A, check out this example](https://docs.google.com/document/d/152TuYJJEGyi1ntp2CtgzPYpQ6alaPb-B62pVN0cqcm8/edit)
            - PDF generated from PowerPoint, Slides, Images or Printing are not recommended. ClaudIA doesn't like it 🤫
            - ClaudIA hasn't mastered reading images yet, but no worries if your PDF has some. It will process the text but not the images 😎
            - Since this is a demo, there's a limit of 20k characters for uploaded contents (Approximately 5-10 pages, depending on font size).
        """)
        st.file_uploader("**FAQ upload**", type=["pdf", "docx"], on_change=handle_file_upload, key="uploaded_file")

        
def render_register_informations(create_new_register_on_claudia):

    if get_query_params() == '':
        st.divider()
        with st.spinner("""
        Loading… ⏳\n\n
        Go get a coffee ☕️ while we are transforming your FAQ into an Improved Data Set (IDS) 🔄.\n\n
        We're more than a startup that connects to generative AI. ClaudIA's model is fueled by a comprehensive stack of technologies designed for real customer service challenges.
        """):
            with st.form("sidebar_form"):
                st.markdown("We want to make it extra customized for you, so write your company name, language and tone of voice.")
                name = st.text_input(
                    "**Company Name**",
                    placeholder="Ex.: Cloud Humans",
                    value=st.session_state.get("company_name", "")
                )

                language = st.selectbox(
                    label="**Language**",
                    options=('Portuguese', 'Spanish', 'English'),
                    index=['Portuguese', 'Spanish', 'English'].index(st.session_state.get("language", ""))
                )

                voice_tone = st.selectbox(
                    label="**Voice tone**",
                    options=(
                        'Cloud Humans Recommended', 'Professional', 'Empathetic', 'Conversational', 'Simple', 'Humorous', 'Academic', 'Creative', 'Friendly'
                    ),
                    index=['Zerezes', 'Professional', 'Empathetic', 'Conversational', 'Simple', 'Humorous', 'Academic', 'Creative', 'Friendly'].index(st.session_state.get("voice_tone", ""))
                )

                
                st.markdown("Ready to go! Click save now and generate your own ClaudIA to play with and share with your team")
                submitted = st.form_submit_button("Save")

                if submitted:
                    response = create_new_register_on_claudia(voice_tone,name.replace(' ', '_'), language,st.session_state.uploaded_faq)
                    if(response.status_code == 200):
                        time.sleep(2) # se tirar isso quebra
                        st.experimental_rerun()
                    elif(response.status_code == 400): 
                        st.markdown(f'**{response.text}**')
                    else:
                        st.markdown("**We're having some troubles processing your request. Please try again later.**")
                
        
def layout(
    company_name,
    handle_file_upload,
    clear_chat,
    handle_question,
    create_new_register_on_claudia
):
    st.set_page_config(page_title='ClaudIA', page_icon=Image.open("./favicon.ico"))
    render_header(company_name)
    render_upload(handle_file_upload)
    render_content(handle_question)
    render_conversation(clear_chat)
    render_register_informations(create_new_register_on_claudia)