import requests
import pandas as pd
from openpyxl import load_workbook
from datetime import datetime, timedelta
import os
import logging
from colorama import init, Fore, Style
from tabulate import tabulate
from dotenv import load_dotenv
import math

load_dotenv()  # Loads variables from .env into environment

init(autoreset=True)

# Setup timestamped log file
log_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_time = datetime.now().strftime("%Y-%m")
log_filename = f"./logs/gitlab_mr_log_{log_time}.log"

logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


# --- Config ---
ACCESS_TOKEN = os.getenv("GITLAB_ACCESS_TOKEN")
API_URL = "https://gitlab.com/api/v4/merge_requests?scope=created_by_me&per_page=100"
EXCEL_PATH = os.getenv("EXCEL_PATH")
SHEET_NAME = "Merge Requests"

# --- Ask user for filter option ---
print(f"{Fore.GREEN}Select Merge Request filter:{Style.RESET_ALL}")
print("1. All Merge Requests")
print("2. Only Open")
print("3. This Month")
print("4. This Week")
print("5. Today")
choice = input("Enter option (1-5): ").strip()

print(f"{Fore.YELLOW}\n🔧 Selected filter: {choice}\n{Style.RESET_ALL}")

# Validate choice
if choice not in ["1", "2", "3", "4", "5"]:
    print(f"{Fore.RED}\n❌ Invalid choice. Defaulting to 'Only Open'.\n{Style.RESET_ALL}")
    choice = "2"

base_url = "https://gitlab.com/api/v4/merge_requests?scope=created_by_me&per_page=100"
now = datetime.now()
if choice == "2":
    API_URL = base_url + "&state=opened"
elif choice == "3":
    first_day = now.replace(day=1).strftime("%Y-%m-%dT00:00:00Z")
    API_URL = base_url + f"&created_after={first_day}"
elif choice == "4":
    start_of_week = (now - timedelta(days=now.weekday())).strftime("%Y-%m-%dT00:00:00Z")
    API_URL = base_url + f"&created_after={start_of_week}"
elif choice == "5":
    today = now.strftime("%Y-%m-%dT00:00:00Z")
    API_URL = base_url + f"&created_after={today}"
else:
    API_URL = base_url

# --- Step 1: Safely Fetch from GitLab ---
data = []
page = 1
while True:
    try:
        headers = {
            "Private-Token": ACCESS_TOKEN,
            "Content-Type": "application/json"
        }
        response = requests.get(f"{API_URL}&page={page}", headers=headers, timeout=15)
        response.raise_for_status()
        page_data = response.json()
        if not page_data:
            break
        data.extend(page_data)
        if len(page_data) < 100:
            break
        page += 1
    except requests.exceptions.HTTPError as errh:
        print(f"⚠️ HTTP error: {errh}")
        break
    except requests.exceptions.ConnectionError as errc:
        print(f"⚠️ Connection error: {errc}")
        break
    except requests.exceptions.Timeout as errt:
        print(f"⚠️ Timeout error: {errt}")
        break
    except requests.exceptions.RequestException as err:
        print(f"⚠️ Unexpected error: {err}")
        break

# --- Step 2: Flatten and Add Timestamp ---
flat_data = []
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Collection of projects (dictionary for lookup)
projects = {
    70107173: {
        "name": "erp-mobile",
        "description": "ERP Mobile",
    },
    67248689: {
        "name": "ticketing",
        "description": "Ticketing",
    },
    50252927: {
        "name": "icon-erp-v3",
        "description": "ERP Web",
    },
}

for mr in data:
    flat_data.append({
        "ID": mr.get("id"),
        "MR Number": mr.get("iid"),
        "JIRA Ticket": "; ".join(mr.get("labels", [])),
        "State": mr.get("state"),
        "Project ID": mr.get("project_id"),
        "Project Name": projects.get(mr.get("project_id"), {}).get("description", "N/A"),
        "Title": mr.get("title"),
        "Author": mr.get("author", {}).get("name"),
        "Source Branch": mr.get("source_branch"),
        "Target Branch": mr.get("target_branch"),
        "Created At": mr.get("created_at"),
        "Updated At": mr.get("updated_at"),
        "Merged Date": mr.get("merged_at"),
        "Merge Status": mr.get("merge_status"),
        "Reviewers": ", ".join([r.get("name") for r in mr.get("reviewers", [])]),
        "Web URL": mr.get("web_url"),
        "Description": mr.get("description"),
        "Logged At": timestamp
    })

# --- Log merge request count and contents ---
logging.info(f"[{timestamp}] {len(flat_data)} merge requests fetched.")
print(f"{Fore.GREEN}\n\n✅ Success:{Style.RESET_ALL} {len(flat_data)} merge requests fetched.\n\n")

