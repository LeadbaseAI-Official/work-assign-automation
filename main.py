import datetime
import time
from slack_sdk import WebClient
from notion_client import Client as NotionClient
import gspread

# ===============================
# CONFIG (edit these values)
# ===============================
ASSIGN_TYPE = "incremental"   # "fixed" or "incremental"
FIXED_SIZE = 10
BASE = 10
INCREMENT = 2

SLACK_TOKEN = "xoxb-..."         # Slack Bot Token
NOTION_TOKEN = "secret_..."      # Notion Integration Token
SHEET_ID = "..."                 # Google Sheet ID
TEAM = ["Aakash", "Priya", "Rohit", "Meena"]   # Outreach members

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


# ===============================
# MORNING FUNCTION
# ===============================
def morning_task(day_count: int):
    if ASSIGN_TYPE == "fixed":
        assign_size = FIXED_SIZE
    else:
        assign_size = BASE + (day_count - 1) * INCREMENT

    leads = sheet.get_all_records()
    start_idx = (day_count - 1) * assign_size * len(TEAM)
    assignments = {}

    for i, member in enumerate(TEAM):
        assigned = leads[start_idx + i*assign_size : start_idx + (i+1)*assign_size]
        assignments[member] = assigned

        # TODO: Push these leads to Notion DB for each member
        # notion.pages.create(...)

        # Mark rows as assigned (light gray background)
        for row in range(start_idx + i*assign_size + 2, start_idx + (i+1)*assign_size + 2):
            sheet.format(f"A{row}:Z{row}", {"backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}})

        # Notify member on Slack
        slack_client.chat_postMessage(
            channel=f"@{member.lower()}",
            text=f"👋 {member}, {assign_size} leads assigned to your Notion DB. Please start outreach."
        )

    print("✅ Morning task complete.")


# ===============================
# EVENING FUNCTION
# ===============================
def evening_task():
    for member in TEAM:
        slack_client.chat_postMessage(
            channel=f"@{member.lower()}",
            text=f"📝 Hi {member}, please submit your daily report in Notion."
        )
    print("✅ Evening task complete.")


# ===============================
# REMINDER FUNCTION
# ===============================
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


if __name__ == "__main__":
    main()
