import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import datetime
import json
import threading
import requests
import random
import time
import sys
import traceback
from dataclasses import dataclass, field
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


def log_exception_to_file(exc, val, tb, context: str = ""):
    """Persist stack traces so startup crashes are debuggable for users."""
    stack = "".join(traceback.format_exception(exc, val, tb))
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    context_note = f"[{context}] " if context else ""
    try:
        with open("simulator_error.log", "a", encoding="utf-8") as fh:
            fh.write(f"{stamp} {context_note}{stack}\n")
    except Exception:
        pass

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

class OllamaSettings:
    raw_url: str = OLLAMA_URL
    raw_health: str = OLLAMA_HEALTH
    model: str = OLLAMA_MODEL

    @classmethod
    def update(cls, url: str, health: str, model: str):
        cls.raw_url = (url or OLLAMA_URL).strip()
        cls.raw_health = (health or OLLAMA_HEALTH).strip()
        cls.model = model or OLLAMA_MODEL

    @classmethod
    def generate_endpoint(cls) -> str:
        return cls._normalize_endpoint(cls.raw_url, "generate")

    @classmethod
    def chat_endpoint(cls) -> str:
        return cls._normalize_endpoint(cls.raw_url, "chat")

    @classmethod
    def health_endpoint(cls) -> str:
        return cls._normalize_endpoint(cls.raw_health, "tags")

    @staticmethod
    def _normalize_endpoint(raw: str, suffix: str) -> str:
        """Accept either a base host or a full Ollama endpoint and return a usable URL."""
        cleaned = (raw or "").strip()

        if not cleaned:
            return f"http://localhost:11434/api/{suffix}"

        if not cleaned.startswith(("http://", "https://")):
            cleaned = "http://" + cleaned

        cleaned = cleaned.rstrip("/")

        if cleaned.endswith(f"/api/{suffix}"):
            return cleaned

        if cleaned.endswith("/api"):
            return f"{cleaned}/{suffix}"

        if cleaned.endswith(f"/{suffix}"):
            return f"{cleaned[:-len(suffix)-1]}/api/{suffix}"

        if "/api/" in cleaned:
            return cleaned

        return f"{cleaned}/api/{suffix}"


