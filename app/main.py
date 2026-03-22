import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

BOARD = [
    {"name": "Go", "type": "go"},
    {"name": "Mediterranean Avenue", "type": "property", "price": 60, "rent": 2, "color": "brown"},
    {"name": "Community Chest", "type": "chest"},
    {"name": "Baltic Avenue", "type": "property", "price": 60, "rent": 4, "color": "brown"},
    {"name": "Income Tax", "type": "tax", "amount": 200},
    {"name": "Reading Railroad", "type": "railroad", "price": 200},
    {"name": "Oriental Avenue", "type": "property", "price": 100, "rent": 6, "color": "light-blue"},
    {"name": "Chance", "type": "chance"},
    {"name": "Vermont Avenue", "type": "property", "price": 100, "rent": 6, "color": "light-blue"},
    {"name": "Connecticut Avenue", "type": "property", "price": 120, "rent": 8, "color": "light-blue"},
    {"name": "Jail / Just Visiting", "type": "jail"},
    {"name": "St. Charles Place", "type": "property", "price": 140, "rent": 10, "color": "pink"},
    {"name": "Electric Company", "type": "utility", "price": 150},
    {"name": "States Avenue", "type": "property", "price": 140, "rent": 10, "color": "pink"},
    {"name": "Virginia Avenue", "type": "property", "price": 160, "rent": 12, "color": "pink"},
    {"name": "Pennsylvania Railroad", "type": "railroad", "price": 200},
    {"name": "St. James Place", "type": "property", "price": 180, "rent": 14, "color": "orange"},
    {"name": "Community Chest", "type": "chest"},
    {"name": "Tennessee Avenue", "type": "property", "price": 180, "rent": 14, "color": "orange"},
    {"name": "New York Avenue", "type": "property", "price": 200, "rent": 16, "color": "orange"},
    {"name": "Free Parking", "type": "parking"},
    {"name": "Kentucky Avenue", "type": "property", "price": 220, "rent": 18, "color": "red"},
    {"name": "Chance", "type": "chance"},
    {"name": "Indiana Avenue", "type": "property", "price": 220, "rent": 18, "color": "red"},
    {"name": "Illinois Avenue", "type": "property", "price": 240, "rent": 20, "color": "red"},
    {"name": "B. & O. Railroad", "type": "railroad", "price": 200},
    {"name": "Atlantic Avenue", "type": "property", "price": 260, "rent": 22, "color": "yellow"},
    {"name": "Ventnor Avenue", "type": "property", "price": 260, "rent": 22, "color": "yellow"},
    {"name": "Water Works", "type": "utility", "price": 150},
    {"name": "Marvin Gardens", "type": "property", "price": 280, "rent": 24, "color": "yellow"},
    {"name": "Go To Jail", "type": "go_to_jail"},
    {"name": "Pacific Avenue", "type": "property", "price": 300, "rent": 26, "color": "green"},
    {"name": "North Carolina Avenue", "type": "property", "price": 300, "rent": 26, "color": "green"},
    {"name": "Community Chest", "type": "chest"},
    {"name": "Pennsylvania Avenue", "type": "property", "price": 320, "rent": 28, "color": "green"},
    {"name": "Short Line", "type": "railroad", "price": 200},
    {"name": "Chance", "type": "chance"},
    {"name": "Park Place", "type": "property", "price": 350, "rent": 35, "color": "dark-blue"},
    {"name": "Luxury Tax", "type": "tax", "amount": 100},
    {"name": "Boardwalk", "type": "property", "price": 400, "rent": 50, "color": "dark-blue"},
]

GO_MONEY = 200
JAIL_INDEX = 10

CHANCE_CARDS = [
    {"text": "Advance to Go", "move_to": 0},
    {"text": "Advance to Illinois Avenue", "move_to": 24},
    {"text": "Go to St. Charles Place", "move_to": 11},
    {"text": "Bank pays you dividend of 50", "money": 50},
    {"text": "Pay poor tax of 15", "money": -15},
    {"text": "Go to Jail", "go_to_jail": True},
]

