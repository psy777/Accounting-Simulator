import React, { useState, useEffect } from 'react'
import {
  Card,
  CardHeader,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Chip
} from '@mui/material'
import { 
  Delete as DeleteIcon,
  Visibility as VisibilityIcon 
} from '@mui/icons-material'
import { 
  getJournalEntriesFromStorage, 
  saveJournalEntriesToStorage,
  getAccountsFromStorage 
} from '../data/accounts'

function JournalEntriesTable() {
  const [entries, setEntries] = useState([])
  const [accounts, setAccounts] = useState([])
  const [selectedEntry, setSelectedEntry] = useState(null)
  const [viewDialogOpen, setViewDialogOpen] = useState(false)

  useEffect(() => {
    setEntries(getJournalEntriesFromStorage())
    setAccounts(getAccountsFromStorage())
    
    const handleAccountsUpdate = () => {
      setAccounts(getAccountsFromStorage())
    }
    
    window.addEventListener('accountsUpdated', handleAccountsUpdate)
    
    return () => {
      window.removeEventListener('accountsUpdated', handleAccountsUpdate)
    }
  }, [])

  const getAccountName = (accountCode) => {
    const account = accounts.find(acc => acc.code === accountCode)
    return account ? `${account.code} - ${account.name}` : accountCode
  }

  const handleDelete = (entryId) => {
    const updatedEntries = entries.filter(entry => entry.id !== entryId)
    setEntries(updatedEntries)
    saveJournalEntriesToStorage(updatedEntries)
  }

  const handleView = (entry) => {
    setSelectedEntry(entry)
    setViewDialogOpen(true)
  }

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount)
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  if (entries.length === 0) {
    return (
      <Card>
        <CardHeader
          title="Journal Entries"
          titleTypographyProps={{ variant: 'h5', fontWeight: 600 }}
        />
        <CardContent>
          <Typography variant="body1" color="text.secondary" align="center" sx={{ py: 4 }}>
            No journal entries found. Add your first entry using the "Add Entry" tab.
          </Typography>
        </CardContent>
      </Card>
    )
  }

  return (
    <>
      <Card>
        <CardHeader
          title={`Journal Entries (${entries.length})`}
          titleTypographyProps={{ variant: 'h5', fontWeight: 600 }}
        />
        <CardContent>
          <TableContainer component={Paper} elevation={0}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Date</strong></TableCell>
                  <TableCell><strong>Description</strong></TableCell>
                  <TableCell><strong>Debit Account</strong></TableCell>
                  <TableCell><strong>Credit Account</strong></TableCell>
                  <TableCell align="right"><strong>Amount</strong></TableCell>
                  <TableCell align="center"><strong>Actions</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {entries
                  .sort((a, b) => new Date(b.date) - new Date(a.date))
                  .map((entry) => (
                  <TableRow key={entry.id} hover>
                    <TableCell>
                      <Chip 
                        label={formatDate(entry.date)} 
                        variant="outlined" 
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {entry.description}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="success.main">
                        {getAccountName(entry.debitAccount)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="error.main">
                        {getAccountName(entry.creditAccount)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" fontWeight="bold">
                        {formatCurrency(entry.amount)}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <IconButton
                        size="small"
                        onClick={() => handleView(entry)}
                        color="primary"
                      >
                        <VisibilityIcon />
                      </IconButton>
                      <IconButton
                        size="small"
                        onClick={() => handleDelete(entry.id)}
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* View Entry Dialog */}
      <Dialog 
        open={viewDialogOpen} 
        onClose={() => setViewDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Journal Entry Details</DialogTitle>
        <DialogContent>
          {selectedEntry && (
            <div>
              <Typography variant="h6" gutterBottom>
                {selectedEntry.description}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Date: {formatDate(selectedEntry.date)}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Amount: {formatCurrency(selectedEntry.amount)}
              </Typography>
              
              <div style={{ marginTop: 16 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Double-Entry:
                </Typography>
                <Typography variant="body2" color="success.main">
                  <strong>Debit:</strong> {getAccountName(selectedEntry.debitAccount)}
                </Typography>
                <Typography variant="body2" color="error.main">
                  <strong>Credit:</strong> {getAccountName(selectedEntry.creditAccount)}
                </Typography>
              </div>
            </div>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </>
  )
}

export default JournalEntriesTable 