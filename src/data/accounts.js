// Chart of Accounts
export const ACCOUNT_TYPES = {
  ASSET: 'Asset',
  LIABILITY: 'Liability',
  EQUITY: 'Equity',
  REVENUE: 'Revenue',
  EXPENSE: 'Expense',
}

export const NORMAL_BALANCES = {
  [ACCOUNT_TYPES.ASSET]: 'debit',
  [ACCOUNT_TYPES.EXPENSE]: 'debit',
  [ACCOUNT_TYPES.LIABILITY]: 'credit',
  [ACCOUNT_TYPES.EQUITY]: 'credit',
  [ACCOUNT_TYPES.REVENUE]: 'credit',
}

export const DEFAULT_ACCOUNTS = [
  // Assets
  { code: '1001', name: 'Cash', type: ACCOUNT_TYPES.ASSET },
  { code: '1002', name: 'Accounts Receivable', type: ACCOUNT_TYPES.ASSET },
  { code: '1003', name: 'Inventory', type: ACCOUNT_TYPES.ASSET },
  { code: '1004', name: 'Equipment', type: ACCOUNT_TYPES.ASSET },
  { code: '1005', name: 'Buildings', type: ACCOUNT_TYPES.ASSET },
  
  // Liabilities
  { code: '2001', name: 'Accounts Payable', type: ACCOUNT_TYPES.LIABILITY },
  { code: '2002', name: 'Notes Payable', type: ACCOUNT_TYPES.LIABILITY },
  { code: '2003', name: 'Mortgage Payable', type: ACCOUNT_TYPES.LIABILITY },
  
  // Equity
  { code: '3001', name: 'Owner\'s Capital', type: ACCOUNT_TYPES.EQUITY },
  { code: '3002', name: 'Retained Earnings', type: ACCOUNT_TYPES.EQUITY },
  
  // Revenue
  { code: '4001', name: 'Sales Revenue', type: ACCOUNT_TYPES.REVENUE },
  { code: '4002', name: 'Service Revenue', type: ACCOUNT_TYPES.REVENUE },
  { code: '4003', name: 'Interest Revenue', type: ACCOUNT_TYPES.REVENUE },
  
  // Expenses
  { code: '5001', name: 'Cost of Goods Sold', type: ACCOUNT_TYPES.EXPENSE },
  { code: '5002', name: 'Salaries Expense', type: ACCOUNT_TYPES.EXPENSE },
  { code: '5003', name: 'Rent Expense', type: ACCOUNT_TYPES.EXPENSE },
  { code: '5004', name: 'Utilities Expense', type: ACCOUNT_TYPES.EXPENSE },
  { code: '5005', name: 'Advertising Expense', type: ACCOUNT_TYPES.EXPENSE },
  { code: '5006', name: 'Depreciation Expense', type: ACCOUNT_TYPES.EXPENSE },
]

// Local storage helper functions
export const getAccountsFromStorage = () => {
  const stored = localStorage.getItem('bookkeeping_accounts')
  return stored ? JSON.parse(stored) : DEFAULT_ACCOUNTS
}

export const saveAccountsToStorage = (accounts) => {
  localStorage.setItem('bookkeeping_accounts', JSON.stringify(accounts))
  // Dispatch custom event to notify other components
  window.dispatchEvent(new CustomEvent('accountsUpdated'))
}

export const getJournalEntriesFromStorage = () => {
  const stored = localStorage.getItem('bookkeeping_journal_entries')
  return stored ? JSON.parse(stored) : []
}

export const saveJournalEntriesToStorage = (entries) => {
  localStorage.setItem('bookkeeping_journal_entries', JSON.stringify(entries))
} 