COMMUNITY_CARDS = [
    {"text": "Advance to Go", "move_to": 0},
    {"text": "Bank error in your favor. Collect 200", "money": 200},
    {"text": "Doctor's fees. Pay 50", "money": -50},
    {"text": "From sale of stock you get 50", "money": 50},
    {"text": "Pay hospital fees of 100", "money": -100},
    {"text": "You inherit 100", "money": 100},
]

COLOR_CLASSES = {
    "brown": "#8b5a2b",
    "light-blue": "#84d7f7",
    "pink": "#d969b5",
    "orange": "#f2a23a",
    "red": "#d74c4c",
    "yellow": "#f2d13d",
    "green": "#2b8b57",
    "dark-blue": "#3158aa",
}


def serialize_player(player: "Player") -> dict[str, Any]:
    return {
        "id": player.id,
        "name": player.name,
        "money": player.money,
        "position": player.position,
        "properties": player.properties,
        "bankrupt": player.bankrupt,
        "connected": player.connected,
        "inJail": player.in_jail,
        "hasRolled": player.has_rolled,
    }


@dataclass
class Player:
    id: str
    name: str
    money: int = 1500
    position: int = 0
    properties: list[int] = field(default_factory=list)
    bankrupt: bool = False
    connected: bool = True
    in_jail: bool = False
    has_rolled: bool = False


