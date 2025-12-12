import random
import sys
import re
from collections import defaultdict
from datetime import date, timedelta

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
        self.story_index = 0
        self.monthly_bills = self._load_monthly_bills()

        # Recurring bill tracker to prevent implausible repeats
        self.last_bill_months = {}

    # --- Initialization and Setup ---
    
    def _load_characters(self):
        """Defines the business owners for narrative flavor."""
        return {
            "SERVICE": {
                "name": "Mr. Sterling",
                "dialogue": "Mr. Sterling, the proprietor of Sterling Consults, nods: 'Ah, Bookkeeper, I've got a batch of invoices here that need tabulating. Keep that ledger pristine.'"
            },
            "RETAIL": {
                "name": "Mrs. Gable",
                "dialogue": "Mrs. Gable from Gable's Groceries beams: 'The market was busy this morning! Can you make sure these receipts and vendor slips get logged before the afternoon rush?'"
            },
            "MANUFACTURING": {
                "name": "Mr. Thorne",
                "dialogue": "Mr. Thorne, the owner of Thorne Fabrication, hands you a clip-board: 'We had a raw material delivery this morning. Get this noted, and check the payroll slips for the factory workers.'"
            }
        }

    def _load_story_beats(self):
        """Creates a simple serialized storyline for each business type."""
        return {
            "SERVICE": [
                "A new contract with the county courthouse is in the works; the clerks keep calling for invoice copies.",
                "Mr. Sterling mentions a rival firm opening nearby. He wants pristine books to woo nervous clients.",
                "An old radio in the office plays swing tunes as you tally hours; the mood eases during the rush.",
                "A junior consultant asks if expense reports can be summarized—you're the steadying hand in the chaos.",
                "Rumor has it a magazine is profiling local businesses. Sterling insists the ledgers shine."],
            "RETAIL": [
                "Mrs. Gable is prepping a mid-summer picnic display; vendors drop by with samples and gossip.",
                "A local family starts a tab for the week. You keep a careful eye on their receivable balance.",
                "Delivery boys race in with crates; the ringing cash register creates a lively soundtrack.",
                "A traveling salesman offers a discount on canned peaches, if you note the early payment terms.",
                "Mrs. Gable plans a harvest festival sale—she wants the books tidy before the posters go up."],
            "MANUFACTURING": [
                "Mr. Thorne lands a navy-adjacent contract and needs spotless records for inspectors.",
                "The factory whistle blows at dawn; you review payroll slips while the presses warm up.",
                "A visiting engineer asks about job costing—your ledgers guide the conversation.",
                "Steel shipments arrive by rail, and the foreman shouts for invoices before unloading.",
                "An efficiency expert strolls through the floor. Thorne wants every expense defended."],
        }

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
        print(f"[Interaction] Your boss, {self.business_owner['name']}, has arrived.")
        print(f"[Dialogue] {self.business_owner['dialogue']}")
        beat = self.story_beats[self.business_type][self.story_index % len(self.story_beats[self.business_type])]
        print(f"[Story Beat] {beat}")
        self.story_index += 1
        print("-" * 70)

        for i, (scenario, suggested_debit) in enumerate(scenarios_with_suggestions):
            
            # --- MODIFICATION: Extract Amount and Remove Hint ---
            transaction_amount = self._parse_amount_from_scenario(scenario)
            
            print(f"\nBUSINESS EVENT {i + 1}/{len(scenarios_with_suggestions)}: {scenario}")
            # Hint removed as requested
            print(f"Required Action: Enter the journal entry.")
            
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
        self.transactions.append(entry)

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
