import React, { useState } from 'react'
import { Card, CardHeader, CardContent, TextField, Button, Stack, Typography } from '@mui/material'
import { useGame } from '../GameContext'

function GameSetup() {
  const { startNewGame } = useGame()
  const [playerName, setPlayerName] = useState('')
  const [shopName, setShopName] = useState('Crescendo Lesson Studio')

  const handleStart = () => {
    startNewGame({ playerName, shopName })
  }

  return (
    <Card>
      <CardHeader title="New Engagement" subheader="Name yourself and the studio before meeting students." />
      <CardContent>
        <Stack spacing={2}>
          <Typography variant="body2" color="text.secondary">
            You have been hired to clean up the lesson books for a bustling music shop. Choose your name and the studio label that
            will appear on invoices and journal entries.
          </Typography>
          <TextField label="Your name" value={playerName} onChange={(e) => setPlayerName(e.target.value)} fullWidth />
          <TextField label="Studio or shop name" value={shopName} onChange={(e) => setShopName(e.target.value)} fullWidth />
          <Button variant="contained" onClick={handleStart}>
            Start engagement
          </Button>
        </Stack>
      </CardContent>
    </Card>
  )
}

export default GameSetup
