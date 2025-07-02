import subprocess
import sys
import os
from colorama import Fore, Style

EXCEL_PATH = r"C:\Personal\Documents\ICON\Work Logs\Allan Adan - Work Activities, Tickets, and KPI.xlsx"

def run_script(script_name):
    try:
        subprocess.run([sys.executable, script_name], check=True)
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}❌ Failed to run {script_name}: {e}{Style.RESET_ALL}")

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def prompt_open_excel():
    answer = input(f"\n{Fore.CYAN}Would you like to open the Excel file now? (y/n): {Style.RESET_ALL}").strip().lower()
    if answer == "y":
        os.startfile(EXCEL_PATH)

def main():
    while True:
        clear_console()
        print(f"{Fore.GREEN}Select an option to run:{Style.RESET_ALL}")
        print("1. Pull Merge Requests from GitLab")
        print("2. Pull JIRA Tickets")
        print("q. Quit")
        choice = input("Enter option (1-2 or q): ").strip()

        if choice == "1":
            run_script("pull mr.py")
            prompt_open_excel()
        elif choice == "2":
            run_script("pull jira tickets.py")
            prompt_open_excel()
        elif choice.lower() == "q":
            print(f"{Fore.CYAN}Goodbye!{Style.RESET_ALL}")
            break
        else:
            print(f"{Fore.RED}Invalid choice. Exiting.{Style.RESET_ALL}")
            break

if __name__ == "__main__":
    main()