class AIHandler:
    _is_online: Optional[bool] = None
    last_error: Optional[str] = None
    last_endpoint: Optional[str] = None
    last_mode: Optional[str] = None  # "generate" or "chat"

    @classmethod
    def check_connection(cls) -> bool:
        """Try a minimal generate call so we only report online when chatting will work."""
        if cls._is_online is not None:
            return cls._is_online

        cls._probe_connectivity()
        return cls._is_online or False

    @classmethod
    def _probe_connectivity(cls):
        cls._is_online = False
        cls.last_endpoint = None
        cls.last_mode = None

        ping_prompt = "ping"
        if cls._try_generate(ping_prompt, system_role="You are a helpful assistant.", timeout=3):
            return
        cls._try_chat(ping_prompt, system_role="You are a helpful assistant.", timeout=3)

    @classmethod
    def _try_generate(cls, prompt: str, system_role: str, timeout: int = 5) -> bool:
        payload = {
            "model": OllamaSettings.model,
            "prompt": prompt,
            "stream": False,
        }
        try:
            resp = requests.post(OllamaSettings.generate_endpoint(), json=payload, timeout=timeout)
            resp.raise_for_status()
            try:
                data = resp.json()
            except ValueError as exc:
                raise requests.exceptions.RequestException(f"Invalid JSON from Ollama generate: {exc}") from exc
            if data.get("response") is None:
                raise requests.exceptions.RequestException("No response text returned from Ollama.")
            cls.last_error = None
            cls._is_online = True
            cls.last_endpoint = OllamaSettings.generate_endpoint()
            cls.last_mode = "generate"
            return True
        except (requests.exceptions.RequestException, Exception) as exc:
            cls.last_error = str(exc)
            cls._is_online = False
            return False

    @classmethod
    def _try_chat(cls, prompt: str, system_role: str, timeout: int = 5) -> bool:
        payload = {
            "model": OllamaSettings.model,
            "messages": [
                {"role": "system", "content": system_role},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }
        try:
            resp = requests.post(OllamaSettings.chat_endpoint(), json=payload, timeout=timeout)
            resp.raise_for_status()
            try:
                data = resp.json()
            except ValueError as exc:
                raise requests.exceptions.RequestException(f"Invalid JSON from Ollama chat: {exc}") from exc
            content = None
            if isinstance(data, dict):
                content = data.get("message", {}).get("content") or data.get("response")
            if not content:
                raise requests.exceptions.RequestException("No response text returned from Ollama chat.")
            cls.last_error = None
            cls._is_online = True
            cls.last_endpoint = OllamaSettings.chat_endpoint()
            cls.last_mode = "chat"
            return True
        except (requests.exceptions.RequestException, Exception) as exc:
            cls.last_error = str(exc)
            cls._is_online = False
            return False

    @classmethod
    def reset_status(cls):
        cls._is_online = None
        cls.last_error = None
        cls.last_endpoint = None
        cls.last_mode = None

    @staticmethod
    def generate_response(prompt, system_role="You are a helpful assistant."):
        """
        Connects to local Ollama instance. Falls back to mock if connection fails.
        """
        combined_prompt = prompt_with_system(prompt, system_role)

        # Prefer generate; fall back to chat if generate fails (e.g., due to endpoint choice)
        if AIHandler._try_generate(combined_prompt, system_role):
            # _try_generate already recorded state; fetch last response again for real message
            try:
                response = requests.post(
                    OllamaSettings.generate_endpoint(),
                    json={"model": OllamaSettings.model, "prompt": combined_prompt, "stream": False},
                    timeout=10,
                )
                response.raise_for_status()
                data = response.json()
                AIHandler.last_error = None
                return data.get("response", "Error parsing AI response.")
            except (requests.exceptions.RequestException, ValueError, Exception) as exc:
                AIHandler.last_error = str(exc)

        if AIHandler._try_chat(prompt, system_role):
            try:
                response = requests.post(
                    OllamaSettings.chat_endpoint(),
                    json={
                        "model": OllamaSettings.model,
                        "messages": [
                            {"role": "system", "content": system_role},
                            {"role": "user", "content": prompt},
                        ],
                        "stream": False,
                    },
                    timeout=10,
                )
                response.raise_for_status()
                data = response.json()
                AIHandler.last_error = None
                return (data.get("message", {}) or {}).get("content") or data.get("response", "Error parsing AI response.")
            except (requests.exceptions.RequestException, ValueError, Exception) as exc:
                AIHandler.last_error = str(exc)

        AIHandler._is_online = False
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


def prompt_with_system(user_prompt: str, system_role: str) -> str:
    """Combine system and user instructions into a single prompt for /generate."""
    return (
        f"System instructions: {system_role}\n"
        f"User message: {user_prompt}\n"
        "Assistant response:"
    )


@dataclass
class Invoice:
    number: str
    from_company: str
    to_company: str
    amount: float
    description: str
    due_date: str
    direction: str = "payable"  # payable or receivable
    status: str = "unposted"  # unposted, posted, paid, invoiced

    def as_message(self) -> str:
        return (
            f"[INVOICE {self.number}] From: {self.from_company} To: {self.to_company} "
            f"Amount: ${self.amount:,.2f} | Due: {self.due_date} | Details: {self.description}"
        )


class BusinessState:
    """Tracks the live state of the simulated business so the UI feels coherent."""

    def __init__(self, ledger: Ledger):
        self.ledger = ledger
        self.cash_balance: float = 5000.0
        self.activity_log: List[str] = []
        self.invoices: List[Invoice] = []

    def add_invoice(self, invoice: Invoice):
        self.invoices.append(invoice)
        self.activity_log.append(f"Logged invoice {invoice.number} ({invoice.direction}) for ${invoice.amount:,.2f}")

    def mark_posted(self, invoice: Invoice):
        invoice.status = "posted"
        self.activity_log.append(f"Posted {invoice.number} to ledger")

    def mark_paid(self, invoice: Invoice):
        invoice.status = "paid"
        delta = -invoice.amount if invoice.direction == "payable" else invoice.amount
        self.cash_balance += delta
        self.activity_log.append(f"Cash {'decrease' if delta < 0 else 'increase'} on {invoice.number}: ${abs(delta):,.2f}")

    def outstanding(self, direction: str):
        return [inv for inv in self.invoices if inv.direction == direction and inv.status != "paid"]

    def latest_activity(self, limit: int = 8) -> List[str]:
        return list(self.activity_log)[-limit:]

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
        try:
            x, y, _, _ = self.widget.bbox("insert")
            x += self.widget.winfo_rootx() + 25
            y += self.widget.winfo_rooty() + 25
        except tk.TclError:
            x = self.widget.winfo_pointerx() + 20
            y = self.widget.winfo_pointery() + 20
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
    def __init__(self, parent, controller, business_state: BusinessState):
        super().__init__(parent, bg=COLOR_PANEL)
        self.controller = controller
        self.business_state = business_state
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

        # Soft notification banner for unseen messages
        self.banner_var = tk.StringVar(value="")
        self.banner_label = tk.Label(self, textvariable=self.banner_var, bg=COLOR_PANEL, fg=COLOR_WARNING, font=FONT_MAIN)
        self.banner_label.pack(fill="x", padx=10)

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

    def refresh_ai_status(self):
        self.ai_status.config(text=self._ai_status_text())

    def _inject_initial_messages(self):
        self.receive_message("Boss", "Welcome to the team. Open the Academy app to learn the ropes.")
        self._deliver_invoice(Invoice("#1001", "Northwind Properties", "Your Company", 1200.00, "Office Rent", "Due this month", direction="payable"))

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
        self.banner_var.set("")

    def send_message(self, event=None):
        msg = self.msg_entry.get()
        if not msg: return
        
        self.msg_entry.delete(0, tk.END)
        self.chat_history[self.current_contact].append(("Me", msg))
        self._refresh_chat()

        # Thread the AI response so UI doesn't freeze
        threading.Thread(target=self._get_ai_reply, args=(self.current_contact, msg), daemon=True).start()

    def _get_ai_reply(self, contact, user_msg):
        system_role = (
            f"{self.contacts[contact]} Stay in character for this persona."
            " Keep replies concise (1-3 sentences) and professional,"
            " including invoice numbers, amounts, due dates, or next steps when relevant."
        )
        prompt = self._build_prompt(contact, user_msg)

        reply = AIHandler.generate_response(prompt, system_role)

        self.controller.after(0, lambda: self.receive_message(contact, reply))

    def _build_prompt(self, contact: str, user_msg: str) -> str:
        persona = self.contacts.get(contact, "You are a helpful assistant in a bookkeeping simulator.")
        style_rules = (
            "Respond as a short messenger chat. Keep messages brief (1-3 sentences),"
            " businesslike, and actionable. Mention key bookkeeping details"
            " such as invoice numbers, dates, totals, payment instructions,"
            " and what to log in the books whenever appropriate."
        )
        summary = self._business_context_summary()
        return (
            f"Contact persona: {persona}\n"
            f"Response style: {style_rules}\n"
            f"Business state summary: {summary}\n"
            f"Player message: {user_msg}\n"
            "Craft the reply now."
        )

    def _business_context_summary(self) -> str:
        payables = ", ".join(
            f"{inv.number} ${inv.amount:,.0f} due {inv.due_date}"
            for inv in self.business_state.outstanding("payable")
        ) or "no payables"
        receivables = ", ".join(
            f"{inv.number} ${inv.amount:,.0f} due {inv.due_date}"
            for inv in self.business_state.outstanding("receivable")
        ) or "no receivables"
        cash = f"cash on hand ${self.business_state.cash_balance:,.0f}"
        return f"{cash}; payables: {payables}; receivables: {receivables}"

    def receive_message(self, contact, message):
        self.chat_history[contact].append((contact, message))
        if self.current_contact == contact:
            self._refresh_chat()
        else:
            self.banner_var.set(f"New message from {contact}. Open their chat to view.")

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
                    direction="receivable",
                )
            except ValueError:
                messagebox.showerror("Invalid", "Amount must be numeric")
                return

            self.invoices.append(invoice)
            self.business_state.add_invoice(invoice)
            self.chat_history[self.current_contact].append(("Me", invoice.as_message()))
            self._refresh_chat()
            self.controller.after(0, self.controller.refresh_dashboard)
            dialog.destroy()

        tk.Button(dialog, text="Send", command=send, bg=COLOR_SUCCESS).grid(row=4, column=0, columnspan=2, pady=10, sticky="ew")

    def _deliver_invoice(self, invoice: Invoice):
        self.invoices.append(invoice)
        self.business_state.add_invoice(invoice)
        self.receive_message(invoice.from_company if invoice.from_company in self.contacts else "Supplier (TechParts)", invoice.as_message())
        self.controller.after(0, self.controller.refresh_dashboard)

    def _ai_status_text(self):
        try:
            online = AIHandler.check_connection()
            if online:
                endpoint = AIHandler.last_endpoint or OllamaSettings.generate_endpoint()
                mode = AIHandler.last_mode or "generate"
                return f"AI: Connected via {mode} at {endpoint}"
            suffix = f" (error: {AIHandler.last_error})" if AIHandler.last_error else ""
            return f"AI: Using mock replies; start Ollama and click Settings > Check Connection{suffix}."
        except Exception as exc:
            log_exception_to_file(type(exc), exc, exc.__traceback__, context="ai-status")
            return "AI: Offline (error while checking status)."

