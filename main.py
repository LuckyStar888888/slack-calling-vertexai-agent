# Standard library imports
import os
import json
import asyncio
import logging
from dotenv import load_dotenv
from datetime import datetime
from flask import Flask, request, make_response

# Third-party imports slack
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier

#Google Cloud imports
from google.cloud import secretmanager

# Vertex AI imports
import vertexai
from google.adk.sessions import VertexAiSessionService
from vertexai import agent_engines


logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Helper to access Google Secret Manager
PROJECT_ID = os.environ.get("PROJECT_ID")

def get_secret_json(secret_id, version_id="latest"):
    """
    Access a secret version from Google Secret Manager.

    Returns:
        str: The secret value as a string.
    """
    
    project_id = PROJECT_ID

    client = secretmanager.SecretManagerServiceClient()

    # Construct the resource name of the secret version
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

    # Access the secret version
    response = client.access_secret_version(request={"name": name})

    # Return the payload as string
    secret_value = response.payload.data.decode("UTF-8")
    return json.loads(secret_value)

# Retrieve secrets from Secret Manager
secret_id = os.environ.get("SECRET_ID")
secrets = get_secret_json(secret_id)

SLACK_BOT_TOKEN = secrets["SLACK_BOT_TOKEN"]
SLACK_SIGNING_SECRET = secrets["SLACK_SIGNING_SECRET"]
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")

RESOURCE_ID = secrets["VERTEX_RESOURCE_ID"]

# GCP variables
LOCATION = "us-central1"
BUCKET = "gs://YOUR BUCKET NAME"


# Validation
if not all([SLACK_BOT_TOKEN, SLACK_APP_TOKEN, PROJECT_ID, LOCATION, BUCKET, RESOURCE_ID]):
    raise EnvironmentError("Missing one or more required environment variables.")

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=BUCKET)
session_service = VertexAiSessionService(PROJECT_ID, LOCATION)

# Initialize Slack client and signature verifier
slack_client = WebClient(token=SLACK_BOT_TOKEN)
signature_verifier = SignatureVerifier(SLACK_SIGNING_SECRET)

# Get bot user ID
BOT_USER_ID = slack_client.auth_test()["user_id"]

# Track greeted users in memory (per process)
greeted_users = set()

# Flask app
flask_app = Flask(__name__)

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    # Slack retry protection
    if request.headers.get("X-Slack-Retry-Num") is not None:
        return make_response("", 200)

    if not signature_verifier.is_valid_request(request.get_data(), request.headers):
        return make_response("Invalid request signature", 403)

    payload = request.get_json()
    if "type" in payload:
        if payload["type"] == "url_verification":
            return make_response(payload["challenge"], 200, {"content_type": "text/plain"})

        if payload["type"] == "event_callback":
            event = payload["event"]
            if event.get("type") == "message" and "subtype" not in event:
                user_id = event["user"]
                # Ignore messages from the bot itself
                if user_id == BOT_USER_ID:
                    return make_response("", 200)
                channel_id = event["channel"]
                user_input = event.get("text", "")

                asyncio.run(handle_message(channel_id, user_id, user_input))
            return make_response("", 200)

    return make_response("No action taken", 200)

async def handle_message(channel_id, user_id, user_input):
    # Greet the user if this is their first message in this session
    if user_id not in greeted_users:
        today = datetime.now().strftime('%A, %B %d, %Y')
        slack_client.chat_postMessage(
            channel=channel_id,
            text=f"Hi, <@{user_id}>, I am Data-Scientist. Nice to see you! Today is {today}. "
        )
        greeted_users.add(user_id)

    # Immediately notify the user that the bot is working on the request
    slack_client.chat_postMessage(
        channel=channel_id,
        text=f"Thanks for your request, I am working on it which will take sometime. Appreciate for your patient."
    )
    # Optional: Wait to simulate a more natural delay
    await asyncio.sleep(2)

    session = await session_service.create_session(app_name=RESOURCE_ID, user_id=user_id)
    agent = agent_engines.get(RESOURCE_ID)

    response_text = ""
    try:
        logging.info(f"User input: {user_input}")
        for event in agent.stream_query(user_id=user_id, session_id=session.id, message=user_input):
            logging.info(f"Vertex event: {event}")
            content = event.get("content", {})
            for part in content.get("parts", []):
                response_text += part.get("text", "")
    except Exception as e:
        logging.error(f"Error during Vertex AI stream_query: {e}")

    await session_service.delete_session(app_name=RESOURCE_ID, user_id=user_id, session_id=session.id)
    slack_client.chat_postMessage(channel=channel_id, text=f"<@{user_id}> {response_text or 'I couldn’t generate a response.'}")

# Only for local debug.
#!!!!!!! lease comment out before you deploy it to Google Cloud Run
if __name__ == "__main__":
    flask_app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))