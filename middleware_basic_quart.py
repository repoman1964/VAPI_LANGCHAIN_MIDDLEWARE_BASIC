from quart import Quart, request, Response, jsonify
from vapi import VapiPayload, VapiWebhookEnum
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
import json, requests

app = Quart(__name__)

middleware_bp = Blueprint('middleware_api', __name__)

# Load environment variables from .env
load_dotenv()

# ENDPOINTS

@middleware_bp.route('/middleware', methods=['POST'])
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
    
# this is the server url set in the assistant_config. vapi sends to that endpoint + "/chat/completions"    
@middleware_bp.route('/chat/completions', methods=['POST'])
async def chat_completions():    

    # Get the 'messages' array from the JSON object
    req_json = await request.get_json()
    messages = req_json.get("messages", [])

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
          

async def function_call_handler(payload):
    """
    Handle Business logic here.
    """
    function_call = payload.get('functionCall')

    if not function_call:
        raise ValueError("Invalid Request.")

    name = function_call.get('name')
    parameters = function_call.get('parameters')
  
    return None

async def status_update_handler(payload):
    """
    Handle Business logic here.
    """
    return None

async def end_of_call_report_handler(payload):
    """
    Handle Business logic here.
    """
    return None

async def speech_update_handler(payload):
    """
    Handle Business logic here.
    """
    return None

async def conversation_update_handler(payload):
    """
    Handle Business logic here.
    """
    return None

async def transcript_handler(payload):
    """
    Handle Business logic here.
    """
    return None

async def hang_event_handler(payload):
    """
    Handle Business logic here.
    """
    return None 

async def assistant_request_handler(payload):
    """
    Handle Business logic here.
    """

    if payload and 'call' in payload:
        assistant_config = {
            "name": "Andrew",
            "model": {
                "provider": "custom-llm",
                "model": "not specified",
                "url": "https://4072-24-96-15-35.ngrok-free.app/",
                "temperature": 0.7,
                "systemPrompt": "You're Andrew, an AI assistant who can help user with any questions they have."
            },
            "voice": {
                "provider": "azure",
                "voiceId": "andrew",
                "speed": 1
            },
            "firstMessage": "Hi, I'm Andrew. I'm on quart now. How do I look?",
            "recordingEnabled": True
        }
        return {'assistant': assistant_config}

    raise ValueError('Invalid call details provided.')


app.register_blueprint(middleware_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
