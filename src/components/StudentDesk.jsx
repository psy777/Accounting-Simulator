import React from 'react'
import { Card, CardHeader, CardContent, Table, TableHead, TableRow, TableCell, TableBody, Button, Stack, Typography } from '@mui/material'
import { useGame } from '../GameContext'

function StudentDesk() {
  const { state, addInvoice, settleInvoice, recordLessonAttendance } = useGame()

  const handleIssueInvoice = (studentId) => {
    const description = 'Weekly lesson invoice'
    const amount = 75
    const dueDate = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)
    addInvoice({ studentId, description, amount, dueDate })
  }

  const handlePay = (invoiceId) => {
    settleInvoice(invoiceId)
  }

  const openInvoices = state.invoices.filter((invoice) => invoice.status === 'open')

  return (
    <Card>
      <CardHeader title="Student Desk" subheader="Log attendance, bill lessons, and collect receipts." />
      <CardContent>
        <Typography variant="subtitle2" sx={{ mb: 1 }}>
          Students
        </Typography>
        <Table size="small" sx={{ mb: 3 }}>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Instrument</TableCell>
              <TableCell>Standing</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {state.students.map((student) => (
              <TableRow key={student.id}>
                <TableCell>{student.name}</TableCell>
                <TableCell>{student.instrument}</TableCell>
                <TableCell>{student.standing}</TableCell>
                <TableCell align="right">
                  <Stack direction="row" spacing={1} justifyContent="flex-end">
                    <Button size="small" onClick={() => recordLessonAttendance(student.id, true)}>
                      Attended
                    </Button>
                    <Button size="small" onClick={() => recordLessonAttendance(student.id, false)} color="warning">
                      Missed
                    </Button>
                    <Button size="small" onClick={() => handleIssueInvoice(student.id)} color="primary" variant="outlined">
                      Invoice
                    </Button>
                  </Stack>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        <Typography variant="subtitle2" sx={{ mb: 1 }}>
          Open invoices
        </Typography>
        {openInvoices.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            All caught up on billing.
          </Typography>
        ) : (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Student</TableCell>
                <TableCell>Description</TableCell>
                <TableCell>Amount</TableCell>
                <TableCell>Due</TableCell>
                <TableCell align="right">Action</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {openInvoices.map((invoice) => {
                const student = state.students.find((s) => s.id === invoice.studentId)
                return (
                  <TableRow key={invoice.id}>
                    <TableCell>{student?.name || invoice.studentId}</TableCell>
                    <TableCell>{invoice.description}</TableCell>
                    <TableCell>${invoice.amount.toFixed(2)}</TableCell>
                    <TableCell>{invoice.dueDate}</TableCell>
                    <TableCell align="right">
                      <Button size="small" onClick={() => handlePay(invoice.id)} variant="contained">
                        Mark paid
                      </Button>
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  )
}

export default StudentDesk
