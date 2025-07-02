# Automated Retrieval of Merge Request Documentation

## Overview

`pull mr.py` is a Python script that fetches your GitLab Merge Requests (MRs), summarizes them, and logs the results to an Excel file for tracking and reporting. It supports filtering by status and date, and provides a console summary as well as persistent logs.

---

## Features

- **Fetches Merge Requests** created by the authenticated user from GitLab.
- **Filter Options:**  
  - All Merge Requests  
  - Only Open  
  - This Month  
  - This Week  
  - Today
- **Console Summary:** Displays a readable summary of each MR.
- **Excel Export:** Appends or updates MR data in a specified Excel file and sheet.
- **Logging:** Logs activity and errors to a timestamped log file.
- **Project Mapping:** Maps known project IDs to friendly names/descriptions.

---

## Usage

1. **Configure Credentials:**  
   Set your GitLab personal access token in the `ACCESS_TOKEN` variable.

2. **Run the Script:**  
   ```sh
   python "pull mr.py"
   ```

3. **Select Filter:**  
   When prompted, enter a number (1-5) to select the MR filter.

4. **Output:**  
   - Console: Summary table of your MRs.
   - Excel: Data saved to  
     `C:\Personal\Documents\ICON\Work Logs\Allan Adan - Work Activities, Tickets, and KPI.xlsx`  
     in the sheet named `Merge Requests`.
   - Log: Activity and errors saved to a file like `gitlab_mr_log_YYYY-MM.log`.

---

## Configuration

- **ACCESS_TOKEN:**  
  Your GitLab personal access token (keep this secret).
- **EXCEL_PATH:**  
  Path to the Excel file for storing MR data.
- **SHEET_NAME:**  
  Name of the worksheet to update.

---

## Data Fields

Each Merge Request entry includes:
- ID
- MR Number
- JIRA Ticket (from labels)
- Project ID & Name
- Title
- Author
- Source/Target Branch
- Created At
- Merged Date
- Merge Status
- Reviewers
- Web URL
- Description
- Logged At (timestamp)

---

## Error Handling

- Handles HTTP, connection, and timeout errors gracefully.
- If Excel file or sheet is missing, it creates them.
- Logs all errors and actions to the log file.

---

## Requirements

- Python 3.x
- `requests`
- `pandas`
- `openpyxl`
- `colorama`
- `tabulate`

Install dependencies with:
```sh
pip install requests pandas openpyxl colorama tabulate
```

---

## Notes

- Only MRs created by the authenticated user are fetched.
- Project names are mapped for known project IDs; others show as "N/A".
- The script appends new MRs and avoids duplicates based on MR ID.

---

## License

Internal use only.