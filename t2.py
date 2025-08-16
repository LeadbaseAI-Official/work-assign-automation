from slack_sdk import WebClient
from dotenv import load_dotenv
import os

load_dotenv()  # load .env file

slack_token = os.getenv("SLACK_BOT_TOKEN")
OUTREACH = os.getenv("OUTREACH")

client = WebClient(token=slack_token)
client.chat_postMessage(channel=OUTREACH, text="Hello World!")
