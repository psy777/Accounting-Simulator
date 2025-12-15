import React from 'react'
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
  Chip,
  Box,
  Typography,
} from '@mui/material'
import { useGame } from '../GameContext'

function JournalEntriesTable() {
  const { state } = useGame()
  const entries = state.journalEntries || []

  const formatCurrency = (amount) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount)

  const formatDate = (dateString) =>
    new Date(dateString).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })

  return (
    <Card>
      <CardHeader title="Journal Entries" titleTypographyProps={{ variant: 'h5', fontWeight: 600 }} />
      <CardContent>
        {entries.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="body1" color="text.secondary">
              No journal entries recorded yet. Add an entry to start tracking the music shop finances.
            </Typography>
          </Box>
        ) : (
          <TableContainer component={Paper} elevation={1}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Date</strong></TableCell>
                  <TableCell><strong>Description</strong></TableCell>
                  <TableCell><strong>Debit Account</strong></TableCell>
                  <TableCell><strong>Credit Account</strong></TableCell>
                  <TableCell align="right"><strong>Amount</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {entries
                  .sort((a, b) => new Date(a.date) - new Date(b.date))
                  .map((entry) => (
                    <TableRow key={entry.id}>
                      <TableCell>{formatDate(entry.date)}</TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Chip label={entry.id.slice(0, 6)} size="small" color="default" />
                          {entry.description}
                        </Box>
                      </TableCell>
                      <TableCell>{entry.debitAccount}</TableCell>
                      <TableCell>{entry.creditAccount}</TableCell>
                      <TableCell align="right">{formatCurrency(entry.amount)}</TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </CardContent>
    </Card>
  )
}

export default JournalEntriesTable
