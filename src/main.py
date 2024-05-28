import uuid
import streamlit as st
import urllib.parse
import requests
import openai
import json
import mimetypes
import re
from src.engine import get_summary_prompt, format_conversation_history, get_completion_summary
import streamlit_analytics


from src.ui import layout 
from datetime import datetime

API_KEY = st.secrets.get("API_KEY")
openai.api_key = API_KEY

HANDOVER_CONFIDENCE_LIMIT = int(st.secrets.get("HANDOVER_CONFIDENCE_LIMIT") or 20)
HANDOVER_MESSAGES_LIMIT = int(st.secrets.get("HANDOVER_MESSAGES_LIMIT") or 2)
USER = 'USER'
AGENT = 'AGENT'

def reset_low_confidence_count():
    st.session_state.low_confidence_count = 0

def reset_context():
    st.session_state["context"] = []

def clear_chat():
    st.session_state["conversation_uuid"] = str(uuid.uuid4())
    st.session_state["generated"] = []
    st.session_state["past"] = []
    st.session_state["messages_ids"] = []
    reset_context()
    reset_low_confidence_count()

def get_query_params():
    query_params = st.experimental_get_query_params()
    project_name = query_params.get('project_name', [''])[0]
    language = query_params.get('language', [''])[0]
    return project_name, language


def redirect_to_claudia_url(project_name: str, language: str, company_name: str):
    st.session_state.company_name = company_name
    st.session_state.project_name = project_name
    st.session_state.language = language
    st.experimental_set_query_params(project_name=project_name, language=language, company_name=company_name)

def initialize_state():
    params = st.experimental_get_query_params()

    if "generated" not in st.session_state:
        clear_chat()

    if "uploaded_faq" not in st.session_state:
        st.session_state.uploaded_faq = None

    if "low_confidence_count" not in st.session_state:
        st.session_state.low_confidence_count = 0
    
    if "current_feedback_id" not in st.session_state:
        st.session_state.current_feedback_id = None

    if "company_name" not in st.session_state:
        st.session_state.company_name = params.get('company_name', [''])[0]

    if "language" not in st.session_state:
        st.session_state.language = params.get('language', ['English'])[0]
    
    if "voice_tone" not in st.session_state:
        st.session_state.voice_tone = 'Zerezes'

    if "project_name" not in st.session_state:
        st.session_state.project_name = params.get('project_name', [''])[0]


import mimetypes

def create_new_register_on_claudia(voiceTone, companyName, language, uploaded_file):
    url = 'http://claudia-api.us-east-1.prd.cloudhumans.io/api/ids/demo/doc'
    headers = {
        'accept': '*/*'
    }

    params = {
        'voiceTone': voiceTone,
        'companyName': companyName,
        'language': language,
    }

    mime_type = mimetypes.guess_type(uploaded_file.name)[0]

    files = {
        'file': (uploaded_file.name, uploaded_file.getvalue(), mime_type)
    }

    response = requests.post(url, headers=headers, params=params, files=files)

    if response.status_code == 200:
        print('Response OK')
        print(f'response.text {response.text}')
        # st.session_state.has_sent_claudia_attributes = True
        redirect_to_claudia_url(response.text, language, response.text.split('_')[0])
    else:
        print('POST request failed')
        print('Status Code:', response.status_code)
        print('Response:', response.text)

    return response


def handle_file_upload():
    st.session_state.uploaded_faq = st.session_state.uploaded_file


def format_messages(message: str, role: str) -> dict:
    current_datetime = datetime.now()
    new_formatted_datetime = current_datetime.strftime('%Y-%m-%dT%H:%M:%S')
    formatted_message = {
        'role': role,
        'content': message,
        'sendAt': new_formatted_datetime,
        'private': False
    }

    return formatted_message


# def format_claudia_input_from_conversation(messages: list, project_name: str) -> dict:
#     ticket_id = f'demo_{str(uuid.uuid4())}'
#
#     claudia_formatted_input = {
#         'cloudChatId': ticket_id,
#         'projectName': project_name,
#         'messages': messages
#     }
#
#     return claudia_formatted_input

def format_claudia_input_from_conversation(messages: list, project_name: str, ticket_id: str = None) -> dict:
    if ticket_id is None:
        ticket_id = f'demo_{str(uuid.uuid4())}'

    claudia_formatted_input = {
        'cloudChatId': ticket_id,
        'projectName': project_name,
        'messages': messages
    }

    return claudia_formatted_input





def call_claudia_message_api(query):
    st.session_state["context"].append(format_messages(query, USER))

    # URL for the API endpoint
    url = "http://claudia-api.us-east-1.prd.cloudhumans.io/api/test/conversation/v2"

    # Headers
    headers = {
        "Content-Type": "application/json"
    }
    json_data = json.dumps(format_claudia_input_from_conversation(st.session_state["context"], st.session_state["project_name"]))

    # Send the POST request
    response = requests.post(url, data=json_data, headers=headers)
    response_json = {}
    project_not_found_regex = False

    if response.status_code == 200:
        response_json = response.json()
        print(f'response json: {response.json()}')
    else:
        print('POST request failed')

        project_not_found_regex = r"Error while handling the message: java\.lang\.Error: Project '([^']+)' not found"
        response_json['project_not_found'] = re.match(project_not_found_regex, response.text)
        
        print('Status Code:', response.status_code)
        print('Response:', response.text)

    final_answer = response_json.get('final_answer', '')
    internal_note = response_json.get('internal_note', '')
    
    st.session_state["context"].append(format_messages(final_answer, AGENT))

    return (final_answer, internal_note, project_not_found_regex)


def handle_question(query):
    with st.spinner("Generating response to your query: `{}` ".format(query)):
        # TODO: Change below to call Claudia API
        text,internal_note ,project_not_found = call_claudia_message_api(query)

        is_handover =  internal_note != None

        result = {'is_handover': is_handover, 'text': text, 'summary_prompt': internal_note, 'project_not_found': project_not_found} 

        st.session_state.generated.append(result)
        st.session_state.past.append(query)

def run():
    with streamlit_analytics.track(save_to_json='analytics_15-08-2023.json', load_from_json='analytics_15-08-2023.json'):
        initialize_state()
        layout(
            company_name=st.session_state.get('company_name'),
            clear_chat=clear_chat,
            handle_file_upload=handle_file_upload,
            handle_question=handle_question,
            create_new_register_on_claudia=create_new_register_on_claudia,
        )