import React, { useEffect, useState } from 'react'
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
  AccordionDetails,
} from '@mui/material'
import { ExpandMore as ExpandMoreIcon } from '@mui/icons-material'
import { ACCOUNT_TYPES, NORMAL_BALANCES } from '../data/accounts'
import { useGame } from '../GameContext'

function BalanceSummary() {
  const { state } = useGame()
  const [accountBalances, setAccountBalances] = useState({})

  useEffect(() => {
    calculateAccountBalances()
  }, [state.accounts, state.journalEntries])

  const calculateAccountBalances = () => {
    const balances = {}

    state.accounts.forEach((account) => {
      balances[account.code] = {
        ...account,
        balance: 0,
      }
    })

    state.journalEntries.forEach((entry) => {
      const debitAccount = state.accounts.find((acc) => acc.code === entry.debitAccount)
      const creditAccount = state.accounts.find((acc) => acc.code === entry.creditAccount)

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

  const formatCurrency = (amount) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Math.abs(amount))

  const getAccountsByType = (type) =>
    Object.values(accountBalances)
      .filter((account) => account.type === type)
      .sort((a, b) => a.code.localeCompare(b.code))

  const getTotalByType = (type) => getAccountsByType(type).reduce((total, account) => total + account.balance, 0)

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
            <Chip label={formatCurrency(total)} color={total >= 0 ? 'success' : 'error'} variant="outlined" />
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <TableContainer component={Paper} elevation={0}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Code</strong></TableCell>
                  <TableCell><strong>Name</strong></TableCell>
                  <TableCell align="right"><strong>Balance</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {accountsOfType.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={3} align="center">
                      <Typography variant="body2" color="text.secondary">
                        No accounts in this category yet.
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  accountsOfType.map((account) => (
                    <TableRow key={account.code}>
                      <TableCell>{account.code}</TableCell>
                      <TableCell>{account.name}</TableCell>
                      <TableCell align="right">
                        <Typography
                          variant="body2"
                          fontWeight="bold"
                          color={account.balance >= 0 ? 'success.main' : 'error.main'}
                        >
                          {formatCurrency(account.balance)}
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </AccordionDetails>
      </Accordion>
    )
  }

  return (
    <Card>
      <CardHeader title="Balance Summary" titleTypographyProps={{ variant: 'h5', fontWeight: 600 }} />
      <CardContent>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <AccountTypeSection type={ACCOUNT_TYPES.ASSET} title="Assets" color="success.main" />
            <AccountTypeSection type={ACCOUNT_TYPES.LIABILITY} title="Liabilities" color="error.main" />
            <AccountTypeSection type={ACCOUNT_TYPES.EQUITY} title="Equity" color="info.main" />
          </Grid>
          <Grid item xs={12} md={6}>
            <AccountTypeSection type={ACCOUNT_TYPES.REVENUE} title="Revenue" color="success.main" />
            <AccountTypeSection type={ACCOUNT_TYPES.EXPENSE} title="Expenses" color="warning.main" />
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  )
}

export default BalanceSummary
