import React, { useState, useEffect } from 'react'
import {
  Card,
  CardHeader,
  CardContent,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Button,
  Grid,
  Alert,
  Box,
  InputAdornment
} from '@mui/material'
import { DatePicker } from '@mui/x-date-pickers'
import { Save as SaveIcon } from '@mui/icons-material'
import dayjs from 'dayjs'
import { 
  getAccountsFromStorage, 
  getJournalEntriesFromStorage, 
  saveJournalEntriesToStorage 
} from '../data/accounts'

function JournalEntryForm() {
  const [accounts, setAccounts] = useState([])
  const [formData, setFormData] = useState({
    date: dayjs(),
    description: '',
    debitAccount: '',
    creditAccount: '',
    amount: ''
  })
  const [alert, setAlert] = useState({ show: false, message: '', severity: 'success' })

  useEffect(() => {
    setAccounts(getAccountsFromStorage())
    
    const handleAccountsUpdate = () => {
      setAccounts(getAccountsFromStorage())
    }
    
    window.addEventListener('accountsUpdated', handleAccountsUpdate)
    
    return () => {
      window.removeEventListener('accountsUpdated', handleAccountsUpdate)
    }
  }, [])

  const handleInputChange = (field) => (event) => {
    setFormData({
      ...formData,
      [field]: event.target.value
    })
  }

  const handleDateChange = (newDate) => {
    setFormData({
      ...formData,
      date: newDate
    })
  }

  const validateForm = () => {
    if (!formData.description.trim()) {
      showAlert('Please enter a description', 'error')
      return false
    }
    if (!formData.debitAccount) {
      showAlert('Please select a debit account', 'error')
      return false
    }
    if (!formData.creditAccount) {
      showAlert('Please select a credit account', 'error')
      return false
    }
    if (formData.debitAccount === formData.creditAccount) {
      showAlert('Debit and credit accounts must be different', 'error')
      return false
    }
    if (!formData.amount || parseFloat(formData.amount) <= 0) {
      showAlert('Please enter a valid amount', 'error')
      return false
    }
    return true
  }

  const showAlert = (message, severity) => {
    setAlert({ show: true, message, severity })
    setTimeout(() => {
      setAlert({ show: false, message: '', severity: 'success' })
    }, 5000)
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    
    if (!validateForm()) return

    const newEntry = {
      id: Date.now().toString(),
      date: formData.date.format('YYYY-MM-DD'),
      description: formData.description.trim(),
      debitAccount: formData.debitAccount,
      creditAccount: formData.creditAccount,
      amount: parseFloat(formData.amount)
    }

    const currentEntries = getJournalEntriesFromStorage()
    const updatedEntries = [...currentEntries, newEntry]
    saveJournalEntriesToStorage(updatedEntries)

    showAlert('Journal entry added successfully!', 'success')
    
    // Reset form
    setFormData({
      date: dayjs(),
      description: '',
      debitAccount: '',
      creditAccount: '',
      amount: ''
    })
  }

  const getAccountDisplay = (account) => {
    return `${account.code} - ${account.name}`
  }

  return (
    <Card>
      <CardHeader
        title="Add New Journal Entry"
        titleTypographyProps={{ variant: 'h5', fontWeight: 600 }}
      />
      <CardContent>
        {alert.show && (
          <Alert 
            severity={alert.severity} 
            sx={{ mb: 2 }}
            onClose={() => setAlert({ ...alert, show: false })}
          >
            {alert.message}
          </Alert>
        )}
        
        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <DatePicker
                label="Date"
                value={formData.date}
                onChange={handleDateChange}
                slotProps={{
                  textField: {
                    fullWidth: true,
                    required: true
                  }
                }}
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                value={formData.description}
                onChange={handleInputChange('description')}
                multiline
                rows={2}
                required
                placeholder="Enter transaction description..."
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <FormControl fullWidth required>
                <InputLabel>Debit Account</InputLabel>
                <Select
                  value={formData.debitAccount}
                  label="Debit Account"
                  onChange={handleInputChange('debitAccount')}
                >
                  {accounts.map((account) => (
                    <MenuItem key={account.code} value={account.code}>
                      {getAccountDisplay(account)}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <FormControl fullWidth required>
                <InputLabel>Credit Account</InputLabel>
                <Select
                  value={formData.creditAccount}
                  label="Credit Account"
                  onChange={handleInputChange('creditAccount')}
                >
                  {accounts.map((account) => (
                    <MenuItem key={account.code} value={account.code}>
                      {getAccountDisplay(account)}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Amount"
                type="number"
                value={formData.amount}
                onChange={handleInputChange('amount')}
                required
                inputProps={{ min: 0, step: 0.01 }}
                InputProps={{
                  startAdornment: <InputAdornment position="start">$</InputAdornment>,
                }}
              />
            </Grid>
            
            <Grid item xs={12}>
              <Button
                type="submit"
                variant="contained"
                size="large"
                startIcon={<SaveIcon />}
                sx={{ mt: 2 }}
              >
                Add Journal Entry
              </Button>
            </Grid>
          </Grid>
        </Box>
      </CardContent>
    </Card>
  )
}

export default JournalEntryForm 