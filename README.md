# Property Rush

Property Rush is a lightweight multiplayer property-trading prototype built with Python, FastAPI, and WebSockets. It is inspired by Monopoly, but sized to stay easy to extend while still feeling recognizably like the real board game.

## What it does

- Multiple players can join the same room from different browser tabs or devices.
- The server owns the game state and enforces turns.
- Players can roll once per turn, buy unowned properties, railroads, and utilities, pay rent, draw cards, visit jail, and go bankrupt.
- The UI updates live for everyone in the room.

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
5. If you land on an unowned property, railroad, or utility and have enough cash, click `Buy Space`.
6. Click `End Turn` to pass control to the next player.

## Current simplifications

- 40 spaces based on the classic Monopoly board
- No auctions, houses, hotels, trading, or save/load yet
- Jail is simplified: you lose one turn and then leave
- Chance and Community Chest are simplified to a smaller card set
- Bankruptcy immediately releases owned properties back to the bank

## Good next steps

- Add trading between players
- Add house and hotel upgrades
- Persist rooms in a database so games survive restarts
- Add reconnection by player token and game lobby screens
