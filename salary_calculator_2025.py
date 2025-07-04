import locale
from fpdf import FPDF
from datetime import datetime
import os
import re

# --- CONFIG ---
LOGO_PLACEHOLDER_PATH = "./asset/images/logo-placeholder.jpg"
FONT_PATH = "./asset/fonts/dejavu-sans/DejaVuSans.ttf"
OUTPUT_PATH = "./public/files/"

# Set locale for currency formatting (Philippines)
try:
    locale.setlocale(locale.LC_ALL, 'en_PH.UTF-8')
except:
    locale.setlocale(locale.LC_ALL, '')  # fallback for systems without PH locale

# --- Input Section ---
print("📥 Philippine Salary Calculator (2025 Edition)")
print("============================================\n")

try:
    daily_rate = float(input("Enter daily rate (₱): "))
    workdays_per_week = int(input("Working days per week (e.g. 5): "))
except ValueError:
    print("\n❌ Invalid input. Please enter numeric values only.")
    exit()

# PDF custom header input
pdf_header = input("Enter company or team name for PDF header (e.g. Google): ")
logo_path = input("Enter path to your company logo file (JPG or PNG): ")
if not os.path.exists(logo_path):
    print("❌ Logo file not found. Setting to default.")
    logo_path = LOGO_PLACEHOLDER_PATH

weeks_per_month = 4.33
months_per_year = 12

# --- Gross Salary Computation ---
monthly_gross = daily_rate * workdays_per_week * weeks_per_month
semi_gross = monthly_gross / 2

# --- Mandatory Deductions: Employee Share ---
sss_employee = 630.00
philhealth_employee = 0.05 * min(max(monthly_gross, 10000), 100000)
pagibig_employee = min(0.02 * monthly_gross, 200.00)

# --- Employer Shares (based on common rates) ---
sss_employer = 880.00
philhealth_employer = philhealth_employee  # matched 50%
pagibig_employer = 100.00  # optional tiered based on policy

# --- Per Cutoff Values ---
semi_sss = sss_employee / 2
semi_ph = philhealth_employee / 2
semi_pagibig = pagibig_employee / 2

# --- Taxable Income ---
taxable_income = monthly_gross - (sss_employee + philhealth_employee + pagibig_employee)

def compute_tax(income):
    if income <= 20833:
        return 0
    elif income <= 33332:
        return (income - 20833) * 0.15
    elif income <= 66666:
        return 1875 + (income - 33333) * 0.20
    elif income <= 166666:
        return 8541.80 + (income - 66667) * 0.25
    elif income <= 666666:
        return 33541.80 + (income - 166667) * 0.30
    else:
        return 183541.80 + (income - 666667) * 0.35

monthly_tax = compute_tax(taxable_income)
semi_tax = monthly_tax / 2

# --- Net Computations ---
semi_net = semi_gross - (semi_sss + semi_ph + semi_pagibig + semi_tax)
monthly_net = semi_net * 2
annual_net = monthly_net * 12
thirteenth_month = monthly_gross
total_net_with_bonus = annual_net + thirteenth_month

# --- Console Output ---
def formatPeso(amount): return locale.currency(amount, symbol=True, grouping=True)

print("\n📄 SALARY BREAKDOWN (Per Cutoff)\n")
print(f"Gross Income        : {formatPeso(semi_gross)}")
print(f"SSS (Employee)      : {formatPeso(semi_sss)}")
print(f"PhilHealth          : {formatPeso(semi_ph)}")
print(f"Pag-IBIG            : {formatPeso(semi_pagibig)}")
print(f"Withholding Tax     : {formatPeso(semi_tax)}")
print(f"🟢 Net Pay           : {formatPeso(semi_net)}")

# --- Ask for PDF Export ---
export = input("\n🧾 Do you want to export this summary to PDF? (y/n): ").strip().lower()
if export != 'y':
    print("👍 Alright, no PDF generated.")
    exit()

# --- PDF Generation ---

class PDF(FPDF):
    def header(self):
        if os.path.exists(logo_path):
            self.image(logo_path, x=10, y=8, w=20)
        self.set_font("DejaVu", "B", 14)
        self.cell(0, 10, pdf_header, new_x="LMARGIN", new_y="NEXT", align="C")
        self.set_font("DejaVu", "", 11)
        self.cell(0, 10, f"Generated on: {datetime.now().strftime('%B %d, %Y')}", new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-12)
        self.set_font("DejaVu", "I", 8)
        self.cell(0, 10, "Generated by Allan's Salary Tool", align="C")

pdf = PDF()
pdf.add_font("DejaVu", "", FONT_PATH)
pdf.add_font("DejaVu", "B", FONT_PATH)
pdf.add_font("DejaVu", "I", FONT_PATH)
pdf.add_page()
pdf.set_font("DejaVu", "", 11)