class AccountingApp(tk.Frame):
    def __init__(self, parent, ledger):
        super().__init__(parent, bg=COLOR_PANEL)
        self.ledger = ledger
        self._setup_ui()

    def _setup_ui(self):
        # Notebook for Tabs
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except tk.TclError:
            # Fall back gracefully if the theme is unavailable instead of crashing the app
            names = style.theme_names()
            fallback = names[0] if names else 'default'
            try:
                style.theme_use(fallback)
            except tk.TclError:
                pass
        
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
        header = tk.Label(self, text="SPREADSHEET WORKPAD", font=FONT_HEADER, bg=COLOR_PANEL, fg=COLOR_ACCENT)
        header.pack(pady=8)

        form = tk.Frame(self, bg=COLOR_PANEL)
        form.pack(fill="x", padx=10, pady=5)

        tk.Label(form, text="Description", bg=COLOR_PANEL, fg=COLOR_FG).grid(row=0, column=0, sticky="e")
        self.entry_desc = tk.Entry(form, width=40)
        self.entry_desc.insert(0, "Quick adjustment or batch entry")
        self.entry_desc.grid(row=0, column=1, columnspan=3, padx=5, pady=4, sticky="w")

        tk.Label(form, text="Account", bg=COLOR_PANEL, fg=COLOR_FG).grid(row=1, column=0, sticky="e")
        self.combo_account = ttk.Combobox(form, values=ChartOfAccounts.ALL_ACCOUNTS, width=28)
        self.combo_account.grid(row=1, column=1, padx=5, pady=4, sticky="w")

        tk.Label(form, text="Debit $", bg=COLOR_PANEL, fg=COLOR_FG).grid(row=1, column=2, sticky="e")
        self.entry_debit = tk.Entry(form, width=10)
        self.entry_debit.grid(row=1, column=3, padx=5, pady=4, sticky="w")

        tk.Label(form, text="Credit $", bg=COLOR_PANEL, fg=COLOR_FG).grid(row=1, column=4, sticky="e")
        self.entry_credit = tk.Entry(form, width=10)
        self.entry_credit.grid(row=1, column=5, padx=5, pady=4, sticky="w")

        tk.Button(form, text="Add Line", command=self._add_line, bg=COLOR_SUCCESS).grid(row=1, column=6, padx=5)
        tk.Button(form, text="Clear", command=self._clear_lines, bg=COLOR_WARNING).grid(row=1, column=7, padx=5)

        columns = ("Description", "Account", "Debit", "Credit")
        self.table = ttk.Treeview(self, columns=columns, show="headings", height=12)
        for col in columns:
            self.table.heading(col, text=col)
            self.table.column(col, width=180 if col == "Description" else 120)
        self.table.pack(fill="both", expand=True, padx=10, pady=5)

        tk.Button(self, text="Post to Ledger", command=self._post_batch, bg=COLOR_ACCENT).pack(pady=8)

        hint = ("Use the workpad to build multi-line journal entries. Enter one debit or credit per line; "
                "totals must balance before posting.")
        tk.Label(self, text=hint, wraplength=800, bg=COLOR_PANEL, fg=COLOR_FG, font=("Consolas", 9)).pack(pady=(0, 10))

    def _add_line(self):
        account = self.combo_account.get()
        desc = self.entry_desc.get() or "Spreadsheet entry"
        debit_txt = self.entry_debit.get().strip()
        credit_txt = self.entry_credit.get().strip()

        if not account:
            messagebox.showerror("Missing", "Choose an account before adding a line.")
            return

        try:
            debit = float(debit_txt) if debit_txt else 0.0
            credit = float(credit_txt) if credit_txt else 0.0
        except ValueError:
            messagebox.showerror("Invalid", "Debit/Credit must be numeric.")
            return

        if debit and credit:
            messagebox.showerror("Unbalanced", "Enter either a debit or credit amount, not both.")
            return
        if not debit and not credit:
            messagebox.showerror("Empty", "Provide a debit or credit amount.")
            return

        line = {"description": desc, "account": account, "debit": debit, "credit": credit}
        self.rows.append(line)
        self.table.insert("", tk.END, values=(desc, account, f"${debit:,.2f}" if debit else "", f"${credit:,.2f}" if credit else ""))
        self.combo_account.set("")
        self.entry_debit.delete(0, tk.END)
        self.entry_credit.delete(0, tk.END)

    def _clear_lines(self):
        self.rows.clear()
        for row in self.table.get_children():
            self.table.delete(row)

    def _post_batch(self):
        if not self.rows:
            messagebox.showwarning("No lines", "Add at least one line before posting.")
            return

        debits: Dict[str, float] = {}
        credits: Dict[str, float] = {}
        for line in self.rows:
            if line["debit"]:
                debits[line["account"]] = debits.get(line["account"], 0.0) + line["debit"]
            if line["credit"]:
                credits[line["account"]] = credits.get(line["account"], 0.0) + line["credit"]

        try:
            self.ledger.add_entry(
                datetime.date.today().strftime("%Y-%m-%d"),
                self.entry_desc.get() or "Spreadsheet batch",
                debits,
                credits,
            )
        except ValueError as exc:
            messagebox.showerror("Unbalanced", str(exc))
            return

        messagebox.showinfo("Posted", "Batch posted to the ledger.")
        self._clear_lines()


