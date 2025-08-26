# AI-Powered Data Analysis APP for Slack Chatbot Calling Google VertexAI Agent

A sophisticated Slack chatbot APP that leverages Google Cloud Vertex AI to provide intelligent data analysis capabilities. The bot acts as a data scientist assistant, helping users with data analysis, insights, and CSV generation from the data warehouse in Google Bihquery through natural language requests.

## Features

- **AI-Powered Data Analysis**: Uses Google Cloud Vertex AI for intelligent data analysis and insights
- **Natural Language Processing**: Understands and responds to data analysis requests in plain English
- **CSV Generation**: Provides data in CSV format for easy analysis and export
- **Session Management**: Maintains user sessions for continuous analysis workflows
- **Date Information**: Built-in date/time assistance
- **Google Cloud Integration**: Uses Secret Manager for secure credential management
- **Slack Integration**: Seamless integration with Slack workspaces

## Architecture

- **Backend**: Flask web server with Gunicorn
- **AI Services**: Google Cloud Vertex AI for data analysis
- **Cloud Services**: Google Cloud Secret Manager for secure credential storage
- **Deployment**: Google Cloud Run with Docker containerization

## Local Testing Instructions

### 1. Prerequisites

- Python 3.12+
- Google Cloud Platform account with Vertex AI enabled
- Slack workspace with app permissions
- Google Cloud CLI (gcloud) installed and configured

### 2. Install Dependencies

(1) Create a virtue environment (Sugguest to use MiniConda)

```bash
conda create --name slack_chatbot python=3.12 -y
conda init
conda activate slack_chatbot
```
(2) Install python libraries
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in your project root with the following variables:

```bash
# Google Cloud Configuration
PROJECT_ID=your-gcp-project-id
SECRET_ID=your-secret-manager-secret-id
SLACK_APP_TOKEN=xapp-your-slack-app-token

# GCP Variables
LOCATION=us-central1
BUCKET=gs://your-staging-bucket
```

### 4. Google Cloud Secret Manager Setup

Create a secret in Google Cloud Secret Manager with the following JSON structure:

```json
{
  "SLACK_BOT_TOKEN": "xoxb-your-slack-bot-token",
  "SLACK_SIGNING_SECRET": "your-slack-signing-secret",
  "VERTEX_RESOURCE_ID": "your-vertex-ai-resource-id"
}
```

**To create the secret via gcloud CLI:**
```bash
# Create the secret
gcloud secrets create your-secret-name --replication-policy="automatic"

# Add the secret version
echo '{"SLACK_BOT_TOKEN":"xoxb-your-token","SLACK_SIGNING_SECRET":"your-secret","VERTEX_RESOURCE_ID":"your-resource"}' | gcloud secrets versions add your-secret-name --data-file=-

# Grant access to your service account
gcloud secrets add-iam-policy-binding your-secret-name --member="serviceAccount:your-service-account@your-project.iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
```

### 5. Slack App Configuration

Configure your Slack app [OAuth & Permissions] with these permissions:
- `chat:write`
- `channels:history`
- `app_mentions:read`
- `im:history`, `im:read`, `im:write`
- `groups:history`
- `mpim:history`

### 6. Test Locally

**(1) Run the Flask application locally:**
```bash
python main.py
```

The app will start on `http://localhost:8080` (or the PORT specified in your environment).

**(2) To get a public URL http using ngrock:**

