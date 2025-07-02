# Automated Retrieval of JIRA Tickets

## Overview

This script automates the retrieval of JIRA tickets from your Atlassian instance, supports multiple filtering options, and saves the results to an Excel workbook. It also provides a readable summary in the console and robust error handling.

---

## Features

- **Fetches JIRA Tickets** using the JIRA REST API.
- **User-Selectable Filters:**
  - Ticket Scope:
    1. All JIRA Tickets
    2. Assigned To Me (Unresolved)
    3. Assigned To Me (Resolved and Unresolved)
    4. Watching (Tickets I Watch)
    5. Was Assigned To Me (Previously assigned, now others)
  - Date Range:
    - All
    - Today
    - This Week
    - This Month
- **Pagination:** Retrieves all tickets, not just the first page.
- **Excel Export:** Appends or updates ticket data in a specified Excel file and sheet, preserving other sheets.
- **Console Summary:** Displays a vertical, readable summary of each ticket.
- **Deduplication:** Updates existing tickets by Key, ensuring the latest data is kept.
- **Error Handling:** Handles HTTP, connection, and timeout errors gracefully. Logs all actions and errors.
- **Logging:** All actions and errors are logged to a timestamped log file.

---

## Usage

1. **Configure Credentials:**  
   Set your JIRA username and API token in the script.

2. **Run the Script:**  
   ```sh
   python "pull jira tickets.py"
   ```

3. **Select Options:**  
   - Choose the ticket scope (1-5).
   - Choose the date filter (a-d).

4. **Output:**  
   - Console: Vertical summary of tickets.
   - Excel: Data saved to  
     `C:\Personal\Documents\ICON\Work Logs\Allan Adan - Work Activities, Tickets, and KPI.xlsx`  
     in the sheet named `JIRA Tickets`.
   - Log: Activity and errors saved to a file like `jira_ticket_log_YYYY-MM.log`.

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

## Error Handling

- Handles HTTP, connection, and timeout errors gracefully.
- If Excel file or sheet is missing, it creates them.
- Logs all errors and actions to the log file.

---

## Notes

- The script appends new tickets and updates existing ones based on the "Key" column.
- Only the "JIRA Tickets" sheet is updated; other sheets in the workbook are preserved.
- The console summary is formatted vertically for readability.

---

## License

Internal use only.