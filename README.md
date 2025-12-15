# Accounting Simulator — Music Shop Story

This simulator blends double-entry bookkeeping tools with a light narrative about being a bookkeeper hired by a neighborhood music studio. Use the tabs to set up the company, log journal entries, issue lesson invoices, and chat with an Ollama model to practice customer interactions.

## Getting started

1. Install dependencies and run the dev server:

```bash
npm install
npm run dev
```

2. Open the app in your browser (Vite will print the URL). Start on **Game setup** to choose your name and studio title.

3. Use **Students** to mark attendance and issue weekly lesson invoices. The **Dashboard**, **Journal**, **T-Accounts**, and **Accounts** tabs keep the books balanced.

4. **Ollama chat** calls a local Ollama instance at `http://localhost:11434/api/generate`. Update the endpoint or model name in `src/components/ChatPage.jsx` if you host Ollama elsewhere.

5. Snapshot or restore progress in **Saves**. Saves live in the browser and include your ledger, invoices, and story actions.

## How to extend

- **Add more story beats:** push custom dialogue into the queue by calling `pushDialogue` from any component or by expanding the defaults in `src/gameController.js`.
- **Customize lesson pricing:** adjust the invoice amount in `StudentDesk` or add controls to collect different lesson lengths.
- **Refine accounts:** edit the default chart in `src/data/accounts.js` to match your studio’s real accounts.
- **Deeper customer logic:** attach more metadata to students in `DEFAULT_STUDENTS` (e.g., preferred contact method) and surface it in `StudentDesk`.
- **Integrate a backend:** swap the localStorage persistence in `gameController.js` for API calls if you want multi-user saves.

## Notes

- The game controller (`src/gameController.js`) is the source of truth for accounts, journal entries, invoices, dialogue, and save slots. Components read state through `GameContext`.
- Journal entries, invoices, and lesson actions automatically log to the action history, which feeds the recent chatter on the dashboard and triggers occasional dialogue pop-ups.