You can download ngrok from the web [ngrok](https://dashboard.ngrok.com/) to create a public URL:

```bash
# Use Windows Powershell
# Install ngrok
npm install -g ngrok

# Create public tunnel to your local Flask app
ngrok http 8080
```

Then you can get a public tunnel http like: `https://your-ngrok-url.ngrok.io` 

Set the Salck APP [Event Subscription]/Request URL  to: `https://your-ngrok-url.ngrok.io/slack/events`
Configure your Slack app [Event Subscriptions/Subscribe to bot events] with these permissions:
- `app_mentions:read`
- `channels:history`
- `im:history`, `im:read`, `im:write`
- `groups:history`
- `mpim:history`

Click Save button.

Then Go back to Install APP/Reinstall

**(3) Go to your Slack Channel APP**

You can start to test to ask questions from the APP.

**Test the Slack endpoint:**
```bash
curl -X POST http://localhost:8080/slack/events \
  -H "Content-Type: application/json" \
  -d '{"type":"url_verification","challenge":"test_challenge"}'
```

**Verify Slack signature validation:**
The app validates Slack request signatures. For testing, you may need to temporarily disable this or use proper Slack test events.

### 7. Local Development Tips

- **Debug Mode**: The app runs in debug mode locally (`debug=True`)
- **Port Configuration**: Default port is 8080, configurable via `PORT` environment variable
- **Hot Reload**: Flask debug mode enables automatic reloading on code changes
- **Logging**: Set `logging.basicConfig(level=logging.DEBUG)` for verbose output

## Google Cloud Run Deployment

### 1. Prepare for Deployment

**Update main.py for production:**
Comment out or remove the local development section:
```python
# Comment out this section before deploying to Google Cloud Run
# if __name__ == "__main__":
#     flask_app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
```

### 2. Configure Service Account

**Create a service account with necessary permissions:**
```bash
# Create service account
gcloud iam service-accounts create slack-bot-sa \
  --display-name="Slack Bot Service Account"

# Grant necessary roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:slack-bot-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:slack-bot-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# Use the service account for Cloud Run
gcloud run services update slack-bot \
  --service-account=slack-bot-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com \
  --region=us-central1
```

### 3. Build and Deploy

**Enable required APIs:**
```bash
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

**Build and deploy to Cloud Run:**
```bash
# Build the container
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/slack-bot

# Deploy to Cloud Run
gcloud run deploy slack-bot \
  --image gcr.io/YOUR_PROJECT_ID/slack-bot \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="PROJECT_ID=YOUR_PROJECT_ID,SECRET_ID=YOUR_SECRET_ID,LOCATION=us-central1,BUCKET=gs://YOUR_BUCKET" \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --concurrency 80
```

### 4. Update Slack Configuration

After deployment, update your Slack app's Event Subscription URL to:
```
https://slack-bot-xxxxx-uc.a.run.app/slack/events
```

### 5. Monitor and Debug

**View logs:**
```bash
gcloud logs tail --service=slack-bot --region=us-central1
```

**Check service status:**
```bash
gcloud run services describe slack-bot --region=us-central1
```

**Test the deployed endpoint:**
```bash
curl -X POST https://slack-bot-xxxxx-uc.a.run.app/slack/events \
  -H "Content-Type: application/json" \
  -d '{"type":"url_verification","challenge":"test_challenge"}'
```

## Usage Guide

### Basic Interaction

1. **Greeting**: The bot automatically greets new users and introduces its capabilities
2. **Date Requests**: Ask for current date or yesterday's date
3. **Data Analysis**: Request data analysis in natural language, and the bot will provide insights and CSV format data

### Data Analysis Requests

#### Example Requests based on your data warehouse
- `"Analyze sales data for Q1 2024"`
- `"Show me customer demographics"`
- `"Generate a report on revenue trends"`
- `"What are the key insights from our marketing data?"`
- `"Create a summary of quarterly performance"`

#### Response Format
The bot will:
1. Acknowledge your request
2. Process it through Vertex AI
3. Provide analysis results in text format
4. Generate CSV data when applicable

### Workflow
1. **Request Analysis** → Bot acknowledges and starts processing
2. **Processing** → Vertex AI analyzes the request
3. **Response** → Bot provides insights and data
4. **Session Management** → Bot maintains context for follow-up questions

## Example Conversations

**User**: "Show me sales data for Q1 2024"
**Bot**: "Thanks for your request, I am working on it which will take sometime. Appreciate for your patient."
[After processing] "Here's the analysis of Q1 2024 sales data: [detailed analysis]"

**User**: "What are the key trends?"
**Bot**: "Based on the data, the key trends are: [trend analysis]"

## Technical Details

### Dependencies

- **Web Framework**: Flask with Gunicorn
- **AI Services**: vertexai, google-cloud-secret-manager
- **Slack Integration**: slack-sdk
- **Async Support**: asyncio
- **Google Cloud**: google-cloud-aiplatform, google-adk

### Key Features

- **Session Management**: Tracks user sessions for continuous analysis
- **Error Handling**: Comprehensive error handling with fallback responses
- **Vertex AI Integration**: Leverages Google's advanced AI for data analysis
- **Slack Event Processing**: Handles Slack events with proper signature validation

### Security

- Uses Google Cloud Secret Manager for credential management
- Validates Slack request signatures
- Implements retry protection for Slack events
- Secure session management with Vertex AI

## Troubleshooting

### Common Issues

1. **Data Analysis Errors**: Verify Vertex AI resource configuration
2. **Slack Integration Issues**: Ensure proper app permissions and event subscription
3. **Secret Manager Errors**: Verify PROJECT_ID and SECRET_ID configuration
4. **Cloud Run Deployment Issues**: Check service account permissions and environment variables

### Debug Mode

**Local Development:**
```python
logging.basicConfig(level=logging.DEBUG)
```

**Cloud Run:**
```bash
gcloud run services update slack-bot \
  --set-env-vars="LOG_LEVEL=DEBUG" \
  --region=us-central1
```

### Common Deployment Issues

1. **Permission Denied**: Ensure service account has proper IAM roles
2. **Secret Access Failed**: Verify secret ID and service account permissions
3. **Vertex AI Initialization Failed**: Check project ID and location configuration
4. **Slack Signature Validation Failed**: Ensure proper signing secret configuration

## Deployment Checklist

### Before Deployment
- [ ] Comment out local development code in main.py
- [ ] Create Dockerfile
- [ ] Set up Google Cloud project and APIs
- [ ] Configure Secret Manager with all required secrets
- [ ] Create service account with proper permissions
- [ ] Update Slack app configuration

### After Deployment
- [ ] Verify Cloud Run service is running
- [ ] Test Slack endpoint with proper signature
- [ ] Monitor logs for any errors
- [ ] Update Slack Event Subscription URL
- [ ] Test bot functionality in Slack

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly (locally and on Cloud Run)
5. Submit a pull request

## License

This project is licensed under the MIT License. 