# --- Load JIRA Tickets sheet for lookup ---
def get_jira_details(jira_keys, jira_excel_path, jira_sheet_name="JIRA Tickets"):
    """Fetch Summaries and Descriptions from JIRA Tickets sheet by multiple Keys."""
    if not jira_keys or not os.path.exists(jira_excel_path):
        return "", ""
    try:
        jira_df = pd.read_excel(jira_excel_path, sheet_name=jira_sheet_name)
        summaries = []
        descriptions = []
        for key in [k.strip() for k in jira_keys.split(";") if k.strip()]:
            match = jira_df[jira_df["Key"] == key]
            if not match.empty:
                summary = match.iloc[0].get("Summary", "")
                description = match.iloc[0].get("Description", "")
                # Replace NaN with empty string
                if pd.isna(summary):
                    summary = ""
                if pd.isna(description):
                    description = ""
                summaries.append(str(summary))
                descriptions.append(str(description))
        return " | ".join(summaries) if summaries else "None", " | ".join(descriptions) if descriptions else "None"
    except Exception as e:
        print(f"{Fore.YELLOW}⚠️ Could not fetch JIRA details for {jira_keys}: {e}{Style.RESET_ALL}")
    return "None", "None"

# Show table summary in console
if flat_data:
    print("\n🗂️  Merge Request Summary:\n")
    for idx, mr in enumerate(flat_data, 1):
        jira_keys = mr.get("JIRA Ticket", "")
        jira_summary, jira_description = get_jira_details(jira_keys, EXCEL_PATH)
        details = {
            "JIRA Ticket":  jira_keys if jira_keys else "N/A",
            "Repo Name":  mr.get("Project Name", "N/A"),
            "Title": mr.get("Title", "N/A"),
            "Source Branch": mr.get("Source Branch", "N/A"),
            "Target Branch": mr.get("Target Branch", "N/A"),
            "Created At": mr.get("Created At", "N/A"),
            "MR Link": mr.get("Web URL", "N/A"),
            "MRDescription": mr.get("Description", "N/A"),
            "JIRA Summary": jira_summary,
            "JIRA Description": jira_description,
        }
        # Choose emoji based on MR state
        state_emoji = {
            "opened": "🟢",
            "merged": "🟣",
            "closed": "🔴",
            "locked": "🔒"
        }
        mr_state = mr.get("State", "").lower()
        emoji = state_emoji.get(mr_state, "🔹")
        print(f"{Fore.CYAN}{emoji} Merge Request #{mr.get('MR Number', 'N/A')} for Ticket {jira_keys} [{mr_state.capitalize() if mr_state else 'N/A'}]{Style.RESET_ALL}")
        print(tabulate(details.items(), tablefmt="plain"))
        print("-" * 60)

        # logging.info(f"[{timestamp}] Project Name: {mr.get('Project Name', 'N/A')} - Merge Request #{mr.get('MR Number', 'N/A')} for JIRA Ticket {jira_keys} - {mr.get('Title', 'N/A')}")
else:
    print("😶 No open merge requests found for this user.")
    exit()

df_new = pd.DataFrame(flat_data)
if df_new.empty:
    print(f"{Fore.YELLOW}⚠️ No new merge requests to write. Skipping Excel update.{Style.RESET_ALL}")


# --- Step 3: Load Existing Data ---
if os.path.exists(EXCEL_PATH):
    try:
        df_existing = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined.drop_duplicates(subset="ID", keep="last", inplace=True)
    except Exception as e:
        print(f"{Fore.YELLOW}⚠️ Could not read Excel file: {e}{Style.RESET_ALL}")
        df_combined = df_new
else:
    df_combined = df_new

# --- Step 4: Write Back to Excel ---
try:
    print(f"{Fore.YELLOW}🔧 Writing to Excel…{Style.RESET_ALL}")
    print(f"{Fore.CYAN}📁 Excel path: {EXCEL_PATH}")
    print(f"{Fore.CYAN}📝 Log file: {os.path.abspath(log_filename)}{Style.RESET_ALL}")

    if not os.path.exists(EXCEL_PATH):
        # File does not exist, create it with write mode
        with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="w") as writer:
            df_combined.to_excel(writer, sheet_name=SHEET_NAME, index=False)
        logging.info(f"Excel file created and {len(df_combined)} unique merge requests synced to '{SHEET_NAME}' sheet.")
        print(f"{Fore.GREEN}✅ Excel file created and {len(df_combined)} unique merge requests synced to '{SHEET_NAME}' sheet.{Style.RESET_ALL}")
    else:
        # File exists, update the sheet only
        with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df_combined.to_excel(writer, sheet_name=SHEET_NAME, index=False)
        logging.info(f"Synced {len(df_combined)} unique merge requests to '{SHEET_NAME}' sheet in Excel.")
        print(f"{Fore.GREEN}✅ Synced {len(df_combined)} unique merge requests to '{SHEET_NAME}' sheet in Excel.{Style.RESET_ALL}")

except Exception as e:
    logging.error(f"Failed to write to Excel: {e}")
    print(f"{Fore.YELLOW}⚠️ Failed to write to Excel: {e}{Style.RESET_ALL}")