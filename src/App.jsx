import React, { useState } from 'react'
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Container, 
  Tabs, 
  Tab, 
  Box 
} from '@mui/material'
import { 
  Add as AddIcon, 
  List as ListIcon, 
  AccountBalance as AccountBalanceIcon,
  Assessment as AssessmentIcon,
  Settings as SettingsIcon
} from '@mui/icons-material'
import JournalEntryForm from './components/JournalEntryForm'
import JournalEntriesTable from './components/JournalEntriesTable'
import TAccountsView from './components/TAccountsView'
import BalanceSummary from './components/BalanceSummary'
import AccountManagement from './components/AccountManagement'

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  )
}

function App() {
  const [tabValue, setTabValue] = useState(0)

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue)
  }

  return (
    <div>
      <AppBar position="static" elevation={0}>
        <Toolbar>
          <AccountBalanceIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Double-Entry Bookkeeping Simulator
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 2 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs 
            value={tabValue} 
            onChange={handleTabChange} 
            aria-label="bookkeeping tabs"
            variant="fullWidth"
          >
            <Tab 
              icon={<AddIcon />} 
              label="Add Entry" 
              iconPosition="start"
            />
            <Tab 
              icon={<ListIcon />} 
              label="Journal Entries" 
              iconPosition="start"
            />
            <Tab 
              icon={<AccountBalanceIcon />} 
              label="T-Accounts" 
              iconPosition="start"
            />
            <Tab 
              icon={<AssessmentIcon />} 
              label="Balance Summary" 
              iconPosition="start"
            />
            <Tab 
              icon={<SettingsIcon />} 
              label="Manage Accounts" 
              iconPosition="start"
            />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <JournalEntryForm />
        </TabPanel>
        <TabPanel value={tabValue} index={1}>
          <JournalEntriesTable />
        </TabPanel>
        <TabPanel value={tabValue} index={2}>
          <TAccountsView />
        </TabPanel>
        <TabPanel value={tabValue} index={3}>
          <BalanceSummary />
        </TabPanel>
        <TabPanel value={tabValue} index={4}>
          <AccountManagement />
        </TabPanel>
      </Container>
    </div>
  )
}

export default App 