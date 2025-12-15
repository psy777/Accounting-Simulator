import React, { useState, useEffect } from 'react'
import {
  Card,
  CardHeader,
  CardContent,
  Grid,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Box,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material'
import { ExpandMore as ExpandMoreIcon } from '@mui/icons-material'
import { 
  getAccountsFromStorage, 
  getJournalEntriesFromStorage,
  ACCOUNT_TYPES,
  NORMAL_BALANCES 
} from '../data/accounts'

function BalanceSummary() {
  const [accounts, setAccounts] = useState([])
  const [entries, setEntries] = useState([])
  const [accountBalances, setAccountBalances] = useState({})

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
    calculateAccountBalances()
  }, [accounts, entries])

  const calculateAccountBalances = () => {
    const balances = {}
    
    accounts.forEach(account => {
      balances[account.code] = {
        ...account,
        balance: 0
      }
    })

    entries.forEach(entry => {
      const debitAccount = accounts.find(acc => acc.code === entry.debitAccount)
      const creditAccount = accounts.find(acc => acc.code === entry.creditAccount)

      if (debitAccount) {
        if (NORMAL_BALANCES[debitAccount.type] === 'debit') {
          balances[entry.debitAccount].balance += entry.amount
        } else {
          balances[entry.debitAccount].balance -= entry.amount
        }
      }

      if (creditAccount) {
        if (NORMAL_BALANCES[creditAccount.type] === 'credit') {
          balances[entry.creditAccount].balance += entry.amount
        } else {
          balances[entry.creditAccount].balance -= entry.amount
        }
      }
    })

    setAccountBalances(balances)
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(Math.abs(amount))
  }

  const getAccountsByType = (type) => {
    return Object.values(accountBalances)
      .filter(account => account.type === type)
      .sort((a, b) => a.code.localeCompare(b.code))
  }

  const getTotalByType = (type) => {
    return getAccountsByType(type)
      .reduce((total, account) => total + account.balance, 0)
  }

  const AccountTypeSection = ({ type, title, color }) => {
    const accountsOfType = getAccountsByType(type)
    const total = getTotalByType(type)
    
    return (
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', justifyContent: 'space-between' }}>
            <Typography variant="h6" sx={{ color }}>
              {title}
            </Typography>
            <Chip 
              label={formatCurrency(total)}
              color={total >= 0 ? 'success' : 'error'}
              variant="outlined"
            />
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <TableContainer component={Paper} elevation={0}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Account Code</strong></TableCell>
                  <TableCell><strong>Account Name</strong></TableCell>
                  <TableCell align="right"><strong>Balance</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {accountsOfType.map((account) => (
                  <TableRow key={account.code}>
                    <TableCell>{account.code}</TableCell>
                    <TableCell>{account.name}</TableCell>
                    <TableCell align="right">
                      <Typography 
                        variant="body2"
                        fontWeight={account.balance !== 0 ? 'bold' : 'normal'}
                      >
                        {formatCurrency(account.balance)}
                        {account.balance < 0 && ' (CR)'}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </AccordionDetails>
      </Accordion>
    )
  }

  const totalAssets = getTotalByType(ACCOUNT_TYPES.ASSET)
  const totalLiabilities = getTotalByType(ACCOUNT_TYPES.LIABILITY)
  const totalEquity = getTotalByType(ACCOUNT_TYPES.EQUITY)
  const totalRevenue = getTotalByType(ACCOUNT_TYPES.REVENUE)
  const totalExpenses = getTotalByType(ACCOUNT_TYPES.EXPENSE)
  
  const netIncome = totalRevenue - totalExpenses

  return (
    <Card>
      <CardHeader
        title="Account Balance Summary"
        titleTypographyProps={{ variant: 'h5', fontWeight: 600 }}
      />
      <CardContent>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper elevation={1} sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Income Statement Summary
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography>Total Revenue:</Typography>
                <Typography fontWeight="bold" color="success.main">
                  {formatCurrency(totalRevenue)}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography>Total Expenses:</Typography>
                <Typography fontWeight="bold" color="error.main">
                  {formatCurrency(totalExpenses)}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', borderTop: 1, pt: 1 }}>
                <Typography fontWeight="bold">Net Income:</Typography>
                <Typography 
                  fontWeight="bold" 
                  color={netIncome >= 0 ? 'success.main' : 'error.main'}
                >
                  {formatCurrency(netIncome)}
                </Typography>
              </Box>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper elevation={1} sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Balance Sheet Summary
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography>Total Assets:</Typography>
                <Typography fontWeight="bold">
                  {formatCurrency(totalAssets)}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography>Total Liabilities:</Typography>
                <Typography fontWeight="bold">
                  {formatCurrency(totalLiabilities)}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', borderTop: 1, pt: 1 }}>
                <Typography fontWeight="bold">Total Equity:</Typography>
                <Typography fontWeight="bold">
                  {formatCurrency(totalEquity)}
                </Typography>
              </Box>
            </Paper>
          </Grid>
        </Grid>

        <Box sx={{ mt: 3 }}>
          <AccountTypeSection 
            type={ACCOUNT_TYPES.ASSET} 
            title="Assets" 
            color="success.main" 
          />
          <AccountTypeSection 
            type={ACCOUNT_TYPES.LIABILITY} 
            title="Liabilities" 
            color="error.main" 
          />
          <AccountTypeSection 
            type={ACCOUNT_TYPES.EQUITY} 
            title="Equity" 
            color="info.main" 
          />
          <AccountTypeSection 
            type={ACCOUNT_TYPES.REVENUE} 
            title="Revenue" 
            color="success.main" 
          />
          <AccountTypeSection 
            type={ACCOUNT_TYPES.EXPENSE} 
            title="Expenses" 
            color="warning.main" 
          />
        </Box>
      </CardContent>
    </Card>
  )
}

export default BalanceSummary 