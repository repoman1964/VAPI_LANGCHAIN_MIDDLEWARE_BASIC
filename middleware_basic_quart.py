from quart import Quart, request, Response, jsonify
from vapi import VapiPayload, VapiWebhookEnum
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
import json, requests
import asyncio

app = Quart(__name__)

# Load environment variables from .env
load_dotenv()

# ENDPOINTS

@app.route('/middleware', methods=['POST'])
async def middleware():
    try:
        req_body = await request.get_json()
        payload: VapiPayload = req_body['message']
        print(payload['type'])
        print(VapiWebhookEnum.ASSISTANT_REQUEST.value)
        
        if payload['type'] == VapiWebhookEnum.FUNCTION_CALL.value:
            response = await function_call_handler(payload)
            return jsonify(response), 200
        elif payload['type'] == VapiWebhookEnum.STATUS_UPDATE.value:
            response = await status_update_handler(payload)
            return jsonify(response), 200
        elif payload['type'] == VapiWebhookEnum.ASSISTANT_REQUEST.value:
            response = await assistant_request_handler(payload)
            return jsonify(response), 201
        elif payload['type'] == VapiWebhookEnum.END_OF_CALL_REPORT.value:
            await end_of_call_report_handler(payload)
            return jsonify({}), 200
        elif payload['type'] == VapiWebhookEnum.SPEECH_UPDATE.value:
            response = await speech_update_handler(payload)
            return jsonify(response), 200
        elif payload['type'] == VapiWebhookEnum.CONVERSATION_UPDATE.value:
            response = await conversation_update_handler(payload)
            return jsonify(response), 200
        elif payload['type'] == VapiWebhookEnum.TRANSCRIPT.value:
            response = await transcript_handler(payload)
            return jsonify(response), 200
        elif payload['type'] == VapiWebhookEnum.HANG.value:
            response = await hang_event_handler(payload)
            return jsonify(response), 200
        else:
            raise ValueError('Unhandled message type')
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# This is the server URL set in the assistant_config. Vapi sends to that endpoint + "/chat/completions"    
@app.route('/chat/completions', methods=['POST'])
async def chat_completions():    
    # Get the 'messages' array from the JSON object
    request_data = await request.get_json()
    messages = request_data.get("messages", [])

    # Find the most recent message where role is 'user'
    human_message_content = None
    for message in messages:
        if message.get("role") == "user":
            human_message_content = message.get("content")

    return Response(generate_response(human_message_content), content_type='text/event-stream')

# HANDLERS

async def generate_response(human_message_content):
    # Create a ChatOpenAI model with streaming enabled
    model = ChatOpenAI(
        model="gpt-4o",
        streaming=True,
        temperature=0.7
    )

    # Create a human message
    human_message = HumanMessage(content=human_message_content)

    # Stream the response
    async for chunk in model.astream([human_message]):
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

async def function_call_handler(payload):
    function_call = payload.get('functionCall')
    if not function_call:
        raise ValueError("Invalid Request.")
    name = function_call.get('name')
    parameters = function_call.get('parameters')
    return None

async def status_update_handler(payload):
    return None

async def end_of_call_report_handler(payload):
    return None

async def speech_update_handler(payload):
    return None

async def conversation_update_handler(payload):
    return None

async def transcript_handler(payload):
    return None

async def hang_event_handler(payload):
    return None 

async def assistant_request_handler(payload):
    if payload and 'call' in payload:
        assistant_config = {
            "name": "Andrew",
            "model": {
                "provider": "custom-llm",
                "model": "not specified",
                "url": "https://e844-24-96-15-35.ngrok-free.app/",
                "temperature": 0.7,
                "systemPrompt": "You're Andrew, an AI assistant who can help user with any questions they have."
            },
            "voice": {
                "provider": "azure",
                "voiceId": "andrew",
                "speed": 1
            },
            "firstMessage": "Hi, I'm Andrew. I'm on a Quart server now. How can I help you today?",
            "recordingEnabled": True
        }
        return {'assistant': assistant_config}
    raise ValueError('Invalid call details provided.')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)