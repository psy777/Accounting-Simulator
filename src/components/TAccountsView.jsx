import React, { useState, useEffect } from 'react'
import {
  Card,
  CardHeader,
  CardContent,
  Grid,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Box,
  Divider,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material'
import { 
  getAccountsFromStorage, 
  getJournalEntriesFromStorage,
  NORMAL_BALANCES 
} from '../data/accounts'

function TAccountsView() {
  const [accounts, setAccounts] = useState([])
  const [entries, setEntries] = useState([])
  const [selectedAccount, setSelectedAccount] = useState('')
  const [accountTransactions, setAccountTransactions] = useState([])

  useEffect(() => {
    setAccounts(getAccountsFromStorage())
    setEntries(getJournalEntriesFromStorage())
    
    const handleAccountsUpdate = () => {
      setAccounts(getAccountsFromStorage())
    }
    
    window.addEventListener('accountsUpdated', handleAccountsUpdate)
    
    return () => {
      window.removeEventListener('accountsUpdated', handleAccountsUpdate)
    }
  }, [])

  useEffect(() => {
    if (selectedAccount && entries.length > 0) {
      calculateAccountTransactions()
    }
  }, [selectedAccount, entries])

  const calculateAccountTransactions = () => {
    const account = accounts.find(acc => acc.code === selectedAccount)
    if (!account) return

    const transactions = []
    let runningBalance = 0

    // Filter entries that affect this account
    const relevantEntries = entries
      .filter(entry => 
        entry.debitAccount === selectedAccount || 
        entry.creditAccount === selectedAccount
      )
      .sort((a, b) => new Date(a.date) - new Date(b.date))

    relevantEntries.forEach(entry => {
      const isDebit = entry.debitAccount === selectedAccount
      const amount = entry.amount

      // Calculate running balance based on normal balance of account
      if (NORMAL_BALANCES[account.type] === 'debit') {
        runningBalance += isDebit ? amount : -amount
      } else {
        runningBalance += isDebit ? -amount : amount
      }

      transactions.push({
        ...entry,
        side: isDebit ? 'debit' : 'credit',
        amount: amount,
        runningBalance: runningBalance
      })
    })

    setAccountTransactions(transactions)
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(Math.abs(amount))
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  const getAccountDisplay = (account) => {
    return `${account.code} - ${account.name}`
  }

  const getCurrentBalance = () => {
    if (accountTransactions.length === 0) return 0
    return accountTransactions[accountTransactions.length - 1].runningBalance
  }

  const getDebitTransactions = () => {
    return accountTransactions.filter(t => t.side === 'debit')
  }

  const getCreditTransactions = () => {
    return accountTransactions.filter(t => t.side === 'credit')
  }

  const selectedAccountData = accounts.find(acc => acc.code === selectedAccount)

  return (
    <Card>
      <CardHeader
        title="T-Accounts View"
        titleTypographyProps={{ variant: 'h5', fontWeight: 600 }}
      />
      <CardContent>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Select Account</InputLabel>
              <Select
                value={selectedAccount}
                label="Select Account"
                onChange={(e) => setSelectedAccount(e.target.value)}
              >
                {accounts.map((account) => (
                  <MenuItem key={account.code} value={account.code}>
                    {getAccountDisplay(account)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </Grid>

        {selectedAccount && selectedAccountData && (
          <Box sx={{ mt: 3 }}>
            {/* T-Account Header */}
            <Paper elevation={2} sx={{ p: 2, mb: 3 }}>
              <Typography variant="h6" align="center" gutterBottom>
                {getAccountDisplay(selectedAccountData)}
              </Typography>
              <Typography variant="subtitle2" align="center" color="text.secondary">
                Type: {selectedAccountData.type} | Normal Balance: {NORMAL_BALANCES[selectedAccountData.type]}
              </Typography>
              <Typography variant="h6" align="center" sx={{ mt: 1 }}>
                Current Balance: {formatCurrency(getCurrentBalance())}
                {getCurrentBalance() < 0 && ' (CR)'}
              </Typography>
            </Paper>

            {/* T-Account Layout */}
            <Grid container spacing={2}>
              {/* Debit Side */}
              <Grid item xs={12} md={6}>
                <Paper elevation={1} sx={{ height: '100%' }}>
                  <Box sx={{ p: 2, bgcolor: 'success.dark', color: 'white' }}>
                    <Typography variant="h6" align="center">
                      Debit
                    </Typography>
                  </Box>
                  <Box sx={{ p: 2 }}>
                    {getDebitTransactions().length === 0 ? (
                      <Typography variant="body2" color="text.secondary" align="center">
                        No debit transactions
                      </Typography>
                    ) : (
                      getDebitTransactions().map((transaction, index) => (
                        <Box key={index} sx={{ mb: 1, pb: 1, borderBottom: '1px solid #333' }}>
                          <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                            {formatDate(transaction.date)}
                          </Typography>
                          <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                            {transaction.description}
                          </Typography>
                          <Typography variant="body2" fontWeight="bold" align="right">
                            {formatCurrency(transaction.amount)}
                          </Typography>
                        </Box>
                      ))
                    )}
                  </Box>
                </Paper>
              </Grid>

              {/* Credit Side */}
              <Grid item xs={12} md={6}>
                <Paper elevation={1} sx={{ height: '100%' }}>
                  <Box sx={{ p: 2, bgcolor: 'error.dark', color: 'white' }}>
                    <Typography variant="h6" align="center">
                      Credit
                    </Typography>
                  </Box>
                  <Box sx={{ p: 2 }}>
                    {getCreditTransactions().length === 0 ? (
                      <Typography variant="body2" color="text.secondary" align="center">
                        No credit transactions
                      </Typography>
                    ) : (
                      getCreditTransactions().map((transaction, index) => (
                        <Box key={index} sx={{ mb: 1, pb: 1, borderBottom: '1px solid #333' }}>
                          <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                            {formatDate(transaction.date)}
                          </Typography>
                          <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
                            {transaction.description}
                          </Typography>
                          <Typography variant="body2" fontWeight="bold" align="right">
                            {formatCurrency(transaction.amount)}
                          </Typography>
                        </Box>
                      ))
                    )}
                  </Box>
                </Paper>
              </Grid>
            </Grid>

            {/* Transaction History Table */}
            {accountTransactions.length > 0 && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Transaction History with Running Balance
                </Typography>
                <TableContainer component={Paper} elevation={1}>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell><strong>Date</strong></TableCell>
                        <TableCell><strong>Description</strong></TableCell>
                        <TableCell align="center"><strong>Debit</strong></TableCell>
                        <TableCell align="center"><strong>Credit</strong></TableCell>
                        <TableCell align="right"><strong>Balance</strong></TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {accountTransactions.map((transaction, index) => (
                        <TableRow key={index}>
                          <TableCell>{formatDate(transaction.date)}</TableCell>
                          <TableCell>{transaction.description}</TableCell>
                          <TableCell align="center">
                            {transaction.side === 'debit' && formatCurrency(transaction.amount)}
                          </TableCell>
                          <TableCell align="center">
                            {transaction.side === 'credit' && formatCurrency(transaction.amount)}
                          </TableCell>
                          <TableCell align="right">
                            <Typography 
                              variant="body2" 
                              fontWeight="bold"
                              color={transaction.runningBalance >= 0 ? 'success.main' : 'error.main'}
                            >
                              {formatCurrency(transaction.runningBalance)}
                              {transaction.runningBalance < 0 && ' (CR)'}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Box>
            )}
          </Box>
        )}

        {!selectedAccount && (
          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Typography variant="body1" color="text.secondary">
              Select an account to view its T-account layout and transaction history.
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  )
}

export default TAccountsView 