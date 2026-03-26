# Property Rush

Property Rush is a multiplayer Monopoly-style web game built with Python, FastAPI, and WebSockets. It now includes a stronger visual system, richer game feedback, persistent room state, property upgrades, and live player-to-player trading.

## What it does

- Multiple players can join the same room from different browser tabs or devices.
- The server owns the game state and enforces turns.
- Players can claim properties, railroads, and utilities, pay dynamic rent, build houses and hotels, sell property back to the bank, and trade with other players.
- Live game logs, leaderboards, highlighted landings, and property detail modals update for everyone in the room.
- Room state is saved to disk so local restarts do not immediately wipe active games.

## Tech stack

- Python 3.11+
- FastAPI
- Uvicorn
- Plain HTML, CSS, and JavaScript frontend

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000)

## Deploy online with Render

1. Push this project to a GitHub repository.
2. Create a Render account and connect your GitHub account.
3. In Render, create a new `Web Service` from your repository.
4. Render should detect the included [render.yaml](C:\Users\anjli\OneDrive\Documents\New project\render.yaml) automatically.
5. If Render asks for commands manually, use:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Wait for the deploy to finish.
7. Open the public `onrender.com` URL and share it with your friends.

Notes:
- The included [.python-version](C:\Users\anjli\OneDrive\Documents\New project\.python-version) asks Render to use Python 3.13.
- Render supports WebSockets, which this game uses for live multiplayer.
- Render free services can spin down after inactivity, so the first page load after being idle may be slow.

## How to play

1. Open the app in two or more browser tabs.
2. Join the same room name from each tab.
3. The game starts automatically when the second player joins.
4. On your turn, click `Roll Dice`.
5. If you land on an unowned property, railroad, or utility and have enough cash, click `Claim Property`.
6. Open property cards or board tiles to inspect details, build houses, or sell back to the bank.
7. Use the trade desk during your turn to offer property and cash deals to another player.
8. Click `End Turn` to pass control to the next player.

## Current simplifications

- 40 spaces based on the classic Monopoly board
- Houses and hotels are simplified into direct upgrades on owned monopolies
- Jail is simplified: you lose one turn and then leave
- Chance and Community Chest use a smaller curated card set
- Property sales go back to the bank at half value
- AI opponents and long-term account-based persistence are not included yet

## Good next steps

- Add auctions and mortgages
- Add smarter upgrade balancing and even-building rules
- Persist rooms in a database so games survive deploys, not just local restarts
- Add reconnection by player token and game lobby screens
