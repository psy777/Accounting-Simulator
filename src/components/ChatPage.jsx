import React, { useState } from 'react'
import {
  Card,
  CardHeader,
  CardContent,
  TextField,
  Button,
  Stack,
  Typography,
  Paper,
  Chip,
  Divider,
} from '@mui/material'
import { useGame } from '../GameContext'

async function callOllama(messages) {
  try {
    const response = await fetch('http://localhost:11434/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: 'llama3', messages }),
    })
    if (!response.ok) throw new Error('Chat request failed')
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''
    let fullText = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (!line.trim()) continue
        try {
          const parsed = JSON.parse(line)
          if (parsed.message?.content) {
            fullText += parsed.message.content
          }
        } catch (error) {
          console.error('Unable to parse Ollama stream chunk', error)
        }
      }
    }
    return fullText || 'The mentor pauses, waiting for you to try again.'
  } catch (error) {
    return `Unable to reach Ollama: ${error.message}`
  }
}

const STUDENT_NAME_BANK = ['Ava Brooks', 'Jonas Wilder', 'Kai Chen', 'Lena Patel', 'Mateo Alvarez']
const INSTRUMENT_BANK = ['Violin', 'Piano', 'Guitar', 'Drums', 'Voice']

function pickRandom(list) {
  return list[Math.floor(Math.random() * list.length)]
}

function buildSystemPrompt(state) {
  const openInvoices = state.invoices.filter((inv) => inv.status === 'open')
  return {
    role: 'system',
    content:
      `You are the pragmatic boss of ${state.shopName}. ` +
      'Give concise answers and actionable bookkeeping guidance. When the user brings up advertising, follow up on lead generation and issuing invoices.',
    game_state: {
      playerName: state.playerName,
      shopName: state.shopName,
      openInvoices: openInvoices.length,
      students: state.students.length,
    },
  }
}

function applyConversationConsequences(text, controller, state) {
  const normalized = text.toLowerCase()
  const consequences = []

  if (normalized.includes('advertising') || normalized.includes('marketing') || normalized.includes('flyer')) {
    const newStudent = controller.addStudent({ name: pickRandom(STUDENT_NAME_BANK), instrument: pickRandom(INSTRUMENT_BANK) })
    const dueDate = new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)
    controller.addInvoice({
      studentId: newStudent.id,
      description: 'Intro lesson package (ad lead)',
      amount: 120,
      dueDate,
    })
    controller.addInvoice({
      studentId: 'marketing-team',
      description: 'Advertising blast with posters and social ads',
      amount: 180,
      dueDate,
    })
    consequences.push('Your boss approved an advertising blast and the campaign attracted a brand new student.')
  }

  if (normalized.includes('new lesson') || normalized.includes('more students') || normalized.includes('new customers')) {
    const newStudent = controller.addStudent({
      name: pickRandom(STUDENT_NAME_BANK),
      instrument: pickRandom(INSTRUMENT_BANK),
      standing: 'trial',
    })
    const dueDate = new Date(Date.now() + 3 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)
    controller.addInvoice({
      studentId: newStudent.id,
      description: 'Trial lesson pack',
      amount: 90,
      dueDate,
    })
    consequences.push(`A new lead named ${newStudent.name} booked a trial. An invoice was generated.`)
  }

  if (normalized.includes('pay') || normalized.includes('collect') || normalized.includes('payment')) {
    const oldestInvoice = state.invoices.find((inv) => inv.status === 'open')
    if (oldestInvoice) {
      controller.recordPayment({ invoiceId: oldestInvoice.id, amount: oldestInvoice.amount, method: 'Chat follow-up' })
      consequences.push('A payment was collected on the oldest open invoice while you were chatting.')
    }
  }

  return consequences
}

function ChatPage() {
  const { state, controller } = useGame()
  const [messages, setMessages] = useState([
    { role: 'assistant', text: 'Boss here—keep me posted on lessons, invoices, and marketing ideas.' },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [actionNotes, setActionNotes] = useState([])

  const handleSend = async () => {
    if (!input.trim()) return
    const userMessage = { role: 'user', text: input.trim() }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)

    const promptMessages = [buildSystemPrompt(state), ...messages.map((m) => ({ role: m.role, content: m.text })), { role: 'user', content: userMessage.text }]
    const response = await callOllama(promptMessages)
    setMessages((prev) => [...prev, { role: 'assistant', text: response }])

    const consequences = applyConversationConsequences(userMessage.text, controller, state)
    if (consequences.length) {
      setActionNotes((prev) => [...consequences, ...prev].slice(0, 5))
    }
    setLoading(false)
  }

  return (
    <Card>
      <CardHeader title="Practice with Customers (Ollama Chat)" subheader="Use a local Ollama model for narrative interactions." />
      <CardContent>
        <Stack spacing={2}>
          <Paper variant="outlined" sx={{ p: 2, maxHeight: 360, overflow: 'auto' }}>
            {messages.map((msg, index) => (
              <Typography key={index} variant="body2" sx={{ mb: 1 }} color={msg.role === 'assistant' ? 'primary' : 'text.primary'}>
                <strong>{msg.role}:</strong> {msg.text}
              </Typography>
            ))}
          </Paper>
          {actionNotes.length > 0 && (
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                <Chip label="Game actions" size="small" color="success" />
                <Typography variant="body2" color="text.secondary">
                  Conversations now trigger bookkeeping moves automatically.
                </Typography>
              </Stack>
              <Divider sx={{ mb: 1 }} />
              {actionNotes.map((note, idx) => (
                <Typography key={idx} variant="body2" sx={{ mb: 0.5 }}>
                  • {note}
                </Typography>
              ))}
            </Paper>
          )}
          <Stack direction="row" spacing={2}>
            <TextField
              fullWidth
              placeholder="Ask about a student invoice or how to record a transaction"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={loading}
            />
            <Button onClick={handleSend} variant="contained" disabled={loading}>
              {loading ? 'Thinking...' : 'Send'}
            </Button>
          </Stack>
        </Stack>
      </CardContent>
    </Card>
  )
}

export default ChatPage
