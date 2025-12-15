import React from 'react'
import { Grid, Card, CardHeader, CardContent, Typography, List, ListItem, ListItemText } from '@mui/material'
import { useGame } from '../GameContext'
import JournalEntryForm from './JournalEntryForm'
import BalanceSummary from './BalanceSummary'

function Dashboard() {
  const { state } = useGame()

  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={5}>
        <JournalEntryForm />
      </Grid>
      <Grid item xs={12} md={7}>
        <BalanceSummary />
      </Grid>
      <Grid item xs={12}>
        <Card>
          <CardHeader title="Recent shop chatter" />
          <CardContent>
            {state.actions.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No actions yet. Start recording lessons and invoices to build the story.
              </Typography>
            ) : (
              <List>
                {[...state.actions].slice(-5).reverse().map((action) => (
                  <ListItem key={action.id}>
                    <ListItemText primary={action.summary} secondary={new Date(action.date).toLocaleString()} />
                  </ListItem>
                ))}
              </List>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  )
}

export default Dashboard
