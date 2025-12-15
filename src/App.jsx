import React, { useState } from 'react'
import { AppBar, Toolbar, Typography, Container, Tabs, Tab, Box, Grid } from '@mui/material'
import SchoolIcon from '@mui/icons-material/School'
import ChatIcon from '@mui/icons-material/Chat'
import SaveIcon from '@mui/icons-material/Save'
import LibraryBooksIcon from '@mui/icons-material/LibraryBooks'
import PeopleIcon from '@mui/icons-material/People'
import PaymentIcon from '@mui/icons-material/Payment'
import Dashboard from './components/Dashboard'
import JournalEntriesTable from './components/JournalEntriesTable'
import TAccountsView from './components/TAccountsView'
import AccountManagement from './components/AccountManagement'
import ChatPage from './components/ChatPage'
import GameSetup from './components/GameSetup'
import GameSaves from './components/GameSaves'
import StudentDesk from './components/StudentDesk'
import StoryDialog from './components/StoryDialog'
import Payments from './components/Payments'
import { useGame } from './GameContext'

function TabPanel({ children, value, index }) {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  )
}

function App() {
  const { state } = useGame()
  const [tabValue, setTabValue] = useState(0)

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue)
  }

  return (
    <div>
      <AppBar position="static" elevation={0}>
        <Toolbar>
          <SchoolIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            {state.shopName} · Bookkeeper: {state.playerName || 'Set your name in Game setup'}
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 2 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="bookkeeping tabs" variant="scrollable">
            <Tab icon={<LibraryBooksIcon />} label="Game setup" iconPosition="start" />
            <Tab icon={<PeopleIcon />} label="Students" iconPosition="start" />
            <Tab icon={<LibraryBooksIcon />} label="Dashboard" iconPosition="start" />
            <Tab icon={<LibraryBooksIcon />} label="Journal" iconPosition="start" />
            <Tab icon={<LibraryBooksIcon />} label="T-Accounts" iconPosition="start" />
            <Tab icon={<LibraryBooksIcon />} label="Accounts" iconPosition="start" />
            <Tab icon={<PaymentIcon />} label="Payments" iconPosition="start" />
            <Tab icon={<ChatIcon />} label="Ollama chat" iconPosition="start" />
            <Tab icon={<SaveIcon />} label="Saves" iconPosition="start" />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <GameSetup />
        </TabPanel>
        <TabPanel value={tabValue} index={1}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <StudentDesk />
            </Grid>
            <Grid item xs={12} md={6}>
              <JournalEntriesTable />
            </Grid>
          </Grid>
        </TabPanel>
        <TabPanel value={tabValue} index={2}>
          <Dashboard />
        </TabPanel>
        <TabPanel value={tabValue} index={3}>
          <JournalEntriesTable />
        </TabPanel>
        <TabPanel value={tabValue} index={4}>
          <TAccountsView />
        </TabPanel>
        <TabPanel value={tabValue} index={5}>
          <AccountManagement />
        </TabPanel>
        <TabPanel value={tabValue} index={6}>
          <Payments />
        </TabPanel>
        <TabPanel value={tabValue} index={7}>
          <ChatPage />
        </TabPanel>
        <TabPanel value={tabValue} index={8}>
          <GameSaves />
        </TabPanel>
      </Container>

      <StoryDialog />
    </div>
  )
}

export default App
