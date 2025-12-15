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
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Typography,
  Alert,
  Chip,
  Box,
  Grid
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
  Cancel as CancelIcon
} from '@mui/icons-material'
import {
  getAccountsFromStorage,
  saveAccountsToStorage,
  getJournalEntriesFromStorage,
  ACCOUNT_TYPES
} from '../data/accounts'

function AccountManagement() {
  const [accounts, setAccounts] = useState([])
  const [entries, setEntries] = useState([])
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingAccount, setEditingAccount] = useState(null)
  const [formData, setFormData] = useState({
    code: '',
    name: '',
    type: ''
  })
  const [alert, setAlert] = useState({ show: false, message: '', severity: 'success' })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = () => {
    setAccounts(getAccountsFromStorage())
    setEntries(getJournalEntriesFromStorage())
  }

  const showAlert = (message, severity) => {
    setAlert({ show: true, message, severity })
    setTimeout(() => {
      setAlert({ show: false, message: '', severity: 'success' })
    }, 5000)
  }

  const generateAccountCode = (accountType) => {
    // Define ranges for each account type
    const ranges = {
      [ACCOUNT_TYPES.ASSET]: { start: 1000, end: 1999 },
      [ACCOUNT_TYPES.LIABILITY]: { start: 2000, end: 2999 },
      [ACCOUNT_TYPES.EQUITY]: { start: 3000, end: 3999 },
      [ACCOUNT_TYPES.REVENUE]: { start: 4000, end: 4999 },
      [ACCOUNT_TYPES.EXPENSE]: { start: 5000, end: 5999 }
    }

    if (!ranges[accountType]) return ''

    const { start, end } = ranges[accountType]
    const existingCodes = new Set(accounts.map(acc => parseInt(acc.code)).filter(code => !isNaN(code)))

    // Find the next available code in the range
    for (let code = start; code <= end; code += 10) {
      if (!existingCodes.has(code)) {
        return code.toString()
      }
    }

    // If all multiples of 10 are taken, try individual numbers
    for (let code = start; code <= end; code++) {
      if (!existingCodes.has(code)) {
        return code.toString()
      }
    }

    // If range is full, return the next number after the range
    return (end + 1).toString()
  }

  const handleAddAccount = () => {
    setEditingAccount(null)
    setFormData({ code: '', name: '', type: '' })
    setDialogOpen(true)
  }

  const handleEditAccount = (account) => {
    setEditingAccount(account)
    setFormData({ ...account })
    setDialogOpen(true)
  }

  const handleDeleteAccount = (accountCode) => {
    // Check if account is used in any journal entries
    const accountUsed = entries.some(entry => 
      entry.debitAccount === accountCode || entry.creditAccount === accountCode
    )

    if (accountUsed) {
      showAlert(
        'Cannot delete account: it is used in existing journal entries. Delete the journal entries first.',
        'error'
      )
      return
    }

    const updatedAccounts = accounts.filter(account => account.code !== accountCode)
    setAccounts(updatedAccounts)
    saveAccountsToStorage(updatedAccounts)
    showAlert('Account deleted successfully!', 'success')
  }

  const validateForm = () => {
    if (!formData.code.trim()) {
      showAlert('Please enter an account code', 'error')
      return false
    }
    if (!formData.name.trim()) {
      showAlert('Please enter an account name', 'error')
      return false
    }
    if (!formData.type) {
      showAlert('Please select an account type', 'error')
      return false
    }

    // Check for duplicate account codes (excluding current account when editing)
    const duplicateCode = accounts.some(account => 
      account.code === formData.code.trim() && 
      (!editingAccount || account.code !== editingAccount.code)
    )

    if (duplicateCode) {
      showAlert('Account code already exists. Please use a different code. Try the auto-generated code or choose another unique code.', 'error')
      return false
    }

    // Validate account code format (should be numeric and reasonable length)
    const codeNum = parseInt(formData.code.trim())
    if (isNaN(codeNum) || formData.code.trim().length < 3 || formData.code.trim().length > 6) {
      showAlert('Account code should be a number between 3-6 digits (e.g., 1010)', 'error')
      return false
    }

    return true
  }

  const handleSaveAccount = () => {
    if (!validateForm()) return

    const accountData = {
      code: formData.code.trim(),
      name: formData.name.trim(),
      type: formData.type
    }

    let updatedAccounts
    if (editingAccount) {
      // Update existing account
      updatedAccounts = accounts.map(account => 
        account.code === editingAccount.code ? accountData : account
      )
      showAlert('Account updated successfully!', 'success')
    } else {
      // Add new account
      updatedAccounts = [...accounts, accountData]
      showAlert('Account created successfully!', 'success')
    }

    setAccounts(updatedAccounts)
    saveAccountsToStorage(updatedAccounts)
    setDialogOpen(false)
    setFormData({ code: '', name: '', type: '' })
    setEditingAccount(null)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
    setFormData({ code: '', name: '', type: '' })
    setEditingAccount(null)
  }

  const handleInputChange = (field) => (event) => {
    const newFormData = {
      ...formData,
      [field]: event.target.value
    }

    // Auto-generate account code when type is selected (only for new accounts)
    if (field === 'type' && !editingAccount && event.target.value) {
      const generatedCode = generateAccountCode(event.target.value)
      newFormData.code = generatedCode
    }

    setFormData(newFormData)
  }

  const getAccountsByType = (type) => {
    return accounts.filter(account => account.type === type)
  }

  const isAccountUsed = (accountCode) => {
    return entries.some(entry => 
      entry.debitAccount === accountCode || entry.creditAccount === accountCode
    )
  }

  const getTypeColor = (type) => {
    const colors = {
      [ACCOUNT_TYPES.ASSET]: 'success',
      [ACCOUNT_TYPES.LIABILITY]: 'error', 
      [ACCOUNT_TYPES.EQUITY]: 'info',
      [ACCOUNT_TYPES.REVENUE]: 'success',
      [ACCOUNT_TYPES.EXPENSE]: 'warning'
    }
    return colors[type] || 'default'
  }

  const getTypeIcon = (type) => {
    const icons = {
      [ACCOUNT_TYPES.ASSET]: '🏢',
      [ACCOUNT_TYPES.LIABILITY]: '💳',
      [ACCOUNT_TYPES.EQUITY]: '🏛️',
      [ACCOUNT_TYPES.REVENUE]: '💰',
      [ACCOUNT_TYPES.EXPENSE]: '📊'
    }
    return icons[type] || ''
  }

  const AccountTypeSection = ({ type, title }) => {
    const typeAccounts = getAccountsByType(type)
    
    if (typeAccounts.length === 0) return null

    return (
             <Box sx={{ mb: 3 }}>
         <Typography variant="h6" gutterBottom color={`${getTypeColor(type)}.main`}>
           {getTypeIcon(type)} {title} ({typeAccounts.length})
         </Typography>
        <TableContainer component={Paper} elevation={1}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell><strong>Code</strong></TableCell>
                <TableCell><strong>Name</strong></TableCell>
                <TableCell align="center"><strong>Status</strong></TableCell>
                <TableCell align="center"><strong>Actions</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {typeAccounts
                .sort((a, b) => a.code.localeCompare(b.code))
                .map((account) => (
                <TableRow key={account.code}>
                  <TableCell>
                    <Typography variant="body2" fontWeight="bold">
                      {account.code}
                    </Typography>
                  </TableCell>
                  <TableCell>{account.name}</TableCell>
                  <TableCell align="center">
                    <Chip
                      label={isAccountUsed(account.code) ? 'In Use' : 'Available'}
                      color={isAccountUsed(account.code) ? 'primary' : 'default'}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell align="center">
                    <IconButton
                      size="small"
                      onClick={() => handleEditAccount(account)}
                      color="primary"
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => handleDeleteAccount(account.code)}
                      color="error"
                      disabled={isAccountUsed(account.code)}
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    )
  }

  return (
    <>
      <Card>
        <CardHeader
          title={`Account Management (${accounts.length} accounts)`}
          titleTypographyProps={{ variant: 'h5', fontWeight: 600 }}
          action={
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleAddAccount}
            >
              Add Account
            </Button>
          }
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

          {accounts.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="body1" color="text.secondary">
                No accounts found. Click "Add Account" to create your first account.
              </Typography>
            </Box>
          ) : (
            <>
              <AccountTypeSection type={ACCOUNT_TYPES.ASSET} title="Assets" />
              <AccountTypeSection type={ACCOUNT_TYPES.LIABILITY} title="Liabilities" />
              <AccountTypeSection type={ACCOUNT_TYPES.EQUITY} title="Equity" />
              <AccountTypeSection type={ACCOUNT_TYPES.REVENUE} title="Revenue" />
              <AccountTypeSection type={ACCOUNT_TYPES.EXPENSE} title="Expenses" />
            </>
          )}
        </CardContent>
      </Card>

      {/* Add/Edit Account Dialog */}
      <Dialog 
        open={dialogOpen} 
        onClose={handleCloseDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          {editingAccount ? 'Edit Account' : 'Add New Account'}
        </DialogTitle>
        <DialogContent>
                     <Grid container spacing={2} sx={{ mt: 1 }}>
             <Grid item xs={12}>
               <FormControl fullWidth>
                 <InputLabel>Account Type</InputLabel>
                 <Select
                   value={formData.type}
                   label="Account Type"
                   onChange={handleInputChange('type')}
                 >
                   <MenuItem value={ACCOUNT_TYPES.ASSET}>🏢 Asset (1000-1999)</MenuItem>
                   <MenuItem value={ACCOUNT_TYPES.LIABILITY}>💳 Liability (2000-2999)</MenuItem>
                   <MenuItem value={ACCOUNT_TYPES.EQUITY}>🏛️ Equity (3000-3999)</MenuItem>
                   <MenuItem value={ACCOUNT_TYPES.REVENUE}>💰 Revenue (4000-4999)</MenuItem>
                   <MenuItem value={ACCOUNT_TYPES.EXPENSE}>📊 Expense (5000-5999)</MenuItem>
                 </Select>
                 <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, ml: 1 }}>
                   {!editingAccount && "Select type first to auto-generate account code"}
                 </Typography>
               </FormControl>
             </Grid>
             <Grid item xs={12} md={4}>
               <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}>
                 <TextField
                   fullWidth
                   label="Account Code"
                   value={formData.code}
                   onChange={handleInputChange('code')}
                   placeholder={editingAccount ? "Cannot change" : "Auto-generated"}
                   helperText={
                     editingAccount 
                       ? "Account code cannot be changed" 
                       : formData.type 
                         ? "Auto-generated (you can edit if needed)" 
                         : "Select account type first"
                   }
                   disabled={!!editingAccount || !formData.type} // Disable if editing or no type selected
                 />
                 {!editingAccount && formData.type && (
                   <Button
                     variant="outlined"
                     size="small"
                     onClick={() => {
                       const newCode = generateAccountCode(formData.type)
                       setFormData({ ...formData, code: newCode })
                     }}
                     sx={{ mt: 1, minWidth: 'auto', px: 1 }}
                     title="Regenerate account code"
                   >
                     ↻
                   </Button>
                 )}
               </Box>
             </Grid>
             <Grid item xs={12} md={8}>
               <TextField
                 fullWidth
                 label="Account Name"
                 value={formData.name}
                 onChange={handleInputChange('name')}
                 placeholder="e.g., Petty Cash"
                 helperText="Descriptive name for the account"
               />
             </Grid>
           </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog} startIcon={<CancelIcon />}>
            Cancel
          </Button>
          <Button 
            onClick={handleSaveAccount} 
            variant="contained"
            startIcon={<SaveIcon />}
          >
            {editingAccount ? 'Update' : 'Create'} Account
          </Button>
        </DialogActions>
      </Dialog>
    </>
  )
}

export default AccountManagement 