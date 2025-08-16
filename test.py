from slack_sdk import WebClient
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()  # load .env file

slack_token = os.getenv("SLACK_BOT_TOKEN")
slack_client = WebClient(token=slack_token)





