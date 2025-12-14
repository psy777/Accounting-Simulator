import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import datetime
import json
import threading
import requests
import random
import time
from dataclasses import dataclass
from typing import List, Dict, Optional

# ==========================================
# CONFIGURATION & CONSTANTS
# ==========================================
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_HEALTH = "http://localhost:11434/api/tags"
OLLAMA_MODEL = "llama3"  # Change to your installed model (e.g., 'mistral', 'llama2')

FONT_MAIN = ("Consolas", 10)
FONT_HEADER = ("Consolas", 12, "bold")
COLOR_BG = "#2E3440"
COLOR_FG = "#D8DEE9"
COLOR_ACCENT = "#88C0D0"
COLOR_SUCCESS = "#A3BE8C"
COLOR_WARNING = "#EBCB8B"
COLOR_ERROR = "#BF616A"
COLOR_PANEL = "#3B4252"

# ==========================================
# BACKEND: ACCOUNTING LOGIC
# ==========================================

class ChartOfAccounts:
    ASSETS = ["Cash", "Accounts Receivable", "Inventory", "Equipment"]
    LIABILITIES = ["Accounts Payable", "Notes Payable", "Taxes Payable"]
    EQUITY = ["Owner's Equity", "Retained Earnings"]
    REVENUE = ["Sales Revenue", "Service Revenue"]
    EXPENSES = ["Rent Expense", "Utilities Expense", "Cost of Goods Sold", "Wages Expense", "Office Supplies"]

    ALL_ACCOUNTS = ASSETS + LIABILITIES + EQUITY + REVENUE + EXPENSES

@dataclass
class JournalEntry:
    id: int
    date: str
    description: str
    debits: Dict[str, float]  # Account: Amount
    credits: Dict[str, float] # Account: Amount

class Ledger:
    def __init__(self):
        self.entries: List[JournalEntry] = []
        self.entry_counter = 1

    def reset(self):
        """Reset the ledger to a clean state (used for tutorial/demo)."""
        self.entries.clear()
        self.entry_counter = 1

    def add_entry(self, date, description, debits, credits):
        # Validate Double Entry
        total_debit = sum(debits.values())
        total_credit = sum(credits.values())
        
        if abs(total_debit - total_credit) > 0.01:
            raise ValueError(f"Unbalanced Entry! Debits: ${total_debit:.2f}, Credits: ${total_credit:.2f}")

        entry = JournalEntry(self.entry_counter, date, description, debits, credits)
        self.entries.append(entry)
        self.entry_counter += 1
        return entry

    def get_balances(self):
        balances = {acc: 0.0 for acc in ChartOfAccounts.ALL_ACCOUNTS}
        for entry in self.entries:
            for acc, amount in entry.debits.items():
                if acc in ChartOfAccounts.ASSETS or acc in ChartOfAccounts.EXPENSES:
                    balances[acc] += amount
                else:
                    balances[acc] -= amount # Contra for normal credit accounts
            
            for acc, amount in entry.credits.items():
                if acc in ChartOfAccounts.ASSETS or acc in ChartOfAccounts.EXPENSES:
                    balances[acc] -= amount
                else:
                    balances[acc] += amount
        return balances

# ==========================================
# BACKEND: OLLAMA / AI INTEGRATION
# ==========================================

class AIHandler:
    _is_online: Optional[bool] = None

    @classmethod
    def check_connection(cls) -> bool:
        """Ping the Ollama tags endpoint to confirm availability."""
        if cls._is_online is not None:
            return cls._is_online

        try:
            resp = requests.get(OLLAMA_HEALTH, timeout=2)
            resp.raise_for_status()
            cls._is_online = True
        except requests.exceptions.RequestException:
            cls._is_online = False
        return cls._is_online

    @staticmethod
    def generate_response(prompt, system_role="You are a helpful assistant."):
        """
        Connects to local Ollama instance. Falls back to mock if connection fails.
        """
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "system": system_role,
            "stream": False
        }
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=5)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "Error parsing AI response.")
        except requests.exceptions.RequestException:
            return AIHandler._mock_response(prompt, system_role)

    @staticmethod
    def _mock_response(prompt, role):
        # Fallback if user doesn't have Ollama
        if "Invoice" in prompt:
            return "Thanks for the invoice. I'll process it shortly."
        elif "Boss" in role:
            return "Good work. Keep the books balanced."
        else:
            return "I received your message."


