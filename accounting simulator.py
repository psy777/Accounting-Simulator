import random
import sys
import re
from collections import defaultdict
from datetime import date, timedelta
import tkinter as tk
from tkinter import ttk, messagebox
import requests

class AccountingSimulator:
    """
    A full-year business simulator tracking daily transactions, General Ledger (GL), 
    Subledgers, and generating Financial Statements based on a chosen business type.
    Set in the 1950s with character interactions.
    """

    def __init__(self):
        self.business_type = None
        self.business_owner = None
        self.gl = {}
        self.subledgers = {"Accounts Receivable": {}, "Accounts Payable": {}}
        self.transactions = []
        self.current_date = date(1955, 1, 3) # Starting on a Monday (Jan 1st 1955 was a Saturday, we start on the first workday)
        self.end_date = date(1955, 12, 31)
        self.transactions_today = 0

        self.scenario_templates = self._load_templates()
        self.holidays = self._load_holidays()
        self.characters = self._load_characters()
        self.story_beats = self._load_story_beats()
        self.story_frames = self._load_story_frames()
        self.story_index = 0
        self.monthly_bills = self._load_monthly_bills()

        self.sensory_details = [
            "A ceiling fan hums overhead, pushing the scent of ledger ink through the room.",
            "Coffee percolates in the corner, its burble mingling with the rustle of paper.",
            "Sunlight slants across the desk, pooling over the neat stacks of invoices."
        ]

        # Recurring bill tracker to prevent implausible repeats
        self.last_bill_months = {}

        # Optional Ollama hookup for live narrative generation
        self.use_ollama = False
        self.ollama_model = "llama3"
        self.ollama_url = "http://localhost:11434"

        # GUI state
        self.gui_root = None
        self.gui_entry_lines = []
        self.gui_totals_var = None
        self.gui_date_var = None

    # --- Initialization and Setup ---
    
    def _load_characters(self):
        """Defines the business owners for narrative flavor."""
        return {
            "SERVICE": {
                "name": "Mr. Sterling",
                "dialogue": "Mr. Sterling nods at the ledger: 'Keep the courthouse folks confident—note every hour and receipt.'"
            },
            "RETAIL": {
                "name": "Mrs. Gable",
                "dialogue": "Mrs. Gable beams: 'Morning rush is over—file each slip so we remember who trusted us.'"
            },
            "MANUFACTURING": {
                "name": "Mr. Thorne",
                "dialogue": "Mr. Thorne hands you a clipboard: 'Steel moves fast; the ledger keeps us honest about what came in and went out.'"
            }
        }

    def _load_story_beats(self):
        """Creates a simple serialized storyline for each business type."""
        return {
            "SERVICE": [
                "Courthouse files pile up; Sterling wants each billed hour marked cleanly for the clerks.",
                "A rival firm opens nearby and Sterling says tidy books will win steady clients.",
                "Couriers drop envelopes while a radio hums swing tunes; you tally hours.",
                "A junior asks you to stitch loose expenses into one summary before lunch.",
                "A magazine may profile local firms; Sterling wants the numbers photo-ready."],
            "RETAIL": [
                "Mrs. Gable sketches a picnic display and wants the costs tucked neatly into inventory.",
                "The Rossi family starts a tab; you track each receipt as neighborhood trust.",
                "Delivery boys race in with crates while the register rings—log sales and stock drops.",
                "A salesman offers discounts on canned peaches if you note early payment terms.",
                "Harvest posters stack up; Gable wants spotless books before crowds arrive."],
            "MANUFACTURING": [
                "Thorne spreads blueprints for a new contract; inspectors may visit, so costs must be crisp.",
                "The factory whistle cracks; you ready payroll slips while presses warm.",
                "An engineer asks how job costs stack; you point to orderly columns.",
                "Steel clatters off rail cars and the foreman shouts for invoices—you anchor the chaos.",
                "An efficiency expert paces with a stopwatch; Thorne trusts the books to defend the spend."],
        }

    def _load_story_frames(self):
        """Provides guided prompts so narration matches bookkeeping actions."""
        return {
            "SERVICE": {
                "voice": "Measured, civic-minded, quick to praise careful documentation for professional clients.",
                "ledger_cue": "Emphasize receivables aging, billable hours, and reimbursable expenses for courthouse and office calls.",
            },
            "RETAIL": {
                "voice": "Warm and bustling, grounded in neighborhood trust and tidy tabs behind the counter.",
                "ledger_cue": "Track inventory flows, cash drawer integrity, and which grocer tabs need a fresh tick mark.",
            },
            "MANUFACTURING": {
                "voice": "Industrial and steady, focused on contracts, materials, and payroll a foreman could audit.",
                "ledger_cue": "Highlight raw material batches, job cost postings, and vendor schedules supporting the factory floor.",
            },
        }

    def _setup_ai_adapter(self):
        """Optional Ollama hookup to enrich narration with local LLM output."""
        choice = input("Use Ollama for live story narration? (y/N): ").strip().lower()
        if choice != 'y':
            print("Using built-in story templates.")
            return

        model = input("Enter Ollama model name [llama3]: ").strip() or self.ollama_model
        url = input("Enter Ollama base URL [http://localhost:11434]: ").strip() or self.ollama_url

        self.use_ollama = True
        self.ollama_model = model
        self.ollama_url = url
        print(f"Ollama enabled with model '{self.ollama_model}' at {self.ollama_url}.")

    def _narrate_with_ai(self, section_label, base_scene):
        """Send a short prompt to Ollama, falling back gracefully on failure."""
        if not self.use_ollama:
            return base_scene

        prompt = (
            "You are a warm 1950s narrator for a bookkeeping adventure. "
            "Retell the scene vividly in 2-3 short sentences with period detail.\n"
            f"Section: {section_label}\n"
            f"Business Type: {self.business_type}\n"
            f"Owner Voice: {self.business_owner['name']}\n"
            f"Scene:\n{base_scene}\n"
            "Keep it concise and do not add questions."
        )

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={"model": self.ollama_model, "prompt": prompt, "stream": False},
                timeout=18,
            )
            if response.ok:
                data = response.json()
                ai_text = data.get("response", "").strip()
                if ai_text:
                    return ai_text
        except Exception:
            pass

        return base_scene + "\n[Ollama unavailable; using built-in narration.]"

    def _build_daily_intro(self):
        """Constructs a narrative opening for the day."""
        detail = random.choice(self.sensory_details)
        beat = self.story_beats[self.business_type][self.story_index % len(self.story_beats[self.business_type])]
        owner = self.business_owner
        frame = self.story_frames[self.business_type]

        lines = [
            f"{owner['name']} greets you and points at the day’s stack.",
            owner['dialogue'],
            beat,
            f"Ledger cue: {frame['ledger_cue']}",
            detail,
        ]

        self.story_index += 1
        return self._narrate_with_ai("daily intro", "\n".join(lines))

    def _lead_into_event(self, idx, total):
        """Provides a short story transition for each business event."""
        transitions = [
            "You flip to a fresh line in the journal.",
            "The desk lamp halos the page as you ready your pencil.",
            "A breeze from the open window stirs the papers, reminding you to keep pace.",
            "You sip the last of the coffee and nod to the next task.",
            "In the hallway, footsteps fade—leaving you with the numbers."
        ]
        lead = random.choice(transitions)
        return f"Scene {idx}/{total} — {lead}"

    def _ledger_story_prompt(self, suggested_debit):
        """Aligns the storytelling cue with a bookkeeping hint so prompts feel intentional."""
        cues = {
            "Accounts Receivable": "Note who owes us and mirror the balance in the AR subledger.",
            "Accounts Payable": "Record the vendor's name and tick the AP control to match the subsidiary listing.",
            "Inventory": "Show the stock moving in or out; pair revenue with cost if goods left the shelves.",
            "Cash": "Mark the cash drawer or bank column to keep the daily proof tight.",
            "Cost of Goods Sold": "Tie the expense line to the related sale so gross margin makes sense on the worksheet.",
            "Utilities Expense": "Route upkeep and services here; these sit under operating expenses.",
            "Rent Expense": "Accrue the month's space cost even if paid earlier as prepaid rent.",
            "Depreciation Expense": "Post the wear and tear with a matching credit to Accumulated Depreciation.",
            "Notes Payable": "Reduce the note and separate any interest if needed.",
        }
        default = "Keep the debits and credits in story order so the ledger reads like the day unfolded."
        return cues.get(suggested_debit, default)

    def _load_templates(self):
        """Defines the pool of transaction building blocks with 1950s flavor."""
        return {
            "ALL": [
                ("Paid $XX cash to the telephone switchboard operator for long-distance business calls.", 12, 35, "Utilities Expense"),
                ("Issued $XX of Common Stock for cash (new investment from a silent partner).", 500, 5000, "Cash"),
                ("Purchased $XX of new office furniture by issuing a Note Payable; the delivery boys track sawdust through the hallway.", 500, 3000, "Equipment"),
                ("Made $XX payment toward the bank loan (Notes Payable liability).", 100, 1000, "Notes Payable"),
                ("Received $XX cash from a non-core service, like copying blueprints for a neighbor; they chat about the Korean armistice while you work.", 50, 200, "Cash"),
                ("Paid $XX cash for minor upkeep on the typewriter after the ribbon snapped mid-report.", 50, 150, "Utilities Expense"), # Catch-all expense
            ],
            "SERVICE": [
                ("Billed Customer 'Capitol Studios' $XX for completed consulting work on credit. Mr. Sterling expects prompt payment.", 500, 5000, "Accounts Receivable"),
                ("Received payment of $XX cash from Customer 'XYZ Corp' on account. Mr. Sterling grins and taps the ledger appreciatively.", 500, 5000, "Cash"),
                ("Performed $XX in services for a quick client, immediately paid in cash after a lively office debate over jazz records.", 200, 3000, "Cash"),
                ("Traveled downtown and charged $XX in train fare to visit a courthouse client; keep the receipt for reimbursement.", 5, 30, "Utilities Expense"),
            ],
            "RETAIL": [
                ("Purchased $XX of canned goods (Inventory) on credit from Vendor 'SupplyCo'.", 800, 7000, "Inventory"),
                ("Paid $XX cash to Vendor 'SupplyCo' on account. Mrs. Gable reminds you to keep track of discounts!", 500, 5000, "Accounts Payable"),
                ("Sold goods on credit for $XX (Cost $YY) to Customer 'MaxRetail'. This was a large order for a local diner.", 500, 5000, "Accounts Receivable"),
                ("Received $XX cash from Customer 'MaxRetail' on account. The delivery driver thanks you for keeping the books straight.", 500, 5000, "Cash"),
                ("Sold groceries for $XX cash (Cost $YY). The cash register tape is full and smells faintly of fresh bread.", 200, 3000, "Cash"),
                ("Paid $XX cash for an in-store radio advertisement to play during Saturday rush hour.", 40, 120, "Utilities Expense"),
            ],
            "MANUFACTURING": [
                ("Purchased $XX of raw steel (Inventory) on credit from 'SteelCorp' for the new contract.", 1000, 10000, "Inventory"),
                ("Paid $XX cash to Vendor 'SteelCorp' on account to ensure materials keep flowing.", 1000, 10000, "Accounts Payable"),
                ("Paid $XX cash for the factory floor workers' weekly wages (Cost of Goods Sold).", 500, 5000, "Cost of Goods Sold"),
                ("Billed Customer 'MegaBuild' $XX (Cost $YY) for custom metalwork delivery on credit.", 5000, 20000, "Accounts Receivable"),
                ("Paid $XX cash to repair a conveyor belt after a late-night breakdown; the foreman is grateful.", 120, 450, "Utilities Expense"),
            ],
            "ADJUSTMENT": [
                ("Record end-of-month wear-and-tear (depreciation) on factory machinery: $XX.", 50, 200, "Depreciation Expense"),
                ("Recognize one month of Prepaid Office Rent expense: $YY. Mr. Sterling needs the expense booked.", 50, 150, "Rent Expense"),
            ]
        }

    def _load_monthly_bills(self):
        """Monthly or low-frequency bills that should not repeat unrealistically."""
        return [
            {
                "name": "Electricity",
                "account": "Utilities Expense",
                "template": "Settled the monthly electric statement with Power Co. for $XX in cash after the evening meter reading.",
                "min": 25,
                "max": 85,
                "day_window": (3, 8),
            },
            {
                "name": "OfficeCleaning",
                "account": "Utilities Expense",
                "template": "Paid $XX cash to the janitorial service for a deep clean before the town's business review board visit.",
                "min": 18,
                "max": 60,
                "day_window": (12, 18),
            },
        ]

    def _load_holidays(self):
        """Defines holiday easter eggs for flavor."""
        return {
            date(1955, 1, 1): "New Year's Day: Received $500.00 gift from founder (Common Stock). The office is closed, but you note the post-dated check.",
            date(1955, 2, 14): "Valentine's Day: Sent out $100.00 cash for employee gifts (Utilities Expense). Mrs. Gable insisted on a small celebration.",
            date(1955, 7, 4): "Independence Day: Large $5,000.00 cash sale to the local town council for event supplies (Cost $2,000.00).",
            date(1955, 12, 25): "Christmas Day: Paid $2,000.00 year-end bonus to employees (Utilities Expense).",
        }

    def _setup_accounts(self, business_type):
        """Initializes GL based on the selected business type."""
        # Base Accounts (DR positive, CR negative)
        initial_gl = {
            "Cash": 20000.00,
            "Accounts Receivable": 0.00,
            "Inventory": 10000.00 if business_type in ["RETAIL", "MANUFACTURING"] else 0.00,
            "Equipment": 5000.00,
            "Prepaid Rent": 3600.00, # 1 year prepaid
            "Accumulated Depreciation": 0.00, 
            "Accounts Payable": 0.00,
            "Notes Payable": -15000.00,
            "Common Stock": 0.00,
            "Retained Earnings": 0.00,
            "Sales Revenue": 0.00,
            "Cost of Goods Sold": 0.00,
            "Rent Expense": 0.00,
            "Depreciation Expense": 0.00,
            "Utilities Expense": 0.00,
        }
        
        # Auto-balance Common Stock initially
        total_assets = initial_gl['Cash'] + initial_gl['Inventory'] + initial_gl['Equipment'] + initial_gl['Prepaid Rent']
        total_liabilities = abs(initial_gl['Notes Payable'])
        initial_gl['Common Stock'] = -(total_assets - total_liabilities) 

        self.gl = initial_gl
        self.business_type = business_type
        self.business_owner = self.characters[business_type]

    # --- Account Helpers ---

    def _get_account_type(self, acc):
        """Internal helper to classify account type."""
        if acc in ["Cash", "Accounts Receivable", "Inventory", "Equipment", "Prepaid Rent"]: return "Asset"
        if acc in ["Accumulated Depreciation"]: return "Contra-Asset"
        if acc in ["Accounts Payable", "Notes Payable"]: return "Liability"
        if acc in ["Common Stock", "Retained Earnings"]: return "Equity"
        if acc in ["Sales Revenue"]: return "Revenue"
        return "Expense" # COGS, Rent, Depreciation, Utilities

    # --- Scenario Generation ---

    def _is_weekend(self, date_obj):
        """Checks if a date is a Saturday (5) or Sunday (6)."""
        return date_obj.weekday() >= 5 
    
    def _parse_amount_from_scenario(self, scenario_text):
        """Extracts the principal dollar amount from the scenario text."""
        # Finds numbers formatted as $X,XXX.XX or $XXX.XX
        # We look for the first dollar amount to be the principal transaction amount
        matches = re.findall(r'\$[\d,]+\.\d{2}', scenario_text)
        
        if matches:
            # Return the first matched amount as a float
            return float(matches[0].replace('$', '').replace(',', ''))
        return 0.0 # Safety fallback

    def _generate_daily_scenario(self):
        """Generates a list of daily transactions based on date and business type."""
        
        scenarios = []

        # 1. Check for Holiday Easter Eggs
        holiday_event = self.holidays.get(self.current_date)
        if holiday_event:
            # For simplicity, holidays are treated as a single event with no suggested debit
            scenarios.append((holiday_event, None))

        # 1b. Add scheduled monthly bills within their time windows
        for bill in self.monthly_bills:
            last_month = self.last_bill_months.get(bill["name"])
            in_window = bill["day_window"][0] <= self.current_date.day <= bill["day_window"][1]
            if last_month != self.current_date.month and in_window and not self._is_weekend(self.current_date):
                amount = round(random.uniform(bill["min"], bill["max"]), 2)
                scenarios.append((bill["template"].replace("$XX", f"${amount:,.2f}"), bill["account"]))
                self.last_bill_months[bill["name"]] = self.current_date.month

        # 2. Daily Routine Transactions (1-3 events per day)
        # Structure: (template_string, min_amt, max_amt, suggested_debit_account)
        transaction_pool = self.scenario_templates["ALL"] + self.scenario_templates[self.business_type]
        
        num_transactions = random.randint(1, 3)
        
        # Adjust frequency for month-end adjustments (last workday of the month)
        is_month_end = (self.current_date + timedelta(days=1)).month != self.current_date.month and not self._is_weekend(self.current_date)

        # 3. Add Adjustments on the last day of the month
        if is_month_end:
            if random.random() < 0.8: # High chance for an adjustment on month-end
                transaction_pool.extend(self.scenario_templates["ADJUSTMENT"])
                num_transactions = min(num_transactions + 1, 4)

        for _ in range(num_transactions):
            template_tuple = random.choice(transaction_pool)
            template, min_amt, max_amt, _ = template_tuple
            
            amount = round(random.uniform(min_amt, max_amt), 2)
            
            # Special handling for Inventory cost (Cost of Goods Sold)
            if '(Cost $YY)' in template:
                cogs = round(amount * 0.4, 2)
                
                # Check for inventory constraint (only applicable if Inventory is needed for transaction)
                if 'Sold goods' in template or 'Billed Customer' in template:
                    if cogs > self.gl.get("Inventory", 0):
                        cogs = max(10, round(self.gl.get("Inventory", 0) * 0.5, 2))
                        amount = round(cogs / 0.4, 2)

                template = template.replace("$XX", f"${amount:,.2f}").replace("$YY", f"${cogs:,.2f}")
            else:
                template = template.replace("$XX", f"${amount:,.2f}")

            # Special handling for Prepaid Rent adjustment
            if 'Prepaid Office Rent expense: $YY' in template:
                monthly_rent = round(self.gl.get("Prepaid Rent", 0) / 12, 2)
                template = template.replace("$YY", f"${monthly_rent:,.2f}")
            
            scenarios.append((template, template_tuple[3])) # return (scenario_text, suggested_debit)
            
        return scenarios

    # --- Financial Reporting (omitted for brevity, remains unchanged) ---

    def print_chart_of_accounts(self):
        """Displays the GL as a structured Trial Balance report."""
        print("\n" + "=" * 80)
        print(f"TRIAL BALANCE - As of {self.current_date.strftime('%B %d, %Y')} | Business Type: {self.business_type}")
        print("=" * 80)
        print(f"{'Account':<30} | {'Type':<15} | {'DEBIT (DR)':>15} | {'CREDIT (CR)':>15}")
        print("-" * 80)
        
        debit_sum, credit_sum = 0.0, 0.0

        for acc in sorted(self.gl.keys()):
            bal = self._calculate_real_balance(acc) # Use helper to calculate DR/CR balance
            acc_type = self._get_account_type(acc)
            
            dr_amount = abs(bal) if bal >= 0 else 0.0
            cr_amount = abs(bal) if bal < 0 else 0.0
            
            debit_sum += dr_amount
            credit_sum += cr_amount

            print(f"{acc:<30} | {acc_type:<15} | ${dr_amount:,.2f}{'':>1} | ${cr_amount:,.2f}{'':>1}")
            
        print("=" * 80)
        print(f"{'TOTALS':<48} | ${debit_sum:,.2f} | ${credit_sum:,.2f}")
        print("=" * 80)
        
        if abs(debit_sum - credit_sum) < 0.01:
            print("Trial Balance Status: Balanced (Debits = Credits)")
        else:
            print(f"Trial Balance Status: OUT OF BALANCE by ${abs(debit_sum - credit_sum):,.2f}!")
        print("-" * 80)
        
    def _calculate_real_balance(self, acc):
        """Returns the actual positive/negative balance from GL."""
        return self.gl.get(acc, 0.0)

    # --- Reporting helpers for GUI rendering ---

    def get_trial_balance_rows(self):
        rows = []
        debit_sum, credit_sum = 0.0, 0.0
        for acc in sorted(self.gl.keys()):
            bal = self._calculate_real_balance(acc)
            dr_amount = abs(bal) if bal >= 0 else 0.0
            cr_amount = abs(bal) if bal < 0 else 0.0
            debit_sum += dr_amount
            credit_sum += cr_amount
            rows.append((acc, self._get_account_type(acc), dr_amount, cr_amount))
        return rows, debit_sum, credit_sum

    def get_income_statement_summary(self):
        revenue_lines, expense_lines = [], []
        revenue_sum = 0.0
        expense_sum = 0.0
        for acc, bal in self.gl.items():
            if self._get_account_type(acc) == "Revenue":
                revenue_sum += abs(bal)
                revenue_lines.append((acc, abs(bal)))
            elif self._get_account_type(acc) == "Expense":
                expense_sum += bal
                expense_lines.append((acc, bal))
        net_income = revenue_sum - expense_sum
        return revenue_lines, expense_lines, revenue_sum, expense_sum, net_income

    def get_balance_sheet_summary(self):
        assets, liabilities, equity = defaultdict(float), defaultdict(float), defaultdict(float)
        for acc, bal in self.gl.items():
            acc_type = self._get_account_type(acc)
            display_bal = abs(bal)
            if acc_type == "Asset":
                assets[acc] = bal
            elif acc_type == "Contra-Asset":
                assets[acc] = -display_bal
            elif acc_type == "Liability":
                liabilities[acc] = display_bal
            elif acc_type == "Equity":
                equity[acc] = display_bal
        current_net_income = self._calculate_net_income()
        equity['Current Net Income'] = current_net_income
        total_assets = sum(assets.values())
        total_liabilities = sum(liabilities.values())
        total_equity = sum(equity.values())
        return assets, liabilities, equity, total_assets, total_liabilities, total_equity

    def _calculate_net_income(self):
        """Helper to calculate net income for reporting."""
        revenue_sum = 0.0
        expense_sum = 0.0
        
        for acc, bal in self.gl.items():
            acc_type = self._get_account_type(acc)
            if acc_type == "Revenue":
                revenue_sum += abs(bal)
            elif acc_type == "Expense":
                expense_sum += bal
        
        return revenue_sum - expense_sum

    def print_income_statement(self):
        """Calculates and prints the Income Statement."""
        revenue_sum = 0.0
        expense_sum = 0.0
        
        print("\n" + "=" * 40)
        print(f"INCOME STATEMENT (Through {self.current_date.strftime('%B %d')})")
        print("=" * 40)
        
        # Revenue Section
        print(f"{'REVENUE':<25}")
        for acc, bal in self.gl.items():
            if self._get_account_type(acc) == "Revenue":
                revenue_sum += abs(bal)
                print(f"  {acc:<23} ${abs(bal):,.2f}")
        print("-" * 40)
        print(f"{'Total Revenue:':<25} ${revenue_sum:,.2f}")

        # Expense Section
        print("\nEXPENSES:")
        for acc, bal in self.gl.items():
            if self._get_account_type(acc) == "Expense":
                expense_sum += bal
                print(f"  {acc:<23} ${bal:,.2f}")
        print("-" * 40)
        print(f"{'Total Expenses:':<25} ${expense_sum:,.2f}")
        print("=" * 40)
        
        net_income = revenue_sum - expense_sum
        print(f"{'NET INCOME / (LOSS):':<25} ${net_income:,.2f}")
        print("=" * 40)

    def print_balance_sheet(self):
        """Calculates and prints the Balance Sheet."""
        assets, liabilities, equity = defaultdict(float), defaultdict(float), defaultdict(float)
        
        # Categorize and sum balances
        for acc, bal in self.gl.items():
            acc_type = self._get_account_type(acc)
            display_bal = abs(bal)
            
            if acc_type == "Asset":
                assets[acc] = bal
            elif acc_type == "Contra-Asset":
                assets[acc] = -display_bal # Contra-assets reduce total assets
            elif acc_type == "Liability":
                liabilities[acc] = display_bal
            elif acc_type == "Equity":
                equity[acc] = display_bal

        total_assets = sum(assets.values())
        total_liabilities = sum(liabilities.values())
        
        # Calculate current period's retained earnings impact
        current_net_income = self._calculate_net_income()
        
        # Balance Sheet must include the temporary accounts' effect on Retained Earnings
        equity['Current Net Income'] = current_net_income
        total_equity = sum(equity.values())
        
        # Render Report
        print("\n" + "=" * 40)
        print(f"BALANCE SHEET (As of {self.current_date.strftime('%B %d, %Y')})")
        print("=" * 40)
        
        # ASSETS
        print(f"{'ASSETS':<25} | {'BALANCE':>10}")
        print("-" * 40)
        for acc in sorted(assets.keys()):
            bal = assets[acc]
            if acc == "Accumulated Depreciation":
                 print(f"  Less: {acc:<18} (${abs(bal):,.2f})")
            else:
                 print(f"  {acc:<23} ${bal:,.2f}")
        print("-" * 40)
        print(f"{'TOTAL ASSETS:':<25} ${total_assets:,.2f}")
        print("=" * 40)
        
        # LIABILITIES + EQUITY
        L_plus_E = total_liabilities + total_equity
        print(f"{'LIABILITIES & EQUITY':<25} | {'BALANCE':>10}")
        print("-" * 40)
        
        print("Liabilities:")
        for acc in sorted(liabilities.keys()):
            print(f"  {acc:<23} ${liabilities[acc]:,.2f}")
        print("-" * 40)
        print(f"{'Total Liabilities:':<25} ${total_liabilities:,.2f}")

        print("\nEquity:")
        for acc in sorted(equity.keys()):
            print(f"  {acc:<23} ${equity[acc]:,.2f}")
        print("-" * 40)
        print(f"{'Total Equity:':<25} ${total_equity:,.2f}")
        print("=" * 40)

        # Final Check
        if abs(total_assets - L_plus_E) < 0.01:
             print("A = L + E Check: OK (Assets match Liabilities + Equity)")
        else:
             print(f"A = L + E Check: FAILED! Differs by ${abs(total_assets - L_plus_E):,.2f}")
        print("=" * 40)


    # --- Game Flow (Updated run_daily_scenario) ---

    def advance_day(self):
        """Moves the game forward one day, skipping weekends."""
        self.current_date += timedelta(days=1)
        self.transactions_today = 0
        
        # Skip weekend days
        while self.current_date <= self.end_date and self._is_weekend(self.current_date):
            print(f"\n[Bookkeeper's Note] Skipping weekend: {self.current_date.strftime('%A, %B %d')}")
            self.current_date += timedelta(days=1)
            
        if self.current_date > self.end_date:
            print("\n*** CONGRATULATIONS! ***")
            print("You have successfully completed a full year of bookkeeping. The ledger is closed!")
            self.print_income_statement()
            self.print_balance_sheet()
            return True
        return False
        
    def run_daily_scenario(self):
        """Handles the daily interaction loop."""

        if self.advance_day(): # Advance and check for end of year
            sys.exit()

        scenarios_with_suggestions = self._generate_daily_scenario()

        print("\n" + "#" * 70)
        print(f"DAILY TRANSACTIONS FOR: {self.current_date.strftime('%A, %B %d, %Y')}")
        print("#" * 70)
        print(self._build_daily_intro())
        print("-" * 70)

        for i, (scenario, suggested_debit) in enumerate(scenarios_with_suggestions):

            # --- MODIFICATION: Extract Amount and Remove Hint ---
            transaction_amount = self._parse_amount_from_scenario(scenario)

            lead_in = self._lead_into_event(i + 1, len(scenarios_with_suggestions))
            ledger_cue = self._ledger_story_prompt(suggested_debit)
            story_scene = "\n".join([
                lead_in,
                scenario,
                f"Ledger cue: {ledger_cue}",
            ])
            narrated_scene = self._narrate_with_ai("event", story_scene)

            print(f"\n{narrated_scene}")
            if narrated_scene != story_scene:
                print(f"(Reference entry details: {scenario})")
            print("Prompt: Journal this as if you were writing in ink—list debits first, indent credits, and name the customer or vendor if one is involved.")

            # Pass the extracted amount to the entry system
            self.perform_journal_entry(transaction_amount)
            self.transactions_today += 1
            
        print("\n" + "=" * 70)
        print(f"All {len(scenarios_with_suggestions)} transactions for {self.current_date.strftime('%B %d')} are logged.")
        input("Press Enter to retire for the day and advance to the next workday...")
        
    # --- Entry Logic (Updated perform_journal_entry) ---

    def get_valid_account(self, prompt):
        """Helper to get a valid account name from the user, with fuzzy matching."""
        account_names = list(self.gl.keys())
        while True:
            acc_input = input(prompt).strip()
            if acc_input.lower() == 'done':
                return 'done'
            
            # Simple fuzzy matching (case-insensitive, prefix/partial match)
            matching_accounts = []
            for existing_acc in account_names:
                if existing_acc.lower() == acc_input.lower():
                    return existing_acc # Exact match
                if acc_input.lower() in existing_acc.lower(): # Check if input is a substring
                    matching_accounts.append(existing_acc)
            
            if len(matching_accounts) == 1:
                confirmed = input(f"  [Suggestion] Did you mean '{matching_accounts[0]}'? (y/n): ").strip().lower()
                if confirmed == 'y':
                    return matching_accounts[0]
                
            if len(matching_accounts) > 1:
                print("  [!] Multiple matches found. Please be more specific:")
                print(f"      Options: {', '.join(matching_accounts)}")
            else:
                print("  [!] Account not found. Try a different name.")
                print("      Available Accounts (partial list): Cash, Accounts Payable, Sales Revenue, Equipment...")

    def get_valid_amount(self, prompt):
        """Helper to get a valid numerical amount from the user."""
        while True:
            try:
                return float(input(prompt).strip().replace('$', '').replace(',', ''))
            except ValueError:
                print("  [!] Invalid amount. Please enter a number.")
                
    def handle_subledger_entry(self, account_name, amount, is_debit, entity):
        """Updates the specific entity's balance in the appropriate subledger using pre-collected entity name."""
        if account_name in self.subledgers:
            if not entity:
                print("  [!] Error: Subledger entry requires an entity name which was not provided.")
                return False

            if entity not in self.subledgers[account_name]:
                self.subledgers[account_name][entity] = 0.0
            
            # AR (Asset, DR Normal) increases with DR, decreases with CR
            if account_name == "Accounts Receivable":
                if is_debit:
                    self.subledgers[account_name][entity] += amount
                else:
                    self.subledgers[account_name][entity] -= amount

            # AP (Liability, CR Normal) decreases with DR, increases with CR
            elif account_name == "Accounts Payable":
                if is_debit:
                    self.subledgers[account_name][entity] -= amount
                else:
                    self.subledgers[account_name][entity] += amount
        return True

    def apply_journal_entry(self, entry):
        """Applies a validated journal entry to the GL and Subledgers."""
        for acc_name, amount, type, entity in entry:
            
            # 1. Update GL
            if type == 'DR':
                self.gl[acc_name] += amount
            else: # type == 'CR'
                self.gl[acc_name] -= amount 

            # 2. Update Subledger if required (uses entity name collected during entry)
            if acc_name in self.subledgers:
                self.handle_subledger_entry(acc_name, amount, type == 'DR', entity)

        print("\n=== TRANSACTION POSTED SUCCESSFULLY ===")
        self.transactions.append({"date": self.current_date, "lines": entry})

    def perform_journal_entry(self, total_transaction_amount=None):
        """Guides the user through entering a full journal entry, simplifying amount entry."""
        print("\n*** ENTER JOURNAL ENTRY ***")
        entry_lines = []
        total_debit = 0.0
        total_credit = 0.0
        
        # Determine the target amount (for manual entries, it might be None, so we set a flag)
        is_daily_scenario = total_transaction_amount is not None

        for entry_type in ['Debit', 'Credit']:
            print(f"\n--- {entry_type}s ---")
            
            while True:
                # Calculate remaining amount needed for this side to match the total transaction amount
                remaining_needed = (total_transaction_amount or 0.0) - (total_debit if entry_type == 'Debit' else total_credit)
                
                # Exit if the full amount is met for a daily scenario
                if is_daily_scenario and remaining_needed < 0.01:
                    break

                acc_name = self.get_valid_account(f"  {entry_type} Account (or 'done'): ")
                
                if acc_name.lower() == 'done':
                    # If done is entered but balance is not met in a daily scenario, warn
                    if is_daily_scenario and remaining_needed > 0.01:
                        print(f"  [!] WARNING: Transaction amount not fully met. Remaining needed: ${remaining_needed:,.2f}")
                    break
                
                amount = 0.0
                
                if is_daily_scenario:
                    # Daily Scenario: Default to remaining amount but allow override
                    prompt_amount = f"  Amount to {entry_type} {acc_name} (Enter for ${remaining_needed:,.2f}): $"
                    amount_input = input(prompt_amount).strip().replace('$', '').replace(',', '')

                    if not amount_input:
                        amount = round(remaining_needed, 2)
                    else:
                        try:
                            amount = round(float(amount_input), 2)
                            if amount > remaining_needed + 0.01:
                                print(f"  [!] Amount entered (${amount:,.2f}) exceeds remaining needed (${remaining_needed:,.2f}). Please enter a smaller amount.")
                                continue
                        except ValueError:
                            print("  [!] Invalid amount. Please enter a number or press Enter.")
                            continue
                
                else:
                    # Manual Entry (Option 6): Must manually enter amount
                    amount = self.get_valid_amount(f"  Amount to {entry_type} {acc_name}: $")
                
                
                if entry_type == 'Debit':
                    total_debit += amount
                    direction = 'DR'
                else:
                    total_credit += amount
                    direction = 'CR'
                    
                
                temp_sub_entry = None
                if acc_name in self.subledgers:
                    temp_sub_entry = input(f"  [Subledger Required] Enter Customer/Vendor Name for {acc_name}: ").strip()
                    if not temp_sub_entry:
                        print("  [!] Subledger entry is MANDATORY for this account. Cancelling line.")
                        # Undo the amount change since the entry was cancelled
                        if entry_type == 'Debit': total_debit -= amount
                        else: total_credit -= amount
                        continue

                entry_lines.append((acc_name, amount, direction, temp_sub_entry))
                print(f"  -> {direction} {acc_name}: ${amount:,.2f} recorded.")


        # Validation Check
        # For daily scenarios, check if both sides match the transaction amount
        # For manual entries (Option 6), check if debit == credit
        validation_check_amount = total_transaction_amount if is_daily_scenario else total_debit
        
        # Check if DR/CR balance matches the target amount (for daily scenarios) or each other (for manual entries)
        if is_daily_scenario and (abs(total_debit - validation_check_amount) > 0.01 or abs(total_credit - validation_check_amount) > 0.01):
             print("\n[!!! VALIDATION FAILED !!!]")
             print(f"Total Debits (${total_debit:,.2f}) and Total Credits (${total_credit:,.2f}) must both equal the Transaction Amount (${validation_check_amount:,.2f}).")
             print("Please try again.")
             return
        
        if not is_daily_scenario and abs(total_debit - total_credit) > 0.01:
            print("\n[!!! VALIDATION FAILED !!!]")
            print(f"Total Debits (${total_debit:,.2f}) != Total Credits (${total_credit:,.2f}).")
            print("The entry must balance. Please try again.")
            return

        if not entry_lines:
            print("No transaction lines entered. Returning to menu.")
            return

        self.apply_journal_entry(entry_lines)


    def print_subledgers(self):
        """Displays the details of the Subledgers and runs the integrity check."""
        print("\n--- SUBSIDIARY LEDGER DETAILS ---")
        
        for control_acc, entities in self.subledgers.items():
            gl_balance = self.gl[control_acc]
            subledger_sum = sum(entities.values())
            
            # For display consistency, convert GL balance to absolute value, which is what the subledger sums up to.
            print(f"\n[{control_acc} Control Account (GL Balance: ${abs(gl_balance):,.2f})]")
            
            if entities:
                for name, bal in entities.items():
                    print(f"  - {name:<20}: ${bal:,.2f}")
            else:
                print("  (No open balances)")
            
            if abs(abs(gl_balance) - subledger_sum) < 0.01:
                print(f"  INTEGRITY CHECK: OK (GL Balance matches Subledger sum of ${subledger_sum:,.2f})")
            else:
                print(f"  INTEGRITY CHECK: FAILED! GL Balance (${abs(gl_balance):,.2f}) does NOT match Subledger sum (${subledger_sum:,.2f}).")

        print("-" * 50)

    # --- GUI: Worksheets and Financial Statements ---

    def _refresh_trial_balance_view(self, tree, totals_label):
        tree.delete(*tree.get_children())
        rows, debit_sum, credit_sum = self.get_trial_balance_rows()
        for idx, (acc, acc_type, dr, cr) in enumerate(rows):
            tag = 'evenrow' if idx % 2 == 0 else 'oddrow'
            tree.insert('', tk.END, values=(acc, acc_type, f"${dr:,.2f}", f"${cr:,.2f}"), tags=(tag,))
        totals_label.config(text=f"Debits: ${debit_sum:,.2f} | Credits: ${credit_sum:,.2f}")


    def _refresh_income_statement_view(self, tree):
        tree.delete(*tree.get_children())
        revenue, expenses, revenue_sum, expense_sum, net = self.get_income_statement_summary()
        tree.insert('', tk.END, values=("REVENUE", ""), tags=('header',))
        for name, amount in revenue:
            tree.insert('', tk.END, values=(f"  {name}", f"${amount:,.2f}"))
        tree.insert('', tk.END, values=("  Total Revenue", f"${revenue_sum:,.2f}"), tags=('double',))
        tree.insert('', tk.END, values=("", ""))
        tree.insert('', tk.END, values=("EXPENSES", ""), tags=('header',))
        for name, amount in expenses:
            tree.insert('', tk.END, values=(f"  {name}", f"${amount:,.2f}"))
        tree.insert('', tk.END, values=("  Total Expenses", f"${expense_sum:,.2f}"), tags=('double',))
        tree.insert('', tk.END, values=("NET INCOME", f"${net:,.2f}"), tags=('total',))

    def _refresh_balance_sheet_view(self, tree):
        tree.delete(*tree.get_children())
        assets, liabilities, equity, total_assets, total_liabilities, total_equity = self.get_balance_sheet_summary()
        tree.insert('', tk.END, values=("ASSETS", ""), tags=('header',))
        for acc in sorted(assets.keys()):
            bal = assets[acc]
            prefix = "Less: " if acc == "Accumulated Depreciation" else ""
            tree.insert('', tk.END, values=(f"  {prefix}{acc}", f"${bal:,.2f}"))
        tree.insert('', tk.END, values=("  Total Assets", f"${total_assets:,.2f}"), tags=('double',))
        tree.insert('', tk.END, values=("", ""))
        tree.insert('', tk.END, values=("LIABILITIES", ""), tags=('header',))
        for acc in sorted(liabilities.keys()):
            tree.insert('', tk.END, values=(f"  {acc}", f"${liabilities[acc]:,.2f}"))
        tree.insert('', tk.END, values=("  Total Liabilities", f"${total_liabilities:,.2f}"), tags=('double',))
        tree.insert('', tk.END, values=("", ""))
        tree.insert('', tk.END, values=("EQUITY", ""), tags=('header',))
        for acc in sorted(equity.keys()):
            tree.insert('', tk.END, values=(f"  {acc}", f"${equity[acc]:,.2f}"))
        tree.insert('', tk.END, values=("  Total Equity", f"${total_equity:,.2f}"), tags=('double',))
        tree.insert('', tk.END, values=("BALANCE CHECK", f"${(total_assets - (total_liabilities + total_equity)):,.2f}"), tags=('total',))

    def _refresh_subledger_view(self, tree):
        tree.delete(*tree.get_children())
        row_idx = 0
        for control_acc, entities in self.subledgers.items():
            gl_balance = self.gl[control_acc]
            subledger_sum = sum(entities.values())
            status = "OK" if abs(abs(gl_balance) - subledger_sum) < 0.01 else "OUT OF BALANCE"
            tree.insert('', tk.END, values=(control_acc, "GL", f"${abs(gl_balance):,.2f}", status), tags=('header',))
            if entities:
                for name, bal in entities.items():
                    tag = 'evenrow' if row_idx % 2 == 0 else 'oddrow'
                    tree.insert('', tk.END, values=(f"  {name}", "Sub", f"${bal:,.2f}", ""), tags=(tag,))
                    row_idx += 1
            else:
                tree.insert('', tk.END, values=("  (No open balances)", "", "$0.00", ""))
            tree.insert('', tk.END, values=("  Total by subledger", "", f"${subledger_sum:,.2f}", status), tags=('double',))
    def _refresh_journal_log(self, tree):
        tree.delete(*tree.get_children())
        row_idx = 0
        for entry in self.transactions:
            entry_date = entry.get("date")
            for acc, amount, direction, entity in entry.get("lines", []):
                tag = 'evenrow' if row_idx % 2 == 0 else 'oddrow'
                debit_str = f"${amount:,.2f}" if direction == 'DR' else ""
                credit_str = f"${amount:,.2f}" if direction == 'CR' else ""
                tree.insert('', tk.END, values=(entry_date.strftime('%b %d'), acc, "", debit_str, credit_str, entity or "-"), tags=(tag,))
                row_idx += 1

    def _add_gui_line(self, account_var, amount_var, type_var, entity_var, tree):
        try:
            amount = float(amount_var.get())
        except ValueError:
            messagebox.showerror("Amount Error", "Please enter a numeric amount.")
            return
        acc_name = account_var.get()
        if not acc_name:
            messagebox.showerror("Account Error", "Choose an account before adding.")
            return
        if acc_name in self.subledgers and not entity_var.get().strip():
            messagebox.showerror("Subledger Required", "Enter a customer/vendor for this control account.")
            return
        direction = 'DR' if type_var.get() == 'Debit' else 'CR'
        line = (acc_name, amount, direction, entity_var.get().strip() or None)
        self.gui_entry_lines.append(line)
        debit_str = f"${amount:,.2f}" if direction == 'DR' else ""
        credit_str = f"${amount:,.2f}" if direction == 'CR' else ""
        tag = 'evenrow' if len(self.gui_entry_lines) % 2 == 0 else 'oddrow'
        tree.insert('', tk.END, values=(acc_name, debit_str, credit_str, entity_var.get().strip() or "—"), tags=(tag,))
        self._update_gui_totals()

    def _update_gui_totals(self):
        debit = sum(amount for acc, amount, drcr, _ in self.gui_entry_lines if drcr == 'DR')
        credit = sum(amount for acc, amount, drcr, _ in self.gui_entry_lines if drcr == 'CR')
        if self.gui_totals_var:
            self.gui_totals_var.set(f"Debits ${debit:,.2f} | Credits ${credit:,.2f}")

    def _post_gui_entry(self, tree, refreshers):
        debit = sum(amount for _, amount, drcr, _ in self.gui_entry_lines if drcr == 'DR')
        credit = sum(amount for _, amount, drcr, _ in self.gui_entry_lines if drcr == 'CR')
        if abs(debit - credit) > 0.01:
            messagebox.showerror("Entry Not Balanced", "Debits and credits must match before posting.")
            return
        if not self.gui_entry_lines:
            messagebox.showwarning("No Lines", "Add at least one line before posting.")
            return
        self.apply_journal_entry(self.gui_entry_lines)
        self.gui_entry_lines = []
        tree.delete(*tree.get_children())
        self._update_gui_totals()
        for cb in refreshers:
            cb()
        messagebox.showinfo("Posted", "Entry posted to the ledger.")

    def _advance_gui_day(self, date_label, story_box, scenario_box):
        intro = self._build_daily_intro()
        scenarios = self._generate_daily_scenario()
        scenario_text = "\n".join([
            f"- {text}\n    Ledger cue: {self._ledger_story_prompt(suggested)}" if suggested else f"- {text}"
            for text, suggested in scenarios
        ])
        story_box.configure(state='normal')
        story_box.delete('1.0', tk.END)
        story_box.insert(tk.END, intro)
        story_box.configure(state='disabled')
        scenario_box.configure(state='normal')
        scenario_box.delete('1.0', tk.END)
        scenario_box.insert(tk.END, scenario_text or "No scenarios today.")
        scenario_box.configure(state='disabled')
        self.advance_day()
        if self.gui_date_var:
            self.gui_date_var.set(self.current_date.strftime('%A, %B %d, %Y'))
        date_label.config(text=self.gui_date_var.get())


    def launch_gui(self):
        self.gui_root = tk.Tk()
        self.gui_root.title("1955 Accounting Simulator — Worksheets & Statements")
        self.gui_root.geometry("1100x760")
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Sheet.TFrame', background='#fdfaf3', borderwidth=1, relief='groove', padding=8)
        style.configure('Sheet.TLabel', background='#fdfaf3', font=('Helvetica', 11, 'bold'))
        style.configure('SheetText.TLabel', background='#fdfaf3', font=('Helvetica', 10))
        style.configure('Ledger.Treeview', font=('Courier New', 10), rowheight=26, bordercolor='#b7b1a5', borderwidth=1)
        style.configure('Ledger.Treeview.Heading', font=('Helvetica', 10, 'bold'), bordercolor='#6f6658', borderwidth=1, relief='raised')
        style.map('Ledger.Treeview', background=[('selected', '#d9ead3')])
        style.configure('Accent.TButton', font=('Helvetica', 10, 'bold'))
        self.gui_date_var = tk.StringVar(value=self.current_date.strftime('%A, %B %d, %Y'))
        header = ttk.Frame(self.gui_root)
        header.pack(fill='x', pady=6)
        ttk.Label(header, text=f"Business: {self.business_type}", font=('TkDefaultFont', 12, 'bold')).pack(side='left', padx=10)
        ttk.Label(header, textvariable=self.gui_date_var, font=('TkDefaultFont', 11)).pack(side='right', padx=10)

        notebook = ttk.Notebook(self.gui_root)
        notebook.pack(fill='both', expand=True)

        # Daily story tab
        story_tab = ttk.Frame(notebook, style='Sheet.TFrame')
        notebook.add(story_tab, text="Daily Story")
        ttk.Label(story_tab, text="Narrated Workday", style='Sheet.TLabel').pack(anchor='w', padx=10, pady=(12, 4))
        date_label = ttk.Label(story_tab, text=self.gui_date_var.get())
        date_label.pack(anchor='w', padx=10, pady=(0, 4))
        story_box = tk.Text(story_tab, height=6, wrap='word', font=('Courier New', 11), background='#fffdf7', relief='solid', borderwidth=1)
        story_box.pack(fill='x', padx=10)
        ttk.Label(story_tab, text="Scenario Notes", style='Sheet.TLabel').pack(anchor='w', padx=10, pady=(10, 4))
        scenario_box = tk.Text(story_tab, height=10, wrap='word', font=('Courier New', 11), background='#fffdf7', relief='solid', borderwidth=1)
        scenario_box.pack(fill='both', padx=10, pady=(0, 8), expand=True)
        advance_btn = ttk.Button(story_tab, text="Generate Workday & Advance", style='Accent.TButton', command=lambda: self._advance_gui_day(date_label, story_box, scenario_box))
        advance_btn.pack(pady=6)

        # Journal entry tab with form-style layout
        entry_tab = ttk.Frame(notebook, style='Sheet.TFrame')
        notebook.add(entry_tab, text="Journal Entry")
        pane = ttk.Panedwindow(entry_tab, orient=tk.HORIZONTAL)
        pane.pack(fill='both', expand=True, padx=6, pady=6)

        form_panel = ttk.Labelframe(pane, text="Journal Line", padding=10)
        pane.add(form_panel, weight=1)
        ttk.Label(form_panel, textvariable=self.gui_date_var).grid(row=0, column=0, columnspan=2, sticky='w')
        ttk.Label(form_panel, text="Account").grid(row=1, column=0, sticky='w')
        account_var = tk.StringVar(value="Cash")
        account_combo = ttk.Combobox(form_panel, textvariable=account_var, values=sorted(self.gl.keys()), state='readonly')
        account_combo.grid(row=2, column=0, padx=(0, 6), sticky='ew')
        ttk.Label(form_panel, text="Amount").grid(row=1, column=1, sticky='w')
        amount_var = tk.StringVar()
        ttk.Entry(form_panel, textvariable=amount_var).grid(row=2, column=1, padx=(0, 6), sticky='ew')
        ttk.Label(form_panel, text="Debit / Credit").grid(row=3, column=0, sticky='w')
        type_var = tk.StringVar(value='Debit')
        ttk.Radiobutton(form_panel, text='Debit', variable=type_var, value='Debit').grid(row=4, column=0, sticky='w')
        ttk.Radiobutton(form_panel, text='Credit', variable=type_var, value='Credit').grid(row=4, column=1, sticky='w')
        ttk.Label(form_panel, text="Customer or Vendor").grid(row=5, column=0, sticky='w')
        entity_var = tk.StringVar()
        ttk.Entry(form_panel, textvariable=entity_var).grid(row=6, column=0, columnspan=2, sticky='ew')
        ttk.Label(form_panel, text="Instruction: add one line per account, then post when balanced.", style='SheetText.TLabel').grid(row=7, column=0, columnspan=2, pady=(6,0), sticky='w')
        form_panel.columnconfigure(0, weight=1)
        form_panel.columnconfigure(1, weight=1)

        preview_panel = ttk.Labelframe(pane, text="Entry Preview", padding=8)
        pane.add(preview_panel, weight=2)
        entry_tree = ttk.Treeview(preview_panel, columns=("Account", "Debit", "Credit", "Party/Ref"), show='headings', style='Ledger.Treeview')
        for col, anchor, width in (("Account", 'w', 200), ("Debit", 'e', 110), ("Credit", 'e', 110), ("Party/Ref", 'w', 160)):
            entry_tree.heading(col, text=col, anchor=anchor)
            entry_tree.column(col, stretch=True, width=width, anchor=anchor)
        entry_tree.tag_configure('evenrow', background='#f0ece4')
        entry_tree.tag_configure('oddrow', background='#fffdf7')
        entry_tree.pack(fill='both', expand=True, padx=4, pady=4)

        self.gui_totals_var = tk.StringVar(value="Debits $0.00 | Credits $0.00")
        ttk.Label(preview_panel, textvariable=self.gui_totals_var, style='SheetText.TLabel').pack(anchor='e', padx=4)

        button_bar = ttk.Frame(preview_panel)
        button_bar.pack(anchor='e', pady=(4,0))
        ttk.Button(button_bar, text="Add Line", style='Accent.TButton', command=lambda: self._add_gui_line(account_var, amount_var, type_var, entity_var, entry_tree)).pack(side='left', padx=4)
        ttk.Button(button_bar, text="Clear", command=lambda: [entry_tree.delete(*entry_tree.get_children()), self.gui_entry_lines.clear(), self._update_gui_totals()]).pack(side='left', padx=4)

        # Ledger tab
        ledger_tab = ttk.Frame(notebook, style='Sheet.TFrame')
        notebook.add(ledger_tab, text="Trial Balance")
        ledger_header = ttk.Label(ledger_tab, text="Trial Balance", style='Sheet.TLabel')
        ledger_header.pack(anchor='center', pady=(10, 2))
        ttk.Label(ledger_tab, text="Account titles at left, reference types in the middle, ruling lines match DR | CR columns.", style='SheetText.TLabel').pack(anchor='center')
        ledger_tree = ttk.Treeview(ledger_tab, columns=("Account", "Type", "Debit", "Credit"), show='headings', style='Ledger.Treeview')
        for col, anchor in (("Account", 'w'), ("Type", 'w'), ("Debit", 'e'), ("Credit", 'e')):
            ledger_tree.heading(col, text=col, anchor=anchor)
            ledger_tree.column(col, stretch=True, width=160 if col == "Account" else 110, anchor=anchor)
        ledger_tree.tag_configure('evenrow', background='#f0ece4')
        ledger_tree.tag_configure('oddrow', background='#fffdf7')
        ledger_tree.pack(fill='both', expand=True, padx=10, pady=6)
        totals_label = ttk.Label(ledger_tab, text="", style='SheetText.TLabel')
        totals_label.pack(anchor='e', padx=12, pady=(0, 4))

        # Statements tab with income and balance side by side
        stmt_tab = ttk.Frame(notebook, style='Sheet.TFrame')
        notebook.add(stmt_tab, text="Statements")
        stmt_pane = ttk.Panedwindow(stmt_tab, orient=tk.HORIZONTAL)
        stmt_pane.pack(fill='both', expand=True, padx=8, pady=8)

        income_frame = ttk.Labelframe(stmt_pane, text="Income Statement", padding=6)
        stmt_pane.add(income_frame, weight=1)
        income_tree = ttk.Treeview(income_frame, columns=("Line", "Amount"), show='headings', style='Ledger.Treeview')
        for col, anchor, width in (("Line", 'w', 240), ("Amount", 'e', 140)):
            income_tree.heading(col, text=col, anchor=anchor)
            income_tree.column(col, width=width, anchor=anchor, stretch=True)
        income_tree.tag_configure('header', background='#e7dfcf', font=('Helvetica', 10, 'bold'))
        income_tree.tag_configure('double', background='#f0ece4')
        income_tree.tag_configure('total', background='#d9ead3', font=('Helvetica', 10, 'bold'))
        income_tree.pack(fill='both', expand=True, padx=4, pady=4)

        bs_frame = ttk.Labelframe(stmt_pane, text="Balance Sheet", padding=6)
        stmt_pane.add(bs_frame, weight=1)
        bs_tree = ttk.Treeview(bs_frame, columns=("Account", "Amount"), show='headings', style='Ledger.Treeview')
        for col, anchor, width in (("Account", 'w', 240), ("Amount", 'e', 140)):
            bs_tree.heading(col, text=col, anchor=anchor)
            bs_tree.column(col, width=width, anchor=anchor, stretch=True)
        bs_tree.tag_configure('header', background='#e7dfcf', font=('Helvetica', 10, 'bold'))
        bs_tree.tag_configure('double', background='#f0ece4')
        bs_tree.tag_configure('total', background='#d9ead3', font=('Helvetica', 10, 'bold'))
        bs_tree.pack(fill='both', expand=True, padx=4, pady=4)

        # Subledger tab
        sub_tab = ttk.Frame(notebook, style='Sheet.TFrame')
        notebook.add(sub_tab, text="Subledgers")
        sub_tree = ttk.Treeview(sub_tab, columns=("Name", "Type", "Balance", "Status"), show='headings', style='Ledger.Treeview')
        for col, anchor, width in (("Name", 'w', 200), ("Type", 'center', 70), ("Balance", 'e', 120), ("Status", 'w', 120)):
            sub_tree.heading(col, text=col, anchor=anchor)
            sub_tree.column(col, width=width, anchor=anchor, stretch=True)
        sub_tree.tag_configure('header', background='#e7dfcf', font=('Helvetica', 10, 'bold'))
        sub_tree.tag_configure('double', background='#f0ece4')
        sub_tree.tag_configure('evenrow', background='#f0ece4')
        sub_tree.tag_configure('oddrow', background='#fffdf7')
        sub_tree.pack(fill='both', expand=True, padx=10, pady=10)

        # Journal log tab
        log_tab = ttk.Frame(notebook, style='Sheet.TFrame')
        notebook.add(log_tab, text="General Journal")
        ttk.Label(log_tab, text="General Journal — debits at left, credits at right", style='Sheet.TLabel').pack(anchor='center', pady=(10, 4))
        log_tree = ttk.Treeview(log_tab, columns=("Date", "Account Title & Explanation", "PR", "Debit", "Credit", "Party/Ref"), show='headings', style='Ledger.Treeview')
        heading_spec = [
            ("Date", 'w', 80),
            ("Account Title & Explanation", 'w', 240),
            ("PR", 'center', 40),
            ("Debit", 'e', 110),
            ("Credit", 'e', 110),
            ("Party/Ref", 'w', 140),
        ]
        for col, anchor, width in heading_spec:
            log_tree.heading(col, text=col, anchor=anchor)
            log_tree.column(col, stretch=True, width=width, anchor=anchor)
        log_tree.tag_configure('evenrow', background='#f0ece4')
        log_tree.tag_configure('oddrow', background='#fffdf7')
        log_tree.pack(fill='both', expand=True, padx=10, pady=8)

        refresh_callbacks = [
            lambda: self._refresh_trial_balance_view(ledger_tree, totals_label),
            lambda: self._refresh_income_statement_view(income_tree),
            lambda: self._refresh_balance_sheet_view(bs_tree),
            lambda: self._refresh_subledger_view(sub_tree),
            lambda: self._refresh_journal_log(log_tree),
        ]

        ttk.Button(button_bar, text="Post Entry", command=lambda: self._post_gui_entry(entry_tree, refresh_callbacks)).pack(side='left', padx=4)

        self._refresh_trial_balance_view(ledger_tree, totals_label)
        self._refresh_income_statement_view(income_tree)
        self._refresh_balance_sheet_view(bs_tree)
        self._refresh_subledger_view(sub_tree)
        self._refresh_journal_log(log_tree)

        self.gui_root.mainloop()
    # --- Main Menu ---

    def business_setup(self):
        """Allows user to select a business type."""
        print("==================================================")
        print("Welcome, Bookkeeper, to the year 1955!")
        print("Your job is to manage the books for a thriving local business.")
        print("==================================================")
        print("Choose the type of business you will manage:")
        print("1: Sterling Consults (Service Business)")
        print("2: Gable's Groceries (Retail Business)")
        print("3: Thorne Fabrication (Manufacturing Business)")
        
        while True:
            choice = input("Enter your choice (1-3): ").strip()
            if choice == '1':
                self._setup_accounts("SERVICE")
                print(f"\nYou are hired by Mr. Sterling. Focus on tabulating services and receivables.")
                break
            elif choice == '2':
                self._setup_accounts("RETAIL")
                print(f"\nYou are hired by Mrs. Gable. Focus on inventory, sales, and vendor payments.")
                break
            elif choice == '3':
                self._setup_accounts("MANUFACTURING")
                print(f"\nYou are hired by Mr. Thorne. Focus on raw materials and production expenses.")
                break
            else:
                print("Invalid choice.")

        self._setup_ai_adapter()
        use_gui = input("Open the worksheet GUI? (y/N): ").strip().lower() == 'y'
        if use_gui:
            print("Launching GUI... close the window to quit.")
            self.launch_gui()
        else:
            self.main_menu()

    def main_menu(self):
        """The main interactive loop for the simulator."""
        print(f"\nGame Start: {self.current_date.strftime('%B %d, %Y')} ({self.business_type} Business)")
        
        while True:
            print("\n" + "=" * 30)
            print("MAIN MENU (The Bookkeeper's Desk)")
            print(f"Current Date: {self.current_date.strftime('%A, %B %d, %Y')}")
            print("=" * 30)
            print("1: View Trial Balance (The General Ledger)")
            print("2: View Subsidiary Ledgers (Check AR/AP Integrity)")
            print("3: START WORKDAY / Process Daily Transactions")
            print("4: View Income Statement (P&L Report)")
            print("5: View Balance Sheet (A=L+E Report)")
            print("6: Enter Custom Journal Entry (Manual Adjustment)")
            print("7: Exit Simulator")
            print("-" * 30)
            
            choice = input("Enter your choice (1-7): ").strip()

            if choice == '1':
                self.print_chart_of_accounts()
            elif choice == '2':
                self.print_subledgers()
            elif choice == '3':
                self.run_daily_scenario()
            elif choice == '4':
                self.print_income_statement()
            elif choice == '5':
                self.print_balance_sheet()
            elif choice == '6':
                # Call perform_journal_entry without an amount, maintaining original manual mode
                self.perform_journal_entry(total_transaction_amount=None) 
            elif choice == '7':
                print("\nThank you for simulating! The books are closed for the year.")
                break
            else:
                print("Invalid choice. Please enter a number from 1 to 7.")

# --- Execution ---
if __name__ == "__main__":
    simulator = AccountingSimulator()
    simulator.business_setup()
