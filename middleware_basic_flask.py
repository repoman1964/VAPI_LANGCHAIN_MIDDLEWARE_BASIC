from flask import Flask, request, Response, jsonify
from vapi import VapiPayload, VapiWebhookEnum
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
import json, requests

app = Flask(__name__)

# Load environment variables from .env
load_dotenv()

# ENDPOINTS

@app.route('/middleware', methods=['POST'])
def middleware():
    try:
        req_body = request.get_json()
        payload: VapiPayload = req_body['message']
        print(payload['type'])
        print(VapiWebhookEnum.ASSISTANT_REQUEST.value)
        
        if payload['type'] == VapiWebhookEnum.FUNCTION_CALL.value:
            response = function_call_handler(payload)
            return jsonify(response), 200
        elif payload['type'] == VapiWebhookEnum.STATUS_UPDATE.value:
            response = status_update_handler(payload)
            return jsonify(response), 200
        elif payload['type'] == VapiWebhookEnum.ASSISTANT_REQUEST.value:
            response = assistant_request_handler(payload)
            return jsonify(response), 201
        elif payload['type'] == VapiWebhookEnum.END_OF_CALL_REPORT.value:
            end_of_call_report_handler(payload)
            return jsonify({}), 200
        elif payload['type'] == VapiWebhookEnum.SPEECH_UPDATE.value:
            response = speech_update_handler(payload)
            return jsonify(response), 200
        elif payload['type'] == VapiWebhookEnum.CONVERSATION_UPDATE.value:
            response = conversation_update_handler(payload)
            return jsonify(response), 200
        elif payload['type'] == VapiWebhookEnum.TRANSCRIPT.value:
            response = transcript_handler(payload)
            return jsonify(response), 200
        elif payload['type'] == VapiWebhookEnum.HANG.value:
            response = hang_event_handler(payload)
            return jsonify(response), 200
        else:
            raise ValueError('Unhandled message type')
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# This is the server URL set in the assistant_config. Vapi sends to that endpoint + "/chat/completions"    
@app.route('/chat/completions', methods=['POST'])
def chat_completions():    
    # Get the 'messages' array from the JSON object
    messages = request.json.get("messages", [])

    # Find the most recent message where role is 'user'
    human_message_content = None
    for message in messages:
        if message.get("role") == "user":
            human_message_content = message.get("content")

    return Response(generate_response(human_message_content), content_type='text/event-stream')

# HANDLERS

def generate_response(human_message_content):
    # Create a ChatOpenAI model with streaming enabled
    model = ChatOpenAI(
        model="gpt-4o",
        streaming=True,
        temperature=0.7
    )

    # Create a human message
    human_message = HumanMessage(content=human_message_content)

    # Stream the response
    for chunk in model.stream([human_message]):
        if chunk.content:
            json_data = json.dumps({
                'choices': [
                    {
                        'delta': {
                            'content': chunk.content + ' ',
                            'role': 'assistant'
                        }
                    }
                ]
            })
            yield f"data: {json_data}\n\n"
    yield "data: [DONE]\n\n"

  
def function_call_handler(payload):
    function_call = payload.get('functionCall')
    if not function_call:
        raise ValueError("Invalid Request.")
    name = function_call.get('name')
    parameters = function_call.get('parameters')
    return None

def status_update_handler(payload):
    return None

def end_of_call_report_handler(payload):
    return None

def speech_update_handler(payload):
    return None

def conversation_update_handler(payload):
    return None

def transcript_handler(payload):
    return None

def hang_event_handler(payload):
    return None 

def assistant_request_handler(payload):
    if payload and 'call' in payload:
        assistant_config = {
            "name": "Andrew",
            "model": {
                "provider": "custom-llm",
                "model": "not specified",
                "url": "https://b878-24-96-15-35.ngrok-free.app/",
                "temperature": 0.7,
                "systemPrompt": "You're Andrew, an AI assistant who can help user with any questions they have."
            },
            "voice": {
                "provider": "azure",
                "voiceId": "andrew",
                "speed": 1
            },
            "firstMessage": "Hi, I'm Andrew, your personal AI assistant.",
            "recordingEnabled": True
        }
        return {'assistant': assistant_config}
    raise ValueError('Invalid call details provided.')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