# 1. Basic Details
pdf.set_font("DejaVu", "B", 12)
pdf.cell(0, 10, "1. Basic Details", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("DejaVu", "", 11)
pdf.cell(70, 8, "Daily Rate", border=1)
pdf.cell(60, 8, formatPeso(daily_rate), border=1, new_x="LMARGIN", new_y="NEXT")
pdf.cell(70, 8, "Workdays per Week", border=1)
pdf.cell(60, 8, str(workdays_per_week), border=1, new_x="LMARGIN", new_y="NEXT")
pdf.cell(70, 8, "Monthly Gross", border=1)
pdf.cell(60, 8, formatPeso(monthly_gross), border=1, new_x="LMARGIN", new_y="NEXT")
pdf.ln(5)

# 2. Mandatory Deductions Per Cutoff (Employee)
pdf.set_font("DejaVu", "B", 12)
pdf.cell(0, 10, "2. Mandatory Deductions Per Cutoff (Employee)", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("DejaVu", "", 11)
pdf.cell(70, 8, "SSS (Employee)", border=1)
pdf.cell(60, 8, formatPeso(semi_sss), border=1, new_x="LMARGIN", new_y="NEXT")
pdf.cell(70, 8, "PhilHealth (Employee)", border=1)
pdf.cell(60, 8, formatPeso(semi_ph), border=1, new_x="LMARGIN", new_y="NEXT")
pdf.cell(70, 8, "Pag-IBIG (Employee)", border=1)
pdf.cell(60, 8, formatPeso(semi_pagibig), border=1, new_x="LMARGIN", new_y="NEXT")
pdf.cell(70, 8, "Withholding Tax", border=1)
pdf.cell(60, 8, formatPeso(semi_tax), border=1, new_x="LMARGIN", new_y="NEXT")
# --- Add total deductions row ---
total_deductions = semi_sss + semi_ph + semi_pagibig + semi_tax
pdf.cell(70, 8, "Total Deductions", border=1)
pdf.cell(60, 8, formatPeso(total_deductions), border=1, new_x="LMARGIN", new_y="NEXT")
pdf.ln(5)

# 2.1 Employer Share Per Cutoff
pdf.set_font("DejaVu", "B", 12)
pdf.cell(0, 10, "2.1 Employer Share Per Cutoff", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("DejaVu", "", 11)
pdf.cell(70, 8, "SSS (Employer)", border=1)
pdf.cell(60, 8, formatPeso(sss_employer / 2), border=1, new_x="LMARGIN", new_y="NEXT")
pdf.cell(70, 8, "PhilHealth (Employer)", border=1)
pdf.cell(60, 8, formatPeso(philhealth_employer / 2), border=1, new_x="LMARGIN", new_y="NEXT")
pdf.cell(70, 8, "Pag-IBIG (Employer)", border=1)
pdf.cell(60, 8, formatPeso(pagibig_employer / 2), border=1, new_x="LMARGIN", new_y="NEXT")
pdf.ln(5)

# 3. Net Pay Per Cutoff
pdf.set_font("DejaVu", "B", 12)
pdf.cell(0, 10, "3. Net Pay Per Cutoff", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("DejaVu", "", 11)
pdf.cell(70, 8, "Gross Income", border=1)
pdf.cell(60, 8, formatPeso(semi_gross), border=1, new_x="LMARGIN", new_y="NEXT")
pdf.cell(70, 8, "Net Pay", border=1)
pdf.cell(60, 8, formatPeso(semi_net), border=1, new_x="LMARGIN", new_y="NEXT")
pdf.ln(5)

# 4. Summary Per Cutoff
pdf.set_font("DejaVu", "B", 12)
pdf.cell(0, 10, "4. Summary Per Cutoff", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("DejaVu", "", 11)
pdf.cell(70, 8, "Monthly Net Pay", border=1)
pdf.cell(60, 8, formatPeso(monthly_net), border=1, new_x="LMARGIN", new_y="NEXT")
pdf.cell(70, 8, "Annual Net (no bonus)", border=1)
pdf.cell(60, 8, formatPeso(annual_net), border=1, new_x="LMARGIN", new_y="NEXT")
pdf.cell(70, 8, "13th Month Bonus", border=1)
pdf.cell(60, 8, formatPeso(thirteenth_month), border=1, new_x="LMARGIN", new_y="NEXT")
pdf.cell(70, 8, "Total Net (with bonus)", border=1)
pdf.cell(60, 8, formatPeso(total_net_with_bonus), border=1, new_x="LMARGIN", new_y="NEXT")
pdf.ln(5)

# 5. Notes
pdf.set_font("DejaVu", "B", 12)
pdf.cell(0, 10, "5. Notes", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("DejaVu", "", 10)
pdf.multi_cell(0, 8, 
    "• All values are computed based on your input and 2025 PH government tables.\n"
    "• SSS, PhilHealth, and Pag-IBIG are employee share per cutoff.\n"
    "• Employer share is shown separately for transparency.\n"
    "• Withholding tax is computed using TRAIN law monthly brackets.\n"
    "• 13th month is computed as 1 month gross.\n"
    "• Actual take-home may vary due to company policy or other deductions."
)
pdf.ln(2)
pdf.set_font("DejaVu", "B", 11)
pdf.cell(0, 8, "5.1 Tax Bracket", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("DejaVu", "", 10)
if taxable_income <= 20833:
    bracket = "No tax (≤ ₱20,833)"
elif taxable_income <= 33332:
    bracket = "15% of excess over ₱20,833"
elif taxable_income <= 66666:
    bracket = "₱1,875 + 20% of excess over ₱33,333"
elif taxable_income <= 166666:
    bracket = "₱8,541.80 + 25% of excess over ₱66,667"
elif taxable_income <= 666666:
    bracket = "₱33,541.80 + 30% of excess over ₱166,667"
else:
    bracket = "₱183,541.80 + 35% of excess over ₱666,667"
pdf.cell(0, 8, f"Your monthly taxable income falls under: {bracket}", new_x="LMARGIN", new_y="NEXT")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
safe_header = re.sub(r'[^A-Za-z0-9 _-]', '', pdf_header).strip().replace(' ', '_')
output_file = f"{OUTPUT_PATH}salary_summary_{safe_header}_{timestamp}.pdf"
pdf.output(output_file)
print(f"\n✅ PDF successfully saved as: {output_file}")