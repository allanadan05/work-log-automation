import requests
import pandas as pd
from datetime import datetime, timedelta
from colorama import Fore, Style
import logging
import os
from tabulate import tabulate
from dotenv import load_dotenv

load_dotenv()  # Loads variables from .env into environment


def extract_description(desc):
    """Extract plain text from Atlassian Document Format."""
    if not desc or not isinstance(desc, dict):
        return ""
    result = []
    def walk(node):
        if isinstance(node, dict):
            if node.get("type") == "text":
                result.append(node.get("text", ""))
            elif node.get("type") in ("paragraph", "listItem"):
                for c in node.get("content", []):
                    walk(c)
                result.append("\n")
            elif node.get("type") in ("orderedList", "bulletList"):
                for c in node.get("content", []):
                    walk(c)
            elif node.get("type") == "mediaSingle":
                pass
            else:
                for c in node.get("content", []):
                    walk(c)
        elif isinstance(node, list):
            for item in node:
                walk(item)
    walk(desc)
    return "".join(result).strip()

# --- Logging Setup ---
log_time = datetime.now().strftime("%Y-%m")
log_filename = f"./logs/jira_ticket_log_{log_time}.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# --- Config ---
JIRA_URL = os.getenv("JIRA_URL")
JIRA_USER = os.getenv("JIRA_USER")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
EXCEL_PATH = os.getenv("EXCEL_PATH")
SHEET_NAME = "JIRA Tickets"

# --- User Options ---
print(f"{Fore.GREEN}Select JIRA Ticket Scope:{Style.RESET_ALL}")
print("1. All JIRA Tickets")
print("2. Assigned To Me (Unresolved)")
print("3. Assigned To Me (Resolved and Unresolved)")
print("4. Watching (Tickets I Watch)")
print("5. Was Assigned To Me")

scope_choice = input("Enter option (1-5): ").strip()

scope_map = {
    "1": "",  # All
    "2": "assignee=currentUser() AND resolution=Unresolved",
    "3": "assignee=currentUser()",
    "4": "watcher = currentUser()",
    "5": "assignee WAS currentUser() AND assignee != currentUser()"
}
if scope_choice not in scope_map:
    print(f"{Fore.RED}Invalid choice. Defaulting to 'Assigned to Me'.{Style.RESET_ALL}")
    scope_choice = "2"

# --- Date Filter Options ---
print(f"{Fore.GREEN}\nSelect Date Filter:{Style.RESET_ALL}")
print("a. All")
print("b. Today")
print("c. This Week")
print("d. This Month")

date_choice = input("Enter option (a-d): ").strip().lower()

if date_choice not in ("a", "b", "c", "d"):
    print(f"{Fore.RED}Invalid choice. Defaulting to 'All'.{Style.RESET_ALL}")
    date_choice = "a"

now = datetime.now()
date_jql = ""
if date_choice == "a":
    date_jql = ""
elif date_choice == "b":
    today = now.strftime("%Y-%m-%d")
    date_jql = f'AND updated >= "{today}"'
elif date_choice == "c":
    start_of_week = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%d")
    date_jql = f'AND updated >= "{start_of_week}"'
elif date_choice == "d":
    first_day = now.replace(day=1).strftime("%Y-%m-%d")
    date_jql = f'AND updated >= "{first_day}"'
else:
    date_jql = ""

base_jql = scope_map[scope_choice]
if base_jql and date_jql:
    JIRA_JQL = f"{base_jql} {date_jql} ORDER BY updated DESC"
elif base_jql:
    JIRA_JQL = f"{base_jql} ORDER BY updated DESC"
else:
    JIRA_JQL = f"ORDER BY updated DESC"
print(f"{Fore.YELLOW}\nJQL: {JIRA_JQL}{Style.RESET_ALL}")

# --- Fetch JIRA Issues with Pagination and Error Handling ---
headers = {"Accept": "application/json"}
auth = (JIRA_USER, JIRA_API_TOKEN)
max_results = 100
start_at = 0
issues = []

