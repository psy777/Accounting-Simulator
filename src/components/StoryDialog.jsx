import React, { useEffect, useState } from 'react'
import { Snackbar, Alert, Typography } from '@mui/material'
import { useGame } from '../GameContext'

function StoryDialog() {
  const { state, popDialogue } = useGame()
  const [open, setOpen] = useState(false)
  const [message, setMessage] = useState(null)

  useEffect(() => {
    if (state.dialogueQueue && state.dialogueQueue.length > 0 && !message) {
      const next = state.dialogueQueue[0]
      setMessage(next)
      setOpen(true)
      popDialogue()
    }
  }, [state.dialogueQueue, message, popDialogue])

  const handleClose = () => {
    setOpen(false)
    setMessage(null)
  }

  return (
    <Snackbar open={open} onClose={handleClose} anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }} autoHideDuration={8000}>
      <Alert onClose={handleClose} severity="info" sx={{ width: '100%' }}>
        <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
          Shop chatter
        </Typography>
        {message?.text}
      </Alert>
    </Snackbar>
  )
}

export default StoryDialog