@dataclass
class Invoice:
    number: str
    from_company: str
    to_company: str
    amount: float
    description: str
    due_date: str

    def as_message(self) -> str:
        return (
            f"[INVOICE {self.number}] From: {self.from_company} To: {self.to_company} "
            f"Amount: ${self.amount:,.2f} | Due: {self.due_date} | Details: {self.description}"
        )

# ==========================================
# GUI: COMPONENTS & APPS
# ==========================================

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip, text=self.text, background="yellow", relief='solid', borderwidth=1, font=("Arial", "8"))
        label.pack()

    def leave(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()

class DocumentViewer(tk.Toplevel):
    def __init__(self, parent, doc_title, doc_content):
        super().__init__(parent)
        self.title(doc_title)
        self.geometry("400x500")
        self.configure(bg="white")
        
        lbl_title = tk.Label(self, text=doc_title.upper(), font=("Helvetica", 16, "bold"), bg="white", fg="black")
        lbl_title.pack(pady=20)
        
        txt_content = tk.Label(self, text=doc_content, justify="left", font=("Courier", 10), bg="white", fg="black", padx=20)
        txt_content.pack(fill="both", expand=True)
        
        tk.Button(self, text="Close", command=self.destroy).pack(pady=10)

class MessengerApp(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_PANEL)
        self.controller = controller
        self.contacts = {
            "Boss": "You are the Boss of a small business. You are demanding but fair. You rely on the bookkeeper.",
            "Landlord (Rent)": "You are a landlord asking for rent payment.",
            "Supplier (TechParts)": "You are a tech supplier sending invoices for parts.",
            "Customer (BigCorp)": "You are a client who just received a service."
        }
        self.current_contact = "Boss"
        self.chat_history = {k: [] for k in self.contacts}
        self.invoices: List[Invoice] = []

        self._setup_ui()
        self._inject_initial_messages()

    def _setup_ui(self):
        # Sidebar for contacts
        self.sidebar = tk.Frame(self, bg=COLOR_BG, width=150)
        self.sidebar.pack(side="left", fill="y")

        lbl_contacts = tk.Label(self.sidebar, text="CONTACTS", bg=COLOR_BG, fg=COLOR_ACCENT, font=FONT_HEADER)
        lbl_contacts.pack(pady=10)

        for contact in self.contacts:
            btn = tk.Button(self.sidebar, text=contact, bg=COLOR_PANEL, fg=COLOR_FG, relief="flat",
                            command=lambda c=contact: self.switch_contact(c))
            btn.pack(fill="x", padx=5, pady=2)

        # Chat Area
        self.chat_area = scrolledtext.ScrolledText(self, state="disabled", bg=COLOR_PANEL, fg=COLOR_FG, font=FONT_MAIN)
        self.chat_area.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        # Input Area
        input_frame = tk.Frame(self, bg=COLOR_PANEL)
        input_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        
        self.msg_entry = tk.Entry(input_frame, bg="white", fg="black", font=FONT_MAIN)
        self.msg_entry.pack(side="left", fill="x", expand=True)
        self.msg_entry.bind("<Return>", self.send_message)

        btn_send = tk.Button(input_frame, text="Send", command=self.send_message, bg=COLOR_ACCENT, fg="black")
        btn_send.pack(side="right", padx=5)

        btn_invoice = tk.Button(input_frame, text="Send Invoice", command=self.compose_invoice, bg=COLOR_SUCCESS)
        btn_invoice.pack(side="right", padx=5)

        self.ai_status = tk.Label(self.sidebar, text=self._ai_status_text(), bg=COLOR_BG, fg=COLOR_FG, wraplength=120)
        self.ai_status.pack(pady=5, padx=5)

    def _inject_initial_messages(self):
        self.receive_message("Boss", "Welcome to the team. Open the Academy app to learn the ropes.")
        self._deliver_invoice(Invoice("#1001", "Northwind Properties", "Your Company", 1200.00, "Office Rent", "Due this month"))

    def switch_contact(self, contact):
        self.current_contact = contact
        self._refresh_chat()

    def _refresh_chat(self):
        self.chat_area.config(state="normal")
        self.chat_area.delete(1.0, tk.END)
        for sender, msg in self.chat_history[self.current_contact]:
            tag = "me" if sender == "Me" else "them"
            self.chat_area.insert(tk.END, f"{sender}: {msg}\n\n", tag)
        self.chat_area.config(state="disabled")
        self.chat_area.yview(tk.END)

    def send_message(self, event=None):
        msg = self.msg_entry.get()
        if not msg: return
        
        self.msg_entry.delete(0, tk.END)
        self.chat_history[self.current_contact].append(("Me", msg))
        self._refresh_chat()

        # Thread the AI response so UI doesn't freeze
        threading.Thread(target=self._get_ai_reply, args=(self.current_contact, msg)).start()

    def _get_ai_reply(self, contact, user_msg):
        system_role = self.contacts[contact]
        prompt = f"User said: '{user_msg}'. Reply in character, keep it under 2 sentences."
        
        reply = AIHandler.generate_response(prompt, system_role)
        
        self.controller.after(0, lambda: self.receive_message(contact, reply))

    def receive_message(self, contact, message):
        self.chat_history[contact].append((contact, message))
        if self.current_contact == contact:
            self._refresh_chat()
        else:
            messagebox.showinfo("New Message", f"New message from {contact}")

    def compose_invoice(self):
        """Create and send a structured invoice to the current contact."""
        dialog = tk.Toplevel(self)
        dialog.title("Send Invoice")
        dialog.configure(bg=COLOR_PANEL)

        tk.Label(dialog, text="Invoice #", bg=COLOR_PANEL, fg=COLOR_FG).grid(row=0, column=0, padx=5, pady=5, sticky="e")
        entry_num = tk.Entry(dialog)
        entry_num.grid(row=0, column=1, padx=5, pady=5)
        entry_num.insert(0, f"#{random.randint(2000, 9999)}")

        tk.Label(dialog, text="Amount", bg=COLOR_PANEL, fg=COLOR_FG).grid(row=1, column=0, padx=5, pady=5, sticky="e")
        entry_amt = tk.Entry(dialog)
        entry_amt.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(dialog, text="Description", bg=COLOR_PANEL, fg=COLOR_FG).grid(row=2, column=0, padx=5, pady=5, sticky="e")
        entry_desc = tk.Entry(dialog, width=40)
        entry_desc.grid(row=2, column=1, padx=5, pady=5)

        tk.Label(dialog, text="Due Date", bg=COLOR_PANEL, fg=COLOR_FG).grid(row=3, column=0, padx=5, pady=5, sticky="e")
        entry_due = tk.Entry(dialog)
        entry_due.grid(row=3, column=1, padx=5, pady=5)
        entry_due.insert(0, (datetime.date.today() + datetime.timedelta(days=30)).isoformat())

        def send():
            try:
                invoice = Invoice(
                    number=entry_num.get(),
                    from_company="Your Company",
                    to_company=self.current_contact,
                    amount=float(entry_amt.get()),
                    description=entry_desc.get() or "Services rendered",
                    due_date=entry_due.get(),
                )
            except ValueError:
                messagebox.showerror("Invalid", "Amount must be numeric")
                return

            self.invoices.append(invoice)
            self.chat_history[self.current_contact].append(("Me", invoice.as_message()))
            self._refresh_chat()
            dialog.destroy()

        tk.Button(dialog, text="Send", command=send, bg=COLOR_SUCCESS).grid(row=4, column=0, columnspan=2, pady=10, sticky="ew")

    def _deliver_invoice(self, invoice: Invoice):
        self.invoices.append(invoice)
        self.receive_message(invoice.from_company if invoice.from_company in self.contacts else "Supplier (TechParts)", invoice.as_message())

    def _ai_status_text(self):
        online = AIHandler.check_connection()
        if online:
            return "AI: Connected to Ollama"
        return "AI: Using mock replies (start Ollama at localhost:11434 for full experience)."

class AccountingApp(tk.Frame):
    def __init__(self, parent, ledger):
        super().__init__(parent, bg=COLOR_PANEL)
        self.ledger = ledger
        self._setup_ui()

    def _setup_ui(self):
        # Notebook for Tabs
        style = ttk.Style()
        style.theme_use('clam')
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.tab_journal = tk.Frame(self.notebook, bg=COLOR_PANEL)
        self.tab_ledger = tk.Frame(self.notebook, bg=COLOR_PANEL)
        self.tab_reports = tk.Frame(self.notebook, bg=COLOR_PANEL)

        self.notebook.add(self.tab_journal, text="Journal Entry")
        self.notebook.add(self.tab_ledger, text="General Ledger")
        self.notebook.add(self.tab_reports, text="Financial Reports")

        self._build_journal_tab()
        self._build_ledger_tab()
        self._build_reports_tab()

    def _build_journal_tab(self):
        frame = tk.Frame(self.tab_journal, bg=COLOR_PANEL)
        frame.pack(padx=20, pady=20)

        tk.Label(frame, text="Description:", bg=COLOR_PANEL, fg=COLOR_FG).grid(row=0, column=0, sticky="w")
        self.entry_desc = tk.Entry(frame, width=40)
        self.entry_desc.grid(row=0, column=1, columnspan=3, pady=5)

        # Debit Line
        tk.Label(frame, text="Debit Account:", bg=COLOR_PANEL, fg=COLOR_FG).grid(row=1, column=0, sticky="w")
        self.combo_dr = ttk.Combobox(frame, values=ChartOfAccounts.ALL_ACCOUNTS)
        self.combo_dr.grid(row=1, column=1, padx=5)
        tk.Label(frame, text="Amount $:", bg=COLOR_PANEL, fg=COLOR_FG).grid(row=1, column=2)
        self.entry_dr_amt = tk.Entry(frame, width=10)
        self.entry_dr_amt.grid(row=1, column=3)

        # Credit Line
        tk.Label(frame, text="Credit Account:", bg=COLOR_PANEL, fg=COLOR_FG).grid(row=2, column=0, sticky="w")
        self.combo_cr = ttk.Combobox(frame, values=ChartOfAccounts.ALL_ACCOUNTS)
        self.combo_cr.grid(row=2, column=1, padx=5)
        tk.Label(frame, text="Amount $:", bg=COLOR_PANEL, fg=COLOR_FG).grid(row=2, column=2)
        self.entry_cr_amt = tk.Entry(frame, width=10)
        self.entry_cr_amt.grid(row=2, column=3)

        btn_post = tk.Button(frame, text="POST ENTRY", bg=COLOR_SUCCESS, command=self.post_entry)
        btn_post.grid(row=3, column=0, columnspan=4, pady=20, sticky="ew")

    def post_entry(self):
        try:
            desc = self.entry_desc.get()
            dr_acc = self.combo_dr.get()
            cr_acc = self.combo_cr.get()
            dr_amt = float(self.entry_dr_amt.get())
            cr_amt = float(self.entry_cr_amt.get())
            
            if not desc or not dr_acc or not cr_acc:
                raise ValueError("All fields required.")

            self.ledger.add_entry(
                datetime.date.today().strftime("%Y-%m-%d"),
                desc,
                {dr_acc: dr_amt},
                {cr_acc: cr_amt}
            )
            
            messagebox.showinfo("Success", "Journal Entry Posted!")
            self._refresh_ledger_display()
            self._refresh_reports()
            
            # Clear fields
            self.entry_desc.delete(0, tk.END)
            self.entry_dr_amt.delete(0, tk.END)
            self.entry_cr_amt.delete(0, tk.END)

        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def _build_ledger_tab(self):
        self.ledger_text = scrolledtext.ScrolledText(self.tab_ledger, width=80, height=20, font=("Consolas", 9))
        self.ledger_text.pack(fill="both", expand=True, padx=10, pady=10)

    def _refresh_ledger_display(self):
        self.ledger_text.delete(1.0, tk.END)
        header = f"{'ID':<5} {'DATE':<12} {'DESCRIPTION':<30} {'ACCOUNT':<20} {'DEBIT':<10} {'CREDIT':<10}\n"
        self.ledger_text.insert(tk.END, header)
        self.ledger_text.insert(tk.END, "-"*90 + "\n")

        for entry in self.ledger.entries:
            # Print Debit line
            for acc, amt in entry.debits.items():
                line = f"{entry.id:<5} {entry.date:<12} {entry.description:<30} {acc:<20} {amt:<10.2f} {'':<10}\n"
                self.ledger_text.insert(tk.END, line)
            # Print Credit line
            for acc, amt in entry.credits.items():
                self.ledger_text.insert(tk.END, f"{'':<5} {'':<12} {'':<30} {acc:<20} {'':<10} {amt:<10.2f}\n")
            self.ledger_text.insert(tk.END, "\n")

    def _build_reports_tab(self):
        self.reports_text = scrolledtext.ScrolledText(self.tab_reports, font=("Consolas", 10))
        self.reports_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        btn_refresh = tk.Button(self.tab_reports, text="Refresh Reports", command=self._refresh_reports)
        btn_refresh.pack(pady=5)

    def _refresh_reports(self):
        balances = self.ledger.get_balances()
        
        # P&L
        revenue = sum(balances[a] for a in ChartOfAccounts.REVENUE)
        expenses = sum(balances[a] for a in ChartOfAccounts.EXPENSES)
        net_income = revenue - expenses
        
        # Balance Sheet
        assets = sum(balances[a] for a in ChartOfAccounts.ASSETS)
        liabilities = sum(balances[a] for a in ChartOfAccounts.LIABILITIES)
        equity = sum(balances[a] for a in ChartOfAccounts.EQUITY) + net_income # Add NI to equity

        report = "=== PROFIT & LOSS STATEMENT ===\n"
        report += f"Total Revenue:   ${revenue:,.2f}\n"
        report += f"Total Expenses:  ${expenses:,.2f}\n"
        report += f"NET INCOME:      ${net_income:,.2f}\n\n"
        
        report += "=== BALANCE SHEET ===\n"
        report += f"Total Assets:       ${assets:,.2f}\n"
        report += f"Total Liabilities:  ${liabilities:,.2f}\n"
        report += f"Total Equity:       ${equity:,.2f}\n"
        report += f"Check (A = L + E):  {assets == (liabilities + equity)}\n"

        self.reports_text.delete(1.0, tk.END)
        self.reports_text.insert(tk.END, report)


class GuideApp(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=COLOR_PANEL)
        
        lbl = tk.Label(self, text="ACCOUNTING ACADEMY", font=FONT_HEADER, bg=COLOR_PANEL, fg=COLOR_ACCENT)
        lbl.pack(pady=10)
        
        text_area = scrolledtext.ScrolledText(self, font=FONT_MAIN, bg=COLOR_PANEL, fg=COLOR_FG)
        text_area.pack(fill="both", expand=True, padx=10, pady=10)
        
        tutorial = """
        WELCOME TO THE BOOKKEEPING SIMULATOR
        ====================================

        CORE CONCEPTS:
        1. Double-Entry Accounting:
           Every transaction affects at least two accounts.
           DEBITS must always equal CREDITS.

        2. The Accounting Equation:
           Assets = Liabilities + Owner's Equity

        CHEAT SHEET:
        - ASSETS (Cash, Inventory):     Increase with DEBIT, Decrease with CREDIT
        - EXPENSES (Rent, Wages):       Increase with DEBIT, Decrease with CREDIT
        - LIABILITIES (Payables):       Increase with CREDIT, Decrease with DEBIT
        - REVENUE (Sales):              Increase with CREDIT, Decrease with DEBIT
        - EQUITY:                       Increase with CREDIT, Decrease with DEBIT

        CHART OF ACCOUNTS WALKTHROUGH:
        Assets -> what the business owns (cash, receivables, inventory, equipment)
        Liabilities -> what the business owes (accounts payable, taxes, notes)
        Equity -> owner's stake (capital, retained earnings)
        Revenue -> sales or service income
        Expenses -> costs to operate (rent, wages, supplies)

        MONTH-END CHECKLIST:
        - Reconcile bank/cash balances.
        - Post all invoices and bills.
        - Run Profit & Loss and Balance Sheet.
        - Prepare Accounts Receivable/Payable aging.
        - Close the books and roll retained earnings.

        SCENARIOS (PRACTICE ENTRIES):

        A) Received a Bill for Rent ($1000)?
           -> Expense (Rent) and Liability (Accounts Payable).
           ENTRY:
           Debit: Rent Expense     $1000
           Credit: Accounts Payable $1000

        B) Paid the Bill?
           -> You lose Cash (Asset) and remove the Liability.
           ENTRY:
           Debit: Accounts Payable $1000
           Credit: Cash             $1000

        C) Sent an Invoice to a customer?
           -> You earned Revenue, but haven't got cash yet (Accounts Receivable).
           ENTRY:
           Debit: Accounts Receivable
           Credit: Sales Revenue

        D) Monthly financial statements:
           Profit & Loss (performance), Balance Sheet (position),
           and optionally Cash Flow (liquidity). Run them after posting all
           journal entries and adjusting inventory/depreciation as needed.
        """
        text_area.insert(tk.END, tutorial)
        text_area.config(state="disabled")


class SpreadsheetApp(tk.Frame):
    def __init__(self, parent, ledger: Ledger):
        super().__init__(parent, bg=COLOR_PANEL)
        self.ledger = ledger
        self.rows: List[Dict[str, str]] = []
        self._setup_ui()

    def _setup_ui(self):
        header = tk.Label(self, text="SPREADSHEET (Trial Balance Sandbox)", font=FONT_HEADER, bg=COLOR_PANEL, fg=COLOR_ACCENT)
        header.pack(pady=8)

        toolbar = tk.Frame(self, bg=COLOR_PANEL)
        toolbar.pack(fill="x", padx=10)

        tk.Button(toolbar, text="Add Row", command=self._open_add_row, bg=COLOR_ACCENT).pack(side="left", padx=5)
        tk.Button(toolbar, text="Load From Ledger", command=self._load_from_ledger, bg=COLOR_SUCCESS).pack(side="left", padx=5)
        tk.Button(toolbar, text="Clear", command=self._clear_rows, bg=COLOR_ERROR, fg="white").pack(side="left", padx=5)

        columns = ("Period", "Account", "Debit", "Credit", "Notes")
        self.table = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns:
            self.table.heading(col, text=col)
            self.table.column(col, width=140)
        self.table.pack(fill="both", expand=True, padx=10, pady=10)

        tip = "Use this sheet to rehearse entries or build monthly statements."
        ToolTip(self.table, tip)

    def _open_add_row(self):
        dialog = tk.Toplevel(self)
        dialog.title("Add Spreadsheet Row")
        dialog.configure(bg=COLOR_PANEL)

        labels = ["Period (YYYY-MM)", "Account", "Debit", "Credit", "Notes"]
        entries = []
        for i, text in enumerate(labels):
            tk.Label(dialog, text=text, bg=COLOR_PANEL, fg=COLOR_FG).grid(row=i, column=0, padx=5, pady=5, sticky="e")
            ent = tk.Entry(dialog)
            ent.grid(row=i, column=1, padx=5, pady=5)
            entries.append(ent)

        entries[0].insert(0, datetime.date.today().strftime("%Y-%m"))

        def add():
            period, account, debit, credit, notes = [e.get() for e in entries]
            self.rows.append({"Period": period, "Account": account, "Debit": debit, "Credit": credit, "Notes": notes})
            self.table.insert("", tk.END, values=(period, account, debit, credit, notes))
            dialog.destroy()

        tk.Button(dialog, text="Insert", command=add, bg=COLOR_SUCCESS).grid(row=len(labels), column=0, columnspan=2, pady=10, sticky="ew")

    def _load_from_ledger(self):
        self._clear_rows()
        balances = self.ledger.get_balances()
        period = datetime.date.today().strftime("%Y-%m")
        for account, amount in balances.items():
            if abs(amount) < 0.01:
                continue
            debit = amount if amount > 0 else ""
            credit = abs(amount) if amount < 0 else ""
            self.rows.append({"Period": period, "Account": account, "Debit": debit, "Credit": credit, "Notes": "From ledger"})
            self.table.insert("", tk.END, values=(period, account, debit, credit, "From ledger"))

    def _clear_rows(self):
        for row in self.table.get_children():
            self.table.delete(row)
        self.rows.clear()

# ==========================================
# MAIN SIMULATOR (OS INTERFACE)
# ==========================================

class SimulatorOS(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PyBookkeeper OS v1.0")
        self.geometry("1100x700")
        self.configure(bg=COLOR_BG)
        
        self.ledger = Ledger()
        
        # Main Layout: Sidebar (Launcher) + Main Area
        self.sidebar = tk.Frame(self, bg="#2E3440", width=80)
        self.sidebar.pack(side="left", fill="y")
        
        self.main_area = tk.Frame(self, bg=COLOR_BG)
        self.main_area.pack(side="right", fill="both", expand=True)
        
        self.apps = {}
        
        # Initialize Apps
        self._init_apps()
        self._create_sidebar_buttons()
        
        # Start Message Simulation Loop
        self.after(10000, self._random_event_trigger)

    def _init_apps(self):
        # We stack frames and just raise the one we want to see
        self.apps["Messenger"] = MessengerApp(self.main_area, self)
        self.apps["Accounting"] = AccountingApp(self.main_area, self.ledger)
        self.apps["Spreadsheet"] = SpreadsheetApp(self.main_area, self.ledger)
        self.apps["Academy"] = GuideApp(self.main_area)
        
        for app in self.apps.values():
            app.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        self.open_app("Messenger")

    def _create_sidebar_buttons(self):
        # Create launcher buttons
        for app_name in self.apps.keys():
            btn = tk.Button(self.sidebar, text=app_name, 
                            bg=COLOR_ACCENT, fg="black", font=("Arial", 9, "bold"),
                            width=10, height=2,
                            command=lambda n=app_name: self.open_app(n))
            btn.pack(pady=10, padx=5)
            
        # Exit Button
        btn_exit = tk.Button(self.sidebar, text="SHUTDOWN", bg=COLOR_ERROR, fg="white",
                             command=self.destroy)
        btn_exit.pack(side="bottom", pady=20)

    def open_app(self, app_name):
        self.apps[app_name].tkraise()

    def _random_event_trigger(self):
        """Simulates business events periodically"""
        events = [
            Invoice("#1002", "Landlord (Rent)", "Your Company", 1200.00, "Office rent - overdue", "Due in 7 days"),
            Invoice("#5478", "Supplier (TechParts)", "Your Company", 200.00, "Keyboard shipment", "Net 30"),
            ("Customer (BigCorp)", "We need an invoice for the consultation yesterday. $500."),
            ("Boss", "I just bought a new coffee machine for the office using the company card ($150). Log it.")
        ]

        if random.random() > 0.7: # 30% chance every 10 seconds
            choice = random.choice(events)
            if isinstance(choice, Invoice):
                self.apps["Messenger"]._deliver_invoice(choice)
            else:
                contact, msg = choice
                self.apps["Messenger"].receive_message(contact, msg)
            
        # Reschedule
        self.after(10000, self._random_event_trigger)

if __name__ == "__main__":
    app = SimulatorOS()
    app.mainloop()