class DashboardApp(tk.Frame):
    def __init__(self, parent, business_state: BusinessState):
        super().__init__(parent, bg=COLOR_PANEL)
        self.business_state = business_state
        # Pre-initialize label references so refresh can safely run even if UI wiring fails early.
        self.lbl_cash: Optional[tk.Label] = None
        self.lbl_payables: Optional[tk.Label] = None
        self.lbl_receivables: Optional[tk.Label] = None
        self.table: Optional[ttk.Treeview] = None
        self.activity: Optional[scrolledtext.ScrolledText] = None
        try:
            self._setup_ui()
        except Exception as exc:
            log_exception_to_file(type(exc), exc, exc.__traceback__, context="dashboard-ui")
        self.refresh()

    def _setup_ui(self):
        header = tk.Label(self, text="OPERATIONS DASHBOARD", font=FONT_HEADER, bg=COLOR_PANEL, fg=COLOR_ACCENT)
        header.pack(pady=8)

        metrics = tk.Frame(self, bg=COLOR_PANEL)
        metrics.pack(fill="x", padx=10)

        self.lbl_cash = tk.Label(metrics, text="Cash: $0", bg=COLOR_PANEL, fg=COLOR_FG, font=FONT_HEADER)
        self.lbl_cash.pack(side="left", padx=10)
        self.lbl_payables = tk.Label(metrics, text="Payables: 0", bg=COLOR_PANEL, fg=COLOR_WARNING, font=FONT_HEADER)
        self.lbl_payables.pack(side="left", padx=10)
        self.lbl_receivables = tk.Label(metrics, text="Receivables: 0", bg=COLOR_PANEL, fg=COLOR_SUCCESS, font=FONT_HEADER)
        self.lbl_receivables.pack(side="left", padx=10)

        body = tk.Frame(self, bg=COLOR_PANEL)
        body.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(body, text="Invoice Inbox", bg=COLOR_PANEL, fg=COLOR_FG, font=FONT_MAIN).pack(anchor="w")
        columns = ("Number", "Direction", "Amount", "Due", "Status", "Description")
        self.table = ttk.Treeview(body, columns=columns, show="headings", height=10)
        for col in columns:
            self.table.heading(col, text=col)
            self.table.column(col, width=140)
        self.table.pack(fill="both", expand=True)

        btns = tk.Frame(body, bg=COLOR_PANEL)
        btns.pack(fill="x", pady=6)
        tk.Button(btns, text="Refresh", command=self.refresh, bg=COLOR_ACCENT).pack(side="left", padx=4)
        tk.Button(btns, text="Post to Ledger", command=self._post_selected, bg=COLOR_SUCCESS).pack(side="left", padx=4)
        tk.Button(btns, text="Mark Paid/Received", command=self._settle_selected, bg=COLOR_WARNING).pack(side="left", padx=4)
        tk.Button(btns, text="New Invoice/Bill", command=self._open_new_invoice, bg=COLOR_BG, fg=COLOR_FG).pack(side="left", padx=4)

        tk.Label(body, text="Recent Activity", bg=COLOR_PANEL, fg=COLOR_FG, font=FONT_MAIN).pack(anchor="w", pady=(10, 0))
        self.activity = scrolledtext.ScrolledText(body, height=6, bg=COLOR_BG, fg=COLOR_FG, font=FONT_MAIN)
        self.activity.pack(fill="x")
        self.activity.config(state="disabled")

    def _open_new_invoice(self):
        """Quick creation of a payable or receivable that feeds the dashboard and ledger posting flow."""
        dialog = tk.Toplevel(self)
        dialog.title("Create Invoice or Bill")
        dialog.configure(bg=COLOR_PANEL)

        tk.Label(dialog, text="Invoice #", bg=COLOR_PANEL, fg=COLOR_FG).grid(row=0, column=0, sticky="e", padx=5, pady=5)
        entry_num = tk.Entry(dialog)
        entry_num.grid(row=0, column=1, padx=5, pady=5)
        entry_num.insert(0, f"#{random.randint(3000, 9999)}")

        tk.Label(dialog, text="Direction", bg=COLOR_PANEL, fg=COLOR_FG).grid(row=1, column=0, sticky="e", padx=5, pady=5)
        direction_var = tk.StringVar(value="payable")
        ttk.Combobox(dialog, textvariable=direction_var, values=["payable", "receivable"], state="readonly").grid(row=1, column=1, padx=5, pady=5, sticky="w")

        tk.Label(dialog, text="Counterparty", bg=COLOR_PANEL, fg=COLOR_FG).grid(row=2, column=0, sticky="e", padx=5, pady=5)
        entry_party = tk.Entry(dialog)
        entry_party.grid(row=2, column=1, padx=5, pady=5)
        entry_party.insert(0, "Supplier/Customer")

        tk.Label(dialog, text="Amount", bg=COLOR_PANEL, fg=COLOR_FG).grid(row=3, column=0, sticky="e", padx=5, pady=5)
        entry_amt = tk.Entry(dialog)
        entry_amt.grid(row=3, column=1, padx=5, pady=5)

        tk.Label(dialog, text="Description", bg=COLOR_PANEL, fg=COLOR_FG).grid(row=4, column=0, sticky="e", padx=5, pady=5)
        entry_desc = tk.Entry(dialog, width=40)
        entry_desc.grid(row=4, column=1, padx=5, pady=5)
        entry_desc.insert(0, "What is this for?")

        tk.Label(dialog, text="Due Date", bg=COLOR_PANEL, fg=COLOR_FG).grid(row=5, column=0, sticky="e", padx=5, pady=5)
        entry_due = tk.Entry(dialog)
        entry_due.grid(row=5, column=1, padx=5, pady=5)
        entry_due.insert(0, (datetime.date.today() + datetime.timedelta(days=30)).isoformat())

        def save_invoice():
            try:
                amount_val = float(entry_amt.get())
            except ValueError:
                messagebox.showerror("Invalid", "Amount must be numeric")
                return

            direction = direction_var.get()
            counterparty = entry_party.get() or ("Vendor" if direction == "payable" else "Customer")
            if direction == "payable":
                frm, to = counterparty, "Your Company"
            else:
                frm, to = "Your Company", counterparty

            invoice = Invoice(
                number=entry_num.get() or f"#{random.randint(4000, 9999)}",
                from_company=frm,
                to_company=to,
                amount=amount_val,
                description=entry_desc.get() or "General",
                due_date=entry_due.get(),
                direction=direction,
            )

            self.business_state.add_invoice(invoice)
            self.refresh()
            dialog.destroy()

        tk.Button(dialog, text="Save", command=save_invoice, bg=COLOR_SUCCESS).grid(row=6, column=0, columnspan=2, sticky="ew", padx=5, pady=10)

    def refresh(self):
        if not all([self.lbl_cash, self.lbl_payables, self.lbl_receivables, self.table, self.activity]):
            # If the UI failed to initialize fully, avoid crashing the simulator.
            return

        self.lbl_cash.config(text=f"Cash: ${self.business_state.cash_balance:,.0f}")
        self.lbl_payables.config(text=f"Payables: {len(self.business_state.outstanding('payable'))}")
        self.lbl_receivables.config(text=f"Receivables: {len(self.business_state.outstanding('receivable'))}")

        for row in self.table.get_children():
            self.table.delete(row)
        for inv in self.business_state.invoices:
            self.table.insert("", tk.END, values=(
                inv.number,
                inv.direction,
                f"${inv.amount:,.2f}",
                inv.due_date,
                inv.status,
                inv.description,
            ))

        self.activity.config(state="normal")
        self.activity.delete(1.0, tk.END)
        for line in self.business_state.latest_activity():
            self.activity.insert(tk.END, f"• {line}\n")
        self.activity.config(state="disabled")

    def _get_selected_invoice(self) -> Optional[Invoice]:
        sel = self.table.selection()
        if not sel:
            return None
        number = self.table.item(sel[0], "values")[0]
        for inv in self.business_state.invoices:
            if inv.number == number:
                return inv
        return None

    def _post_selected(self):
        inv = self._get_selected_invoice()
        if not inv:
            messagebox.showwarning("No selection", "Select an invoice to post.")
            return
        if inv.status not in {"unposted", "invoiced"}:
            messagebox.showinfo("Already posted", f"{inv.number} is already {inv.status}.")
            return
        try:
            debit, credit = self._build_entry(inv)
            self.business_state.ledger.add_entry(
                datetime.date.today().isoformat(),
                f"Post {inv.number} - {inv.description}",
                debit,
                credit,
            )
            inv.status = "posted"
            self.business_state.mark_posted(inv)
        except ValueError as exc:
            messagebox.showerror("Unbalanced", str(exc))
        self.refresh()

    def _settle_selected(self):
        inv = self._get_selected_invoice()
        if not inv:
            messagebox.showwarning("No selection", "Select an invoice to settle.")
            return
        if inv.status == "paid":
            messagebox.showinfo("Already settled", f"{inv.number} is already paid/received.")
            return
        if inv.status == "unposted":
            self._post_selected()
            inv = self._get_selected_invoice()
            if not inv or inv.status == "unposted":
                return
        debit = {}
        credit = {}
        if inv.direction == "payable":
            debit["Accounts Payable"] = inv.amount
            credit["Cash"] = inv.amount
        else:
            debit["Cash"] = inv.amount
            credit["Accounts Receivable"] = inv.amount
        try:
            self.business_state.ledger.add_entry(
                datetime.date.today().isoformat(),
                f"Settle {inv.number}",
                debit,
                credit,
            )
            self.business_state.mark_paid(inv)
        except ValueError as exc:
            messagebox.showerror("Unbalanced", str(exc))
        self.refresh()

    def _build_entry(self, inv: Invoice):
        description = inv.description.lower()
        debit = {}
        credit = {}
        if inv.direction == "payable":
            debit[self._guess_expense_account(description)] = inv.amount
            credit["Accounts Payable"] = inv.amount
        else:
            debit["Accounts Receivable"] = inv.amount
            credit["Sales Revenue"] = inv.amount
        return debit, credit

    def _guess_expense_account(self, desc: str) -> str:
        if "rent" in desc:
            return "Rent Expense"
        if "wage" in desc or "payroll" in desc:
            return "Wages Expense"
        if "inventory" in desc or "parts" in desc or "equipment" in desc:
            return "Cost of Goods Sold"
        return "Office Supplies"


