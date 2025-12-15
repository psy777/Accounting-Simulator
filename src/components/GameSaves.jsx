import React, { useState, useEffect } from 'react'
import { Card, CardHeader, CardContent, List, ListItem, ListItemText, Button, Stack, TextField, Typography } from '@mui/material'
import { useGame } from '../GameContext'

function GameSaves() {
  const { controller, saveSlot, loadSlot, deleteSlot } = useGame()
  const [slots, setSlots] = useState([])
  const [slotName, setSlotName] = useState('')

  const refresh = () => setSlots(controller.getSaveSlots())

  useEffect(() => {
    refresh()
  }, [])

  const handleSave = () => {
    if (!slotName.trim()) return
    saveSlot(slotName.trim())
    refresh()
    setSlotName('')
  }

  return (
    <Card>
      <CardHeader title="Game setup & saves" subheader="Snapshot your work or return to an earlier session." />
      <CardContent>
        <Stack spacing={2}>
          <Stack direction="row" spacing={2}>
            <TextField label="Save slot name" value={slotName} onChange={(e) => setSlotName(e.target.value)} fullWidth />
            <Button variant="contained" onClick={handleSave}>
              Save
            </Button>
          </Stack>
          <Typography variant="subtitle2">Saved slots</Typography>
          {slots.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No saves yet. Create one before trying risky accounting experiments.
            </Typography>
          ) : (
            <List>
              {slots.map((slot) => (
                <ListItem key={slot} secondaryAction={<Button onClick={() => deleteSlot(slot)}>Delete</Button>}>
                  <ListItemText
                    primary={slot}
                    secondary={
                      <Stack direction="row" spacing={1}>
                        <Button size="small" onClick={() => loadSlot(slot)}>
                          Load
                        </Button>
                      </Stack>
                    }
                  />
                </ListItem>
              ))}
            </List>
          )}
        </Stack>
      </CardContent>
    </Card>
  )
}

export default GameSaves
