import os
import datetime
from slack_sdk import WebClient
from notion_client import Client as NotionClient
import gspread
from dotenv import load_dotenv
from slack_sdk.errors import SlackApiError
from oauth2client.service_account import ServiceAccountCredentials


# ===============================
# LOAD ENVIRONMENT VARIABLES
# ===============================
load_dotenv()

ASSIGN_TYPE = os.getenv("ASSIGN_TYPE", "incremental")   # "fixed" or "incremental"
FIXED_SIZE = int(os.getenv("FIXED_SIZE", 10))
BASE = int(os.getenv("BASE", 10))
INCREMENT = int(os.getenv("INCREMENT", 2))

SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
SHEET_ID = os.getenv("SHEET_ID")

TEAM = os.getenv("TEAM", "Aakash,Priya,Rohit,Meena").split(",")

# Init clients
slack_client = WebClient(token=SLACK_TOKEN)
notion = NotionClient(auth=NOTION_TOKEN)
gc = gspread.service_account(filename="credentials.json")
sheet = gc.open_by_key(SHEET_ID).sheet1


# ===============================
# Helper: check if within ±X minutes
# ===============================
def in_time_range(target_hour: int, target_minute: int, delta_minutes=30):
    now = datetime.datetime.now()
    target = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    diff = abs((now - target).total_seconds() / 60)  # in minutes
    return diff <= delta_minutes


# ===============================================================================
# MORNING FUNCTION
# ===============================================================================




load_dotenv()  # loads Slack token and channel from .env
SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN")
OUTREACH = os.getenv("OUTREACH")

# ---------------- GOOGLE SHEETS SETUP ----------------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gspread.authorize(creds)

sheet_main = client.open("MainDatabase").sheet1       # main DB
sheet_assign = client.open("Assignments")            # has multiple tables: E101, E102...

# ---------------- SLACK SETUP ----------------
client_slack = WebClient(token=SLACK_TOKEN)

# ---------------- MORNING TASK ----------------
def morning_task():
    # Step 1: Fetch counters from main sheet
    counters = sheet_main.get_all_values()[0:2]
    row_count = int(counters[0][4])  # 5th column, 1st row
    day_count = int(counters[1][4])  # 5th column, 2nd row

    # Step 2: Pull main DB data
    data = sheet_main.get_all_values()
    total_rows = len(data)

    # Step 3: Python indices (0-based)
    py_start_index = row_count
    py_end_index = min(row_count + 50, total_rows)
    new_rows = data[py_start_index:py_end_index]

    if not new_rows:
        print("No new rows to assign.")
        return

    # Step 4: Split into chunks → assign to E101, E102...
    tables = ["E101", "E102", "E103", "E104", "E105"]
    chunk_size = 2
    assigned = {}

    for i, table in enumerate(tables):
        ws = sheet_assign.worksheet(table)
        start = i * chunk_size
        end = start + chunk_size
        chunk = new_rows[start:end]

        if chunk:
            ws.clear()
            ws.insert_row([f"Assigned Data (Day {day_count})"], 1)
            ws.insert_rows(chunk, 2)
            assigned[table] = len(chunk)

    # Step 5: Mark cells green in main sheet (only actual assigned rows)
    total_assigned_rows = sum(assigned.values())
    if total_assigned_rows > 0:
        sheet_start_row = py_start_index + 1
        sheet_end_row = py_start_index + total_assigned_rows

        batch_format_requests = [{
            "repeatCell": {
                "range": {
                    "sheetId": sheet_main.id,
                    "startRowIndex": sheet_start_row - 1,
                    "endRowIndex": sheet_end_row,
                    "startColumnIndex": 0,
                    "endColumnIndex": 5
                },
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": {"red": 0.8, "green": 1, "blue": 0.8}
                    }
                },
                "fields": "userEnteredFormat.backgroundColor"
            }
        }]
        sheet_main.spreadsheet.batch_update({"requests": batch_format_requests})

    # Step 6: Update row_count and day_count in main sheet
    sheet_main.update(range_name="E1:E2", values=[[py_start_index + total_assigned_rows], [day_count + 1]])

    # Step 7: Slack message
    message = f"Good Morning Team, Your work has been assigned to you for  Day - {day_count}.\nYou can start Outreach from now. "
 

    try:
        client_slack.chat_postMessage(channel=OUTREACH, text=message)
    except SlackApiError as e:
        print(f"Slack error: {e.response['error']}")



# ====================================================================================
# EVENING FUNCTION
# =====================================================================================




def evening_task():
    outreach_channel = os.getenv("OUTREACH")  # load channel ID
    today = datetime.now().strftime("%d-%b")

    try:
        slack_client.chat_postMessage(
            channel=outreach_channel,
            text=f"<!channel>Good evening team! Please submit your report of *{today}*.\n\n"
                 f"before End Of The Day."
        )
        print("✅ Evening task complete (sent to OUTREACH channel).")
    except Exception as e:
        print(f"Slack API error: {e}")



# ===========================================================================================
# REMINDER FUNCTION
# ===========================================================================================


def reminder_task():
    for member in TEAM:
        # TODO: Query Notion DB to check if report submitted
        submitted = False
        if not submitted:
            slack_client.chat_postMessage(
                channel=f"@{member.lower()}",
                text=f"⏰ Reminder {member}: You haven’t submitted today’s report. Please do it now."
            )
    print("✅ Reminder task complete.")


# ===============================
# MAIN ROUTER
# ===============================
def main():
    day_count = (datetime.date.today() - datetime.date(2025, 8, 16)).days + 1  # Example start date

    if in_time_range(9, 0):
        morning_task(day_count)
    elif in_time_range(19, 0):
        evening_task()
    elif in_time_range(21, 0):
        reminder_task()
    else:
        print("⏳ Script ran, but no task matched.")