class SettingsApp(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=COLOR_PANEL)
        self.controller = controller
        self.status_var = tk.StringVar(value="Configure your Ollama endpoint and model.")
        self._setup_ui()

    def _setup_ui(self):
        header = tk.Label(self, text="SETTINGS", font=FONT_HEADER, bg=COLOR_PANEL, fg=COLOR_ACCENT)
        header.pack(pady=10)

        form = tk.Frame(self, bg=COLOR_PANEL)
        form.pack(pady=10, padx=20, fill="x")

        tk.Label(form, text="Ollama Generate URL", bg=COLOR_PANEL, fg=COLOR_FG).grid(row=0, column=0, sticky="e", pady=5, padx=5)
        self.entry_url = tk.Entry(form, width=50)
        self.entry_url.grid(row=0, column=1, sticky="w", pady=5, padx=5)

        tk.Label(form, text="Ollama Health URL", bg=COLOR_PANEL, fg=COLOR_FG).grid(row=1, column=0, sticky="e", pady=5, padx=5)
        self.entry_health = tk.Entry(form, width=50)
        self.entry_health.grid(row=1, column=1, sticky="w", pady=5, padx=5)

        tk.Label(form, text="Model Name", bg=COLOR_PANEL, fg=COLOR_FG).grid(row=2, column=0, sticky="e", pady=5, padx=5)
        self.entry_model = tk.Entry(form, width=25)
        self.entry_model.grid(row=2, column=1, sticky="w", pady=5, padx=5)

        self._sync_entries()

        button_bar = tk.Frame(self, bg=COLOR_PANEL)
        button_bar.pack(pady=10)

        tk.Button(button_bar, text="Save & Test", command=self._save_and_test, bg=COLOR_SUCCESS).pack(side="left", padx=5)
        tk.Button(button_bar, text="Check Connection", command=self._test_only, bg=COLOR_ACCENT).pack(side="left", padx=5)

        tk.Label(self, textvariable=self.status_var, bg=COLOR_PANEL, fg=COLOR_FG, wraplength=600, justify="left").pack(pady=10, padx=15, fill="x")

    def _save_and_test(self):
        OllamaSettings.update(self.entry_url.get(), self.entry_health.get(), self.entry_model.get())
        self._sync_entries()
        AIHandler.reset_status()
        self.controller.refresh_ai_status()
        self._run_connectivity_check(prefix="Saved. ")

    def _test_only(self):
        self._run_connectivity_check()

    def _run_connectivity_check(self, prefix: str = ""):
        def worker():
            AIHandler.reset_status()
            online = AIHandler.check_connection()
            endpoint = AIHandler.last_endpoint or OllamaSettings.generate_endpoint()
            mode = AIHandler.last_mode or "generate"
            if online:
                status = (
                    f"Connected to Ollama at {endpoint} using {mode} (from '{OllamaSettings.raw_url}')."
                )
            else:
                status = (
                    f"Could not reach Ollama at {endpoint}. Last error: {AIHandler.last_error or 'unknown'}."
                )
            self.after(0, lambda: self.status_var.set(prefix + status))
            if online:
                self.after(0, self.controller.refresh_ai_status)

        threading.Thread(target=worker, daemon=True).start()

    def _sync_entries(self):
        """Preserve user-entered endpoints without auto-modifying them."""
        for entry, value in (
            (self.entry_url, OllamaSettings.raw_url),
            (self.entry_health, OllamaSettings.raw_health),
            (self.entry_model, OllamaSettings.model),
        ):
            entry.delete(0, tk.END)
            entry.insert(0, value)

