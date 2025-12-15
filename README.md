# Double-Entry Bookkeeping Simulator

A modern React application built with Vite and Material-UI that simulates double-entry bookkeeping principles. This educational tool helps users understand the fundamentals of accounting through an interactive, user-friendly interface.

## Features

- **Add Journal Entries**: Create double-entry transactions with date, description, debit account, credit account, and amount
- **View Journal Entries**: Display all transactions in a sortable table format
- **T-Accounts View**: Visualize individual account transactions in traditional T-account layout with running balances
- **Balance Summary**: Review account balances organized by type (Assets, Liabilities, Equity, Revenue, Expenses)
- **Account Management**: Create, edit, and delete accounts with validation and usage tracking
- **Local Storage**: All data persists in the browser's local storage
- **Dark Theme**: Modern, professional dark-themed UI using Material-UI

## Getting Started

### Prerequisites

- Node.js (v16 or higher)
- npm

### Installation

1. Clone or download this project
2. Navigate to the project directory:
   ```bash
   cd DoubleEntryProgram
   ```

3. Install dependencies:
   ```bash
   npm install
   ```

4. Start the development server:
   ```bash
   npm run dev
   ```

5. Open your browser and navigate to `http://localhost:5173`

## Project Structure

```
DoubleEntryProgram/
├── src/
│   ├── components/
│   │   ├── JournalEntryForm.jsx      # Form for adding new journal entries
│   │   ├── JournalEntriesTable.jsx   # Table view of all journal entries
│   │   ├── TAccountsView.jsx         # T-account visualization
│   │   ├── BalanceSummary.jsx        # Account balance summary
│   │   └── AccountManagement.jsx     # Create, edit, and manage accounts
│   ├── data/
│   │   └── accounts.js               # Chart of accounts and data utilities
│   ├── App.jsx                       # Main app component with navigation
│   ├── main.jsx                      # App entry point
│   └── theme.js                      # Material-UI dark theme configuration
├── index.html                        # HTML template
├── package.json                      # Dependencies and scripts
├── vite.config.js                    # Vite configuration
└── README.md                         # This file
```

## Usage

### Adding Journal Entries
1. Navigate to the "Add Entry" tab
2. Fill in the transaction details:
   - Date (defaults to today)
   - Description of the transaction
   - Debit account (account being debited)
   - Credit account (account being credited)
   - Amount (positive number)
3. Click "Add Journal Entry"

### Viewing Journal Entries
- Click the "Journal Entries" tab to see all transactions
- Use the view button to see entry details
- Use the delete button to remove entries

### T-Accounts
- Select the "T-Accounts" tab
- Choose an account from the dropdown
- View the account in traditional T-account format with:
  - Debit transactions on the left
  - Credit transactions on the right
  - Running balance calculation
  - Transaction history table

### Balance Summary
- Navigate to the "Balance Summary" tab
- View account balances organized by type
- See income statement and balance sheet summaries
- Accounts are grouped into:
  - Assets (normal debit balance)
  - Liabilities (normal credit balance)
  - Equity (normal credit balance)
  - Revenue (normal credit balance)
  - Expenses (normal debit balance)

### Account Management
- Click the "Manage Accounts" tab to access account management
- **Add New Accounts**: Click "Add Account" to create custom accounts
  - Select account type first (Asset, Liability, Equity, Revenue, or Expense)
  - Account code is auto-generated based on type:
    - Assets: 1000-1999
    - Liabilities: 2000-2999
    - Equity: 3000-3999
    - Revenue: 4000-4999
    - Expenses: 5000-5999
  - Edit the auto-generated code if needed (must be unique)
  - Provide descriptive account name
  - Use the ↻ button to regenerate the account code
- **Edit Accounts**: Click the edit icon to modify account names and types
- **Delete Accounts**: Remove unused accounts (accounts with transactions cannot be deleted)
- **Usage Tracking**: See which accounts are "In Use" vs "Available"
- **Organized by Type**: Accounts are displayed grouped by their type with color coding

## Chart of Accounts

The application comes with a predefined chart of accounts:

**Assets:**
- 1001 - Cash
- 1002 - Accounts Receivable
- 1003 - Inventory
- 1004 - Equipment
- 1005 - Buildings

**Liabilities:**
- 2001 - Accounts Payable
- 2002 - Notes Payable
- 2003 - Mortgage Payable

**Equity:**
- 3001 - Owner's Capital
- 3002 - Retained Earnings

**Revenue:**
- 4001 - Sales Revenue
- 4002 - Service Revenue
- 4003 - Interest Revenue

**Expenses:**
- 5001 - Cost of Goods Sold
- 5002 - Salaries Expense
- 5003 - Rent Expense
- 5004 - Utilities Expense
- 5005 - Advertising Expense
- 5006 - Depreciation Expense

## Technologies Used

- **React 18** - Frontend framework
- **Vite** - Build tool and development server
- **Material-UI (MUI)** - Component library and design system
- **Material-UI Icons** - Icon components
- **Day.js** - Date handling library
- **Local Storage API** - Data persistence

## Educational Value

This simulator demonstrates key accounting concepts:
- **Double-Entry Principle**: Every transaction affects at least two accounts
- **Debits and Credits**: Understanding which accounts increase/decrease with debits vs credits
- **Account Types**: Different behavior of Assets, Liabilities, Equity, Revenue, and Expenses
- **T-Accounts**: Traditional visual representation of account transactions
- **Trial Balance**: Ensuring debits equal credits across all accounts

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Customization

You can customize the chart of accounts in two ways:
1. **Through the UI**: Use the "Manage Accounts" tab to add, edit, or delete accounts through the user interface
2. **Code Modification**: Modify `src/data/accounts.js` to change the default accounts that appear on first load

The application stores all account data in the browser's local storage, so any changes made through the UI will persist across sessions.

## License

This project is open source and available under the MIT License. 