class GameRoom:
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.players: dict[str, Player] = {}
        self.connections: dict[str, WebSocket] = {}
        self.property_owner: dict[int, str] = {}
        self.turn_order: list[str] = []
        self.current_turn_index = 0
        self.started = False
        self.last_roll: tuple[int, int] | None = None
        self.last_roll_total = 0
        self.last_message = "Waiting for at least 2 players."

    def add_player(self, player_id: str, name: str, websocket: WebSocket) -> Player:
        if player_id in self.players:
            player = self.players[player_id]
            player.name = name
            player.connected = True
        else:
            player = Player(id=player_id, name=name)
            self.players[player_id] = player
            self.turn_order.append(player_id)
        self.connections[player_id] = websocket
        self.last_message = f"{player.name} joined room {self.room_id}."
        return player

    def remove_player(self, player_id: str) -> None:
        self.connections.pop(player_id, None)
        if player_id in self.players:
            self.players[player_id].connected = False
            self.last_message = f"{self.players[player_id].name} disconnected."

    @property
    def current_player(self) -> Player | None:
        if not self.turn_order:
            return None
        return self.players[self.turn_order[self.current_turn_index]]

    def ensure_started(self) -> None:
        if not self.started and len(self.turn_order) >= 2:
            self.started = True
            self.current_player.has_rolled = False
            self.last_message = f"Game started. {self.current_player.name} goes first."

    def winner_name(self) -> str | None:
        solvent = [player for player in self.players.values() if not player.bankrupt]
        if self.started and len(solvent) == 1 and len(self.players) > 1:
            return solvent[0].name
        return None

    def can_buy_current_space(self, player: Player) -> bool:
        space = BOARD[player.position]
        return (
            space["type"] in {"property", "railroad", "utility"}
            and player.position not in self.property_owner
            and player.money >= space["price"]
            and player.has_rolled
            and not player.bankrupt
        )

    def state(self, player_id: str | None = None) -> dict[str, Any]:
        current = self.current_player
        me = self.players.get(player_id) if player_id else None
        return {
            "type": "state",
            "roomId": self.room_id,
            "started": self.started,
            "players": [serialize_player(self.players[pid]) for pid in self.turn_order],
            "propertyOwners": self.property_owner,
            "currentTurn": current.id if current else None,
            "currentTurnName": current.name if current else None,
            "board": BOARD,
            "lastRoll": self.last_roll,
            "lastMessage": self.last_message,
            "you": player_id,
            "winner": self.winner_name(),
            "canBuy": self.can_buy_current_space(me) if me else False,
        }

    def next_turn(self) -> None:
        if not self.turn_order:
            return
        for _ in range(len(self.turn_order)):
            self.current_turn_index = (self.current_turn_index + 1) % len(self.turn_order)
            player = self.players[self.turn_order[self.current_turn_index]]
            if not player.bankrupt:
                player.has_rolled = False
                break
        self.last_roll = None
        self.last_roll_total = 0
        self.last_message = f"{self.current_player.name}'s turn."

    def send_to_jail(self, player: Player) -> None:
        player.position = JAIL_INDEX
        player.in_jail = True
        player.has_rolled = True
        self.last_message = f"{player.name} was sent to jail."

    def move_player(self, player: Player, target: int) -> None:
        if target < player.position:
            player.money += GO_MONEY
        player.position = target

    def handle_roll(self, player_id: str) -> None:
        self.ensure_started()
        if not self.started:
            self.last_message = "Need at least 2 players to start."
            return
        if self.current_player is None or self.current_player.id != player_id:
            self.last_message = "It is not your turn."
            return

        player = self.players[player_id]
        if player.bankrupt:
            self.last_message = f"{player.name} is bankrupt and cannot play."
            return
        if player.has_rolled:
            self.last_message = "You already rolled this turn."
            return

        player.has_rolled = True

        if player.in_jail:
            player.in_jail = False
            self.last_roll = None
            self.last_roll_total = 0
            self.last_message = f"{player.name} used their turn to leave jail."
            return

        die_one = random.randint(1, 6)
        die_two = random.randint(1, 6)
        total = die_one + die_two
        self.last_roll = (die_one, die_two)
        self.last_roll_total = total
        old_position = player.position
        player.position = (player.position + total) % len(BOARD)
        if player.position < old_position:
            player.money += GO_MONEY
        self.resolve_landing(player)

    def resolve_landing(self, player: Player) -> None:
        space = BOARD[player.position]
        base_message = f"{player.name} landed on {space['name']}."
        if space["type"] == "property":
            owner_id = self.property_owner.get(player.position)
            if owner_id and owner_id != player.id:
                rent = space["rent"]
                owner = self.players[owner_id]
                player.money -= rent
                owner.money += rent
                self.last_message = f"{player.name} paid {rent} rent to {owner.name}."
            elif owner_id == player.id:
                self.last_message = f"{player.name} landed on their own property."
            else:
                self.last_message = f"{base_message} It is available for {space['price']}."
        elif space["type"] == "railroad":
            owner_id = self.property_owner.get(player.position)
            if owner_id and owner_id != player.id:
                owner = self.players[owner_id]
                rent = self.railroad_rent(owner_id)
                player.money -= rent
                owner.money += rent
                self.last_message = f"{player.name} paid railroad rent of {rent} to {owner.name}."
            elif owner_id == player.id:
                self.last_message = f"{player.name} landed on their own railroad."
            else:
                self.last_message = f"{base_message} It is available for {space['price']}."
        elif space["type"] == "utility":
            owner_id = self.property_owner.get(player.position)
            if owner_id and owner_id != player.id:
                owner = self.players[owner_id]
                rent = self.utility_rent(owner_id)
                player.money -= rent
                owner.money += rent
                self.last_message = f"{player.name} paid utility rent of {rent} to {owner.name}."
            elif owner_id == player.id:
                self.last_message = f"{player.name} landed on their own utility."
            else:
                self.last_message = f"{base_message} It is available for {space['price']}."
        elif space["type"] == "tax":
            amount = space["amount"]
            player.money -= amount
            self.last_message = f"{player.name} paid tax of {amount}."
        elif space["type"] == "chance":
            self.apply_card(player, random.choice(CHANCE_CARDS), "Chance")
        elif space["type"] == "chest":
            self.apply_card(player, random.choice(COMMUNITY_CARDS), "Community Chest")
        elif space["type"] == "go_to_jail":
            self.send_to_jail(player)
        else:
            self.last_message = base_message
        self.check_bankruptcy(player)

    def apply_card(self, player: Player, card: dict[str, Any], deck_name: str) -> None:
        message = f"{player.name} drew {deck_name}: {card['text']}."
        if "money" in card:
            player.money += card["money"]
        if card.get("go_to_jail"):
            self.send_to_jail(player)
            self.last_message = f"{message} They were sent to jail."
            return
        if "move_to" in card:
            self.move_player(player, card["move_to"])
            self.last_message = message
            self.resolve_landing(player)
            return
        self.last_message = message

    def railroad_rent(self, owner_id: str) -> int:
        owned = sum(
            1
            for position, holder in self.property_owner.items()
            if holder == owner_id and BOARD[position]["type"] == "railroad"
        )
        return 25 * max(1, 2 ** (owned - 1))

    def utility_rent(self, owner_id: str) -> int:
        owned = sum(
            1
            for position, holder in self.property_owner.items()
            if holder == owner_id and BOARD[position]["type"] == "utility"
        )
        multiplier = 10 if owned >= 2 else 4
        return max(1, self.last_roll_total) * multiplier

    def handle_buy(self, player_id: str) -> None:
        if self.current_player is None or self.current_player.id != player_id:
            self.last_message = "It is not your turn."
            return

        player = self.players[player_id]
        if not self.can_buy_current_space(player):
            self.last_message = "This space cannot be bought right now."
            return

        space = BOARD[player.position]
        player.money -= space["price"]
        player.properties.append(player.position)
        self.property_owner[player.position] = player.id
        self.last_message = f"{player.name} bought {space['name']} for {space['price']}."
        self.check_bankruptcy(player)

    def handle_end_turn(self, player_id: str) -> None:
        if self.current_player is None or self.current_player.id != player_id:
            self.last_message = "It is not your turn."
            return
        if not self.players[player_id].has_rolled:
            self.last_message = "Roll before ending your turn."
            return
        self.next_turn()

    def check_bankruptcy(self, player: Player) -> None:
        if player.money >= 0 or player.bankrupt:
            return
        player.bankrupt = True
        player.in_jail = False
        for position in list(player.properties):
            self.property_owner.pop(position, None)
        player.properties.clear()
        self.last_message = f"{player.name} has gone bankrupt."

    async def broadcast_state(self) -> None:
        stale: list[str] = []
        for pid, websocket in self.connections.items():
            try:
                await websocket.send_text(json.dumps(self.state(pid)))
            except Exception:
                stale.append(pid)
        for pid in stale:
            self.remove_player(pid)


