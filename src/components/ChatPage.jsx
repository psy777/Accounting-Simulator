import React, { useState } from 'react'
import { Card, CardHeader, CardContent, TextField, Button, Stack, Typography, Paper } from '@mui/material'
import { useGame } from '../GameContext'

async function callOllama(prompt) {
  try {
    const response = await fetch('http://localhost:11434/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: 'llama3', prompt }),
    })
    if (!response.ok) throw new Error('Chat request failed')
    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let result = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      result += decoder.decode(value)
    }
    return result
  } catch (error) {
    return `Unable to reach Ollama: ${error.message}`
  }
}

function ChatPage() {
  const { state } = useGame()
  const [messages, setMessages] = useState([
    {
      role: 'system',
      text: 'You are a mentor helping a bookkeeper make sense of lesson invoices, journal entries, and student conversations.',
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSend = async () => {
    if (!input.trim()) return
    const userMessage = { role: 'user', text: input.trim() }
    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)
    const financialSummary = `You are talking to ${state.playerName || 'a bookkeeper'} at ${state.shopName}. There are ${
      state.journalEntries.length
    } journal entries and ${state.invoices.length} invoices.`
    const response = await callOllama(`${financialSummary}\n\n${userMessage.text}`)
    setMessages((prev) => [...prev, { role: 'assistant', text: response }])
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