# ==========================================
# MAIN SIMULATOR (OS INTERFACE)
# ==========================================

class SimulatorOS(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PyBookkeeper OS v1.0")
        self.geometry("1100x700")
        self.configure(bg=COLOR_BG)

        # Prevent hard crashes by surfacing unexpected Tk errors in a dialog and console
        self.report_callback_exception = self._handle_callback_exception

        self.ledger = Ledger()
        self.business_state = BusinessState(self.ledger)
        
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

    def _handle_callback_exception(self, exc, val, tb):
        log_exception_to_file(exc, val, tb, context="tk-callback")
        print("\n=== Tk callback error ===\n", "".join(traceback.format_exception(exc, val, tb)))
        try:
            messagebox.showerror("Unexpected Error", "A background action failed. Check the console for details.")
        except tk.TclError:
            # If UI is already closing, avoid raising another exception
            pass

    def _init_apps(self):
        # We stack frames and just raise the one we want to see
        self.apps["Dashboard"] = DashboardApp(self.main_area, self.business_state)
        self.apps["Messenger"] = MessengerApp(self.main_area, self, self.business_state)
        self.apps["Accounting"] = AccountingApp(self.main_area, self.ledger)
        self.apps["Spreadsheet"] = SpreadsheetApp(self.main_area, self.ledger)
        self.apps["Academy"] = GuideApp(self.main_area)
        self.apps["Settings"] = SettingsApp(self.main_area, self)
        
        for app in self.apps.values():
            app.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.open_app("Dashboard")

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

    def refresh_ai_status(self):
        messenger = self.apps.get("Messenger")
        if messenger:
            messenger.refresh_ai_status()

    def refresh_dashboard(self):
        dash = self.apps.get("Dashboard")
        if dash:
            dash.refresh()

    def _random_event_trigger(self):
        """Simulates business events periodically"""
        try:
            events = [
                Invoice("#1002", "Landlord (Rent)", "Your Company", 1200.00, "Office rent - overdue", "Due in 7 days", direction="payable"),
                Invoice("#5478", "Supplier (TechParts)", "Your Company", 200.00, "Keyboard shipment", "Net 30", direction="payable"),
                ("Customer (BigCorp)", "We need an invoice for the consultation yesterday. $500."),
                ("Boss", "I just bought a new coffee machine for the office using the company card ($150). Log it."),
            ]

            if random.random() > 0.7:  # 30% chance every 10 seconds
                choice = random.choice(events)
                if isinstance(choice, Invoice):
                    self.apps["Messenger"]._deliver_invoice(choice)
                else:
                    contact, msg = choice
                    self.apps["Messenger"].receive_message(contact, msg)
            self.refresh_dashboard()
        except Exception:
            # Surface errors via Tk's global handler; don't stop the scheduler
            self.report_callback_exception(*sys.exc_info())
        finally:
            # Reschedule regardless of success
            self.after(10000, self._random_event_trigger)

if __name__ == "__main__":
    try:
        app = SimulatorOS()
        app.mainloop()
    except Exception as exc:
        log_exception_to_file(type(exc), exc, exc.__traceback__, context="startup")
        print("\nSimulator failed to start. See simulator_error.log for details.\n")
        try:
            messagebox.showerror("Startup Failed", "The simulator could not start. Check simulator_error.log for details.")
        except tk.TclError:
            pass