try:
    while True:
        params = {
            "jql": JIRA_JQL,
            "maxResults": max_results,
            "startAt": start_at
        }
        try:
            response = requests.get(f"{JIRA_URL}/rest/api/3/search", headers=headers, params=params, auth=auth, timeout=30)
            response.raise_for_status()
            data = response.json()
            issues.extend(data.get("issues", []))
            logging.info(f"Fetched {len(data.get('issues', []))} issues (startAt={start_at})")
            if start_at + max_results >= data.get("total", 0):
                break
            start_at += max_results
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching JIRA issues: {e}")
            print(f"{Fore.RED}Error fetching JIRA issues: {e}{Style.RESET_ALL}")
            break
except Exception as e:
    logging.error(f"Unexpected error during JIRA fetch: {e}")
    print(f"{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}")

# --- Flatten Data ---
flat_data = []
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
for issue in issues:
    fields = issue["fields"]
    parent = fields.get("parent", {})
    project = fields.get("project", {})
    desc = extract_description(fields.get("description"))
    flat_data.append({
        "Status": fields.get("status", {}).get("name"),
        "Priority": fields.get("priority", {}).get("name"),
        "Key": issue["key"],
        "Parent Key": parent.get("key"),
        "Parent Summary": parent.get("fields", {}).get("summary"),
        "Project": project.get("name"),
        "Summary": fields.get("summary"),
        "Description": desc,
        "Assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else "Unassigned",
        "Created": fields.get("created"),
        "Updated": fields.get("updated"),
        "Due Date": fields.get("duedate"),
        "Logged At": timestamp
    })

# --- Save to Excel with Error Handling and Deduplication ---
if flat_data:
    try:
        # Load existing data if file/sheet exists
        if os.path.exists(EXCEL_PATH):
            try:
                existing_df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
                logging.info("Loaded existing Excel data.")
            except Exception as e:
                existing_df = pd.DataFrame()
                logging.warning(f"Could not load sheet '{SHEET_NAME}': {e}")
        else:
            existing_df = pd.DataFrame()

        new_df = pd.DataFrame(flat_data)
        if not existing_df.empty:
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            # Keep the latest info for each Key (update row if Key already exists)
            combined_df.drop_duplicates(subset=["Key"], keep="last", inplace=True)
        else:
            combined_df = new_df

        # Use append mode to preserve other sheets, replace only the target sheet
        with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            combined_df.to_excel(writer, sheet_name=SHEET_NAME, index=False)
        print(f"{Fore.GREEN}✅ Pulled {len(flat_data)} JIRA tickets.{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📁 Saved to: {EXCEL_PATH}{Style.RESET_ALL}")
        logging.info(f"Saved {len(combined_df)} unique tickets to Excel.")

        # --- Show vertical table summary in console ---
        def truncate(text, length=40):
            if pd.isna(text):
                return ""
            text = str(text).replace('\n', ' ').replace('\r', ' ')
            return text[:length] + ("..." if len(text) > length else "")

        summary_df = new_df.copy()
        summary_df["Summary"] = summary_df["Summary"]
        summary_df["Description"] = summary_df["Description"].apply(lambda x: truncate(x, 60))
        summary_df["Updated"] = pd.to_datetime(summary_df["Updated"]).dt.strftime('%Y-%m-%d %H:%M')

        display_cols = ["Key", "Project", "Summary", "Description", "Status", "Assignee", "Due Date", "Updated"]

        print(f"\n{Fore.YELLOW}JIRA Ticket Summary:{Style.RESET_ALL}")
        for idx, row in summary_df[display_cols].iterrows():
            print(f"{Fore.CYAN}{'-'*40}{Style.RESET_ALL}")
            print(f"{Fore.BLUE}Ticket {idx + 1}:{Style.RESET_ALL}")
            for col in display_cols:
                print(f"{Fore.GREEN}{col}:{Style.RESET_ALL} {row[col]}")
        print(f"{Fore.CYAN}{'-'*40}{Style.RESET_ALL}")

    except Exception as e:
        logging.error(f"Error saving to Excel: {e}")
        print(f"{Fore.RED}Error saving to Excel: {e}{Style.RESET_ALL}")
else:
    print(f"{Fore.YELLOW}No JIRA tickets found.{Style.RESET_ALL}")
    logging.info("No JIRA tickets found.")