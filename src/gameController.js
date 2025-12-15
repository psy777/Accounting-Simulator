import { DEFAULT_ACCOUNTS, ACCOUNT_TYPES } from './data/accounts'

const STORAGE_KEY = 'music_shop_manager_state'
const SAVE_SLOTS_KEY = 'music_shop_manager_saves'

const DEFAULT_STUDENTS = [
  { id: 'stu-1', name: 'Evelyn Torres', instrument: 'Violin', standing: 'strong', balance: 0 },
  { id: 'stu-2', name: 'Marcus Lee', instrument: 'Piano', standing: 'new', balance: 0 },
  { id: 'stu-3', name: 'Priya Shah', instrument: 'Guitar', standing: 'follow-up', balance: 0 },
]

const DEFAULT_DIALOGUE = [
  {
    id: 'intro-1',
    text: 'Welcome aboard! The band room is a little chaotic, but your ledgers will keep us in tune.',
    mood: 'warm',
  },
  {
    id: 'intro-2',
    text: 'Students pay for lessons weekly. Track invoices, log journal entries, and keep cash flowing.',
    mood: 'helpful',
  },
]

const createBaseState = () => ({
  playerName: '',
  shopName: 'Crescendo Lesson Studio',
  actions: [],
  journalEntries: [],
  accounts: DEFAULT_ACCOUNTS,
  students: DEFAULT_STUDENTS,
  invoices: [],
  dialogueQueue: [...DEFAULT_DIALOGUE],
  currentDate: new Date().toISOString(),
})

class GameController {
  constructor() {
    this.state = this.loadState()
    this.listeners = new Set()
  }

  subscribe(listener) {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  notify() {
    this.saveState()
    this.listeners.forEach((listener) => listener(this.state))
  }

  getState() {
    return this.state
  }

  loadState() {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      try {
        return JSON.parse(stored)
      } catch (error) {
        console.error('Unable to parse saved game state', error)
      }
    }
    return createBaseState()
  }

  saveState() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(this.state))
  }

  startNewGame({ playerName, shopName }) {
    this.state = {
      ...createBaseState(),
      playerName: playerName || 'Bookkeeper',
      shopName: shopName || 'Crescendo Lesson Studio',
    }
    this.recordAction({
      type: 'session',
      summary: `${this.state.playerName} started managing ${this.state.shopName}`,
    })
    this.notify()
  }

  updateName(playerName) {
    this.state.playerName = playerName
    this.recordAction({ type: 'profile', summary: `Updated profile name to ${playerName}` })
    this.notify()
  }

  pushDialogue(text, mood = 'neutral') {
    this.state.dialogueQueue = [...this.state.dialogueQueue, { id: crypto.randomUUID(), text, mood }]
    this.notify()
  }

  popDialogue() {
    const [next, ...rest] = this.state.dialogueQueue
    this.state.dialogueQueue = rest
    return next
  }

  addJournalEntry(entry) {
    const newEntry = {
      ...entry,
      id: entry.id || crypto.randomUUID(),
    }
    this.state.journalEntries = [...this.state.journalEntries, newEntry]
    this.recordAction({
      type: 'journal',
      summary: `${newEntry.description} for $${newEntry.amount.toFixed(2)}`,
      date: newEntry.date,
    })
    this.notify()
  }

  setAccounts(accounts) {
    this.state.accounts = accounts
    this.recordAction({ type: 'accounts', summary: 'Updated chart of accounts' })
    this.notify()
  }

  addInvoice({ studentId, description, amount, dueDate }) {
    const invoice = {
      id: crypto.randomUUID(),
      studentId,
      description,
      amount,
      dueDate,
      status: 'open',
      createdAt: new Date().toISOString(),
    }
    this.state.invoices = [...this.state.invoices, invoice]
    this.recordAction({ type: 'invoice', summary: `Issued invoice to ${studentId} for $${amount}` })
    this.pushDialogue('A new invoice is out. Keep an eye on the receivable!', 'alert')
    this.notify()
  }

  settleInvoice(invoiceId) {
    this.state.invoices = this.state.invoices.map((invoice) =>
      invoice.id === invoiceId ? { ...invoice, status: 'paid', paidAt: new Date().toISOString() } : invoice,
    )
    this.recordAction({ type: 'invoice', summary: `Marked invoice ${invoiceId} as paid` })
    this.notify()
  }

  updateStudentBalance(studentId, delta) {
    this.state.students = this.state.students.map((student) =>
      student.id === studentId ? { ...student, balance: (student.balance || 0) + delta } : student,
    )
    this.notify()
  }

  recordLessonAttendance(studentId, attended) {
    const student = this.state.students.find((s) => s.id === studentId)
    if (!student) return
    const summary = attended
      ? `${student.name} completed a lesson`
      : `${student.name} missed a lesson`
    this.recordAction({ type: 'lesson', summary })
    if (!attended) {
      this.pushDialogue(`${student.name} missed their slot. Should we waive or charge a fee?`, 'concerned')
    }
    this.notify()
  }

  recordAction(action) {
    const stamped = {
      id: crypto.randomUUID(),
      date: action.date || new Date().toISOString(),
      ...action,
    }
    this.state.actions = [...this.state.actions, stamped]
  }

  getAccountBalance(code) {
    const account = this.state.accounts.find((acc) => acc.code === code)
    if (!account) return 0
    const normalSide = account.type === ACCOUNT_TYPES.ASSET || account.type === ACCOUNT_TYPES.EXPENSE ? 'debit' : 'credit'
    let balance = 0
    this.state.journalEntries.forEach((entry) => {
      if (entry.debitAccount === code) {
        balance += normalSide === 'debit' ? entry.amount : -entry.amount
      }
      if (entry.creditAccount === code) {
        balance += normalSide === 'credit' ? entry.amount : -entry.amount
      }
    })
    return balance
  }

  saveSlot(slotName) {
    const slots = this.getSaveSlots()
    const slotData = { ...this.state, savedAt: new Date().toISOString(), slotName }
    localStorage.setItem(`${SAVE_SLOTS_KEY}:${slotName}`, JSON.stringify(slotData))
    const updatedSlots = Array.from(new Set([...slots, slotName]))
    localStorage.setItem(SAVE_SLOTS_KEY, JSON.stringify(updatedSlots))
    this.recordAction({ type: 'save', summary: `Saved progress to slot ${slotName}` })
    this.notify()
  }

  loadSlot(slotName) {
    const stored = localStorage.getItem(`${SAVE_SLOTS_KEY}:${slotName}`)
    if (!stored) return
    try {
      this.state = JSON.parse(stored)
      this.recordAction({ type: 'load', summary: `Loaded progress from ${slotName}` })
      this.notify()
    } catch (error) {
      console.error('Failed to load save slot', error)
    }
  }

  deleteSlot(slotName) {
    localStorage.removeItem(`${SAVE_SLOTS_KEY}:${slotName}`)
    const slots = this.getSaveSlots().filter((slot) => slot !== slotName)
    localStorage.setItem(SAVE_SLOTS_KEY, JSON.stringify(slots))
  }

  getSaveSlots() {
    const stored = localStorage.getItem(SAVE_SLOTS_KEY)
    if (stored) {
      try {
        return JSON.parse(stored)
      } catch (error) {
        console.error('Failed to parse save slot index', error)
      }
    }
    return []
  }
}

export default GameController