app = FastAPI(title="Property Rush")
rooms: dict[str, GameRoom] = {}
static_dir = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def index() -> HTMLResponse:
    return HTMLResponse((static_dir / "index.html").read_text(encoding="utf-8"))


@app.get("/api/meta")
async def meta() -> dict[str, Any]:
    return {"board": BOARD, "colors": COLOR_CLASSES}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    player_id: str | None = None
    room: GameRoom | None = None
    try:
        while True:
            payload = json.loads(await websocket.receive_text())
            action = payload.get("action")
            if action == "join":
                room_id = str(payload.get("roomId", "demo")).strip() or "demo"
                player_name = str(payload.get("name", "Player")).strip() or "Player"
                player_id = str(payload.get("playerId") or uuid4())
                room = rooms.setdefault(room_id, GameRoom(room_id))
                room.add_player(player_id, player_name, websocket)
                room.ensure_started()
                await room.broadcast_state()
                await websocket.send_text(json.dumps({"type": "joined", "playerId": player_id}))
                continue

            if room is None or player_id is None:
                await websocket.send_text(
                    json.dumps({"type": "error", "message": "Join a room first."})
                )
                continue

            if action == "roll":
                room.handle_roll(player_id)
            elif action == "buy":
                room.handle_buy(player_id)
            elif action == "end_turn":
                room.handle_end_turn(player_id)
            else:
                await websocket.send_text(
                    json.dumps({"type": "error", "message": "Unknown action."})
                )
                continue

            await room.broadcast_state()
    except WebSocketDisconnect:
        if room and player_id:
            room.remove_player(player_id)
            await room.broadcast_state()
