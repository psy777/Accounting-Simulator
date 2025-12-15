import React from 'react'
import {
  Card,
  CardHeader,
  CardContent,
  Grid,
  Typography,
  Stack,
  Button,
  Chip,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Box,
  Paper,
} from '@mui/material'
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong'
import PaidIcon from '@mui/icons-material/Paid'
import { useGame } from '../GameContext'

function InvoiceCard({ invoice, student, onPay }) {
  const total = invoice.lineItems?.reduce((sum, item) => sum + item.amount, 0) || invoice.amount
  return (
    <Card variant="outlined" sx={{ height: '100%' }}>
      <CardContent>
        <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1 }}>
          <Stack direction="row" spacing={1} alignItems="center">
            <ReceiptLongIcon color="primary" />
            <Box>
              <Typography variant="subtitle2">{invoice.description || 'Lesson Invoice'}</Typography>
              <Typography variant="caption" color="text.secondary">
                Invoice #{invoice.id.slice(0, 8)} · Due {invoice.dueDate}
              </Typography>
            </Box>
          </Stack>
          <Chip label={invoice.status.toUpperCase()} color={invoice.status === 'paid' ? 'success' : 'warning'} size="small" />
        </Stack>

        <Box sx={{ border: '1px dashed', borderColor: 'divider', p: 1.5, borderRadius: 1, mb: 2 }}>
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            Billed To
          </Typography>
          <Typography variant="body2">{student?.name || 'New customer'}</Typography>
          <Typography variant="caption" color="text.secondary">
            {student?.instrument ? `${student.instrument} lessons` : 'Music studio client'}
          </Typography>
        </Box>

        <Table size="small" sx={{ mb: 2 }}>
          <TableHead>
            <TableRow>
              <TableCell>Description</TableCell>
              <TableCell align="right">Amount</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {(invoice.lineItems || [{ id: 'single', label: invoice.description, amount: invoice.amount }]).map((item) => (
              <TableRow key={item.id}>
                <TableCell>{item.label}</TableCell>
                <TableCell align="right">${item.amount.toFixed(2)}</TableCell>
              </TableRow>
            ))}
            <TableRow>
              <TableCell sx={{ fontWeight: 700 }}>Total Due</TableCell>
              <TableCell align="right" sx={{ fontWeight: 700 }}>
                ${total.toFixed(2)}
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>

        {invoice.status !== 'paid' && (
          <Button fullWidth variant="contained" onClick={onPay} startIcon={<PaidIcon />}>Mark as paid</Button>
        )}
        {invoice.status === 'paid' && (
          <Typography variant="caption" color="text.secondary">
            Paid on {invoice.paidAt?.slice(0, 10) || 'today'}
          </Typography>
        )}
      </CardContent>
    </Card>
  )
}

function Payments() {
  const { state, recordPayment } = useGame()
  const openInvoices = state.invoices.filter((inv) => inv.status === 'open')
  const settledInvoices = state.invoices.filter((inv) => inv.status === 'paid')

  const handlePay = (invoice) => {
    recordPayment({ invoiceId: invoice.id, amount: invoice.amount, method: 'Manual payment' })
  }

  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={8}>
        <Card>
          <CardHeader title="Invoices" subheader="Styled PDFs on the fly—track who owes what at a glance." />
          <CardContent>
            {openInvoices.length === 0 && settledInvoices.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No invoices yet—issue some from the student desk or by chatting with your boss.
              </Typography>
            ) : (
              <Grid container spacing={2}>
                {openInvoices.map((invoice) => (
                  <Grid item xs={12} md={6} key={invoice.id}>
                    <InvoiceCard invoice={invoice} student={state.students.find((s) => s.id === invoice.studentId)} onPay={() => handlePay(invoice)} />
                  </Grid>
                ))}
                {settledInvoices.map((invoice) => (
                  <Grid item xs={12} md={6} key={invoice.id}>
                    <InvoiceCard invoice={invoice} student={state.students.find((s) => s.id === invoice.studentId)} onPay={() => {}} />
                  </Grid>
                ))}
              </Grid>
            )}
          </CardContent>
        </Card>
      </Grid>
      <Grid item xs={12} md={4}>
        <Card variant="outlined">
          <CardHeader title="Payments" subheader="Receipts and banking log" />
          <CardContent>
            {state.payments.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                Payments will land here once you mark invoices as paid.
              </Typography>
            ) : (
              <Stack spacing={1}>
                {state.payments
                  .slice()
                  .reverse()
                  .map((payment) => {
                    const invoice = state.invoices.find((inv) => inv.id === payment.invoiceId)
                    const student = state.students.find((s) => s.id === invoice?.studentId)
                    return (
                      <Paper key={payment.id} variant="outlined" sx={{ p: 1.5 }}>
                        <Stack direction="row" justifyContent="space-between" alignItems="center">
                          <Box>
                            <Typography variant="subtitle2">${payment.amount.toFixed(2)}</Typography>
                            <Typography variant="caption" color="text.secondary">
                              {student?.name || 'Unassigned customer'} · Invoice {payment.invoiceId.slice(0, 6)}
                            </Typography>
                          </Box>
                          <Chip label={payment.method} size="small" />
                        </Stack>
                        <Typography variant="caption" color="text.secondary">
                          Received {payment.paidAt.slice(0, 10)} {payment.memo ? `· ${payment.memo}` : ''}
                        </Typography>
                      </Paper>
                    )
                  })}
              </Stack>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  )
}

export default Payments
