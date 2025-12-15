import React, { createContext, useContext, useMemo, useState, useEffect } from 'react'
import GameController from './gameController'

const GameContext = createContext(null)

export function GameProvider({ children }) {
  const [controller] = useState(() => new GameController())
  const [state, setState] = useState(controller.getState())

  useEffect(() => {
    return controller.subscribe(setState)
  }, [controller])

  const value = useMemo(
    () => ({
      controller,
      state,
      startNewGame: controller.startNewGame.bind(controller),
      addJournalEntry: controller.addJournalEntry.bind(controller),
      setAccounts: controller.setAccounts.bind(controller),
      pushDialogue: controller.pushDialogue.bind(controller),
      popDialogue: controller.popDialogue.bind(controller),
      addInvoice: controller.addInvoice.bind(controller),
      settleInvoice: controller.settleInvoice.bind(controller),
      recordPayment: controller.recordPayment.bind(controller),
      addStudent: controller.addStudent.bind(controller),
      recordLessonAttendance: controller.recordLessonAttendance.bind(controller),
      updateStudentBalance: controller.updateStudentBalance.bind(controller),
      saveSlot: controller.saveSlot.bind(controller),
      loadSlot: controller.loadSlot.bind(controller),
      deleteSlot: controller.deleteSlot.bind(controller),
    }),
    [controller, state],
  )

  return <GameContext.Provider value={value}>{children}</GameContext.Provider>
}

export const useGame = () => {
  const ctx = useContext(GameContext)
  if (!ctx) throw new Error('useGame must be used within GameProvider')
  return ctx
}
