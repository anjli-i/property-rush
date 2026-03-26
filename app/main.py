import json
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

BOARD = [
    {"name": "Go", "type": "go"},
    {"name": "Mediterranean Avenue", "type": "property", "price": 60, "mortgage": 30, "house_cost": 50, "color": "brown", "rents": [2, 10, 30, 90, 160, 250]},
    {"name": "Community Chest", "type": "chest"},
    {"name": "Baltic Avenue", "type": "property", "price": 60, "mortgage": 30, "house_cost": 50, "color": "brown", "rents": [4, 20, 60, 180, 320, 450]},
    {"name": "Income Tax", "type": "tax", "amount": 200},
    {"name": "Reading Railroad", "type": "railroad", "price": 200, "mortgage": 100},
    {"name": "Oriental Avenue", "type": "property", "price": 100, "mortgage": 50, "house_cost": 50, "color": "light-blue", "rents": [6, 30, 90, 270, 400, 550]},
    {"name": "Chance", "type": "chance"},
    {"name": "Vermont Avenue", "type": "property", "price": 100, "mortgage": 50, "house_cost": 50, "color": "light-blue", "rents": [6, 30, 90, 270, 400, 550]},
    {"name": "Connecticut Avenue", "type": "property", "price": 120, "mortgage": 60, "house_cost": 50, "color": "light-blue", "rents": [8, 40, 100, 300, 450, 600]},
    {"name": "Jail / Just Visiting", "type": "jail"},
    {"name": "St. Charles Place", "type": "property", "price": 140, "mortgage": 70, "house_cost": 100, "color": "pink", "rents": [10, 50, 150, 450, 625, 750]},
    {"name": "Electric Company", "type": "utility", "price": 150, "mortgage": 75},
    {"name": "States Avenue", "type": "property", "price": 140, "mortgage": 70, "house_cost": 100, "color": "pink", "rents": [10, 50, 150, 450, 625, 750]},
    {"name": "Virginia Avenue", "type": "property", "price": 160, "mortgage": 80, "house_cost": 100, "color": "pink", "rents": [12, 60, 180, 500, 700, 900]},
    {"name": "Pennsylvania Railroad", "type": "railroad", "price": 200, "mortgage": 100},
    {"name": "St. James Place", "type": "property", "price": 180, "mortgage": 90, "house_cost": 100, "color": "orange", "rents": [14, 70, 200, 550, 750, 950]},
    {"name": "Community Chest", "type": "chest"},
    {"name": "Tennessee Avenue", "type": "property", "price": 180, "mortgage": 90, "house_cost": 100, "color": "orange", "rents": [14, 70, 200, 550, 750, 950]},
    {"name": "New York Avenue", "type": "property", "price": 200, "mortgage": 100, "house_cost": 100, "color": "orange", "rents": [16, 80, 220, 600, 800, 1000]},
    {"name": "Free Parking", "type": "parking"},
    {"name": "Kentucky Avenue", "type": "property", "price": 220, "mortgage": 110, "house_cost": 150, "color": "red", "rents": [18, 90, 250, 700, 875, 1050]},
    {"name": "Chance", "type": "chance"},
    {"name": "Indiana Avenue", "type": "property", "price": 220, "mortgage": 110, "house_cost": 150, "color": "red", "rents": [18, 90, 250, 700, 875, 1050]},
    {"name": "Illinois Avenue", "type": "property", "price": 240, "mortgage": 120, "house_cost": 150, "color": "red", "rents": [20, 100, 300, 750, 925, 1100]},
    {"name": "B. & O. Railroad", "type": "railroad", "price": 200, "mortgage": 100},
    {"name": "Atlantic Avenue", "type": "property", "price": 260, "mortgage": 130, "house_cost": 150, "color": "yellow", "rents": [22, 110, 330, 800, 975, 1150]},
    {"name": "Ventnor Avenue", "type": "property", "price": 260, "mortgage": 130, "house_cost": 150, "color": "yellow", "rents": [22, 110, 330, 800, 975, 1150]},
    {"name": "Water Works", "type": "utility", "price": 150, "mortgage": 75},
    {"name": "Marvin Gardens", "type": "property", "price": 280, "mortgage": 140, "house_cost": 150, "color": "yellow", "rents": [24, 120, 360, 850, 1025, 1200]},
    {"name": "Go To Jail", "type": "go_to_jail"},
    {"name": "Pacific Avenue", "type": "property", "price": 300, "mortgage": 150, "house_cost": 200, "color": "green", "rents": [26, 130, 390, 900, 1100, 1275]},
    {"name": "North Carolina Avenue", "type": "property", "price": 300, "mortgage": 150, "house_cost": 200, "color": "green", "rents": [26, 130, 390, 900, 1100, 1275]},
    {"name": "Community Chest", "type": "chest"},
    {"name": "Pennsylvania Avenue", "type": "property", "price": 320, "mortgage": 160, "house_cost": 200, "color": "green", "rents": [28, 150, 450, 1000, 1200, 1400]},
    {"name": "Short Line", "type": "railroad", "price": 200, "mortgage": 100},
    {"name": "Chance", "type": "chance"},
    {"name": "Park Place", "type": "property", "price": 350, "mortgage": 175, "house_cost": 200, "color": "dark-blue", "rents": [35, 175, 500, 1100, 1300, 1500]},
    {"name": "Luxury Tax", "type": "tax", "amount": 100},
    {"name": "Boardwalk", "type": "property", "price": 400, "mortgage": 200, "house_cost": 200, "color": "dark-blue", "rents": [50, 200, 600, 1400, 1700, 2000]},
]

GO_MONEY = 200
JAIL_INDEX = 10
MAX_LOG_ITEMS = 14
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ROOMS_FILE = DATA_DIR / "rooms.json"
PROPERTY_GROUPS = {
    "brown": [1, 3],
    "light-blue": [6, 8, 9],
    "pink": [11, 13, 14],
    "orange": [16, 18, 19],
    "red": [21, 23, 24],
    "yellow": [26, 27, 29],
    "green": [31, 32, 34],
    "dark-blue": [37, 39],
}

CHANCE_CARDS = [
    {"text": "Advance to Go", "move_to": 0},
    {"text": "Advance to Illinois Avenue", "move_to": 24},
    {"text": "Go to St. Charles Place", "move_to": 11},
    {"text": "Take a trip to Reading Railroad", "move_to": 5},
    {"text": "Bank pays you dividend of 50", "money": 50},
    {"text": "Pay poor tax of 15", "money": -15},
    {"text": "Go to Jail", "go_to_jail": True},
]

COMMUNITY_CARDS = [
    {"text": "Advance to Go", "move_to": 0},
    {"text": "Bank error in your favor. Collect 200", "money": 200},
    {"text": "Doctor's fees. Pay 50", "money": -50},
    {"text": "From sale of stock you get 50", "money": 50},
    {"text": "Holiday fund matures. Receive 100", "money": 100},
    {"text": "Pay hospital fees of 100", "money": -100},
    {"text": "You inherit 100", "money": 100},
]


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


@dataclass
class TradeOffer:
    id: str
    from_player_id: str
    to_player_id: str
    offer_property: int | None = None
    request_property: int | None = None
    offer_money: int = 0
    request_money: int = 0


def serialize_player(player: Player) -> dict[str, Any]:
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
        "avatar": player.name[:2].upper(),
    }


class GameRoom:
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.players: dict[str, Player] = {}
        self.connections: dict[str, WebSocket] = {}
        self.property_owner: dict[int, str] = {}
        self.property_houses: dict[int, int] = {}
        self.turn_order: list[str] = []
        self.current_turn_index = 0
        self.started = False
        self.last_roll: tuple[int, int] | None = None
        self.last_roll_total = 0
        self.last_message = "Waiting for at least 2 players."
        self.log: list[str] = ["Welcome to Property Rush."]
        self.highlighted_space: int | None = None
        self.trade_offer: TradeOffer | None = None

    @classmethod
    def from_snapshot(cls, data: dict[str, Any]) -> "GameRoom":
        room = cls(data["room_id"])
        room.players = {
            item["id"]: Player(
                id=item["id"],
                name=item["name"],
                money=item["money"],
                position=item["position"],
                properties=list(item["properties"]),
                bankrupt=item["bankrupt"],
                connected=False,
                in_jail=item["in_jail"],
                has_rolled=item["has_rolled"],
            )
            for item in data.get("players", [])
        }
        room.property_owner = {int(k): v for k, v in data.get("property_owner", {}).items()}
        room.property_houses = {int(k): int(v) for k, v in data.get("property_houses", {}).items()}
        room.turn_order = list(data.get("turn_order", []))
        room.current_turn_index = int(data.get("current_turn_index", 0))
        room.started = bool(data.get("started", False))
        roll = data.get("last_roll")
        room.last_roll = tuple(roll) if roll else None
        room.last_roll_total = int(data.get("last_roll_total", 0))
        room.last_message = data.get("last_message", room.last_message)
        room.log = list(data.get("log", room.log))
        room.highlighted_space = data.get("highlighted_space")
        if data.get("trade_offer"):
            room.trade_offer = TradeOffer(**data["trade_offer"])
        return room

    def snapshot(self) -> dict[str, Any]:
        return {
            "room_id": self.room_id,
            "players": [
                {
                    "id": player.id,
                    "name": player.name,
                    "money": player.money,
                    "position": player.position,
                    "properties": player.properties,
                    "bankrupt": player.bankrupt,
                    "in_jail": player.in_jail,
                    "has_rolled": player.has_rolled,
                }
                for player in self.players.values()
            ],
            "property_owner": self.property_owner,
            "property_houses": self.property_houses,
            "turn_order": self.turn_order,
            "current_turn_index": self.current_turn_index,
            "started": self.started,
            "last_roll": list(self.last_roll) if self.last_roll else None,
            "last_roll_total": self.last_roll_total,
            "last_message": self.last_message,
            "log": self.log,
            "highlighted_space": self.highlighted_space,
            "trade_offer": asdict(self.trade_offer) if self.trade_offer else None,
        }

    def add_log(self, message: str) -> None:
        self.last_message = message
        self.log.append(message)
        self.log = self.log[-MAX_LOG_ITEMS:]

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
        self.add_log(f"{player.name} joined room {self.room_id}.")
        return player

    def remove_player(self, player_id: str) -> None:
        self.connections.pop(player_id, None)
        player = self.players.get(player_id)
        if player:
            player.connected = False
            self.add_log(f"{player.name} disconnected.")

    @property
    def current_player(self) -> Player | None:
        if not self.turn_order:
            return None
        return self.players[self.turn_order[self.current_turn_index]]

    def ensure_started(self) -> None:
        if not self.started and len(self.turn_order) >= 2:
            self.started = True
            self.current_player.has_rolled = False
            self.add_log(f"Game started. {self.current_player.name} goes first.")

    def winner_name(self) -> str | None:
        solvent = [player for player in self.players.values() if not player.bankrupt]
        if self.started and len(solvent) == 1 and len(self.players) > 1:
            return solvent[0].name
        return None

    def owns_monopoly(self, player_id: str, property_index: int) -> bool:
        space = BOARD[property_index]
        color = space.get("color")
        if not color:
            return False
        return all(self.property_owner.get(index) == player_id for index in PROPERTY_GROUPS[color])

    def property_level_label(self, houses: int) -> str:
        if houses >= 5:
            return "Hotel"
        if houses == 0:
            return "No houses"
        if houses == 1:
            return "1 house"
        return f"{houses} houses"

    def current_rent(self, position: int) -> int:
        space = BOARD[position]
        if space["type"] == "property":
            houses = self.property_houses.get(position, 0)
            if houses == 0 and self.owns_monopoly(self.property_owner.get(position, ""), position):
                return space["rents"][0] * 2
            return space["rents"][min(houses, len(space["rents"]) - 1)]
        if space["type"] == "railroad":
            return self.railroad_rent(self.property_owner.get(position, ""))
        if space["type"] == "utility":
            return self.utility_rent(self.property_owner.get(position, ""))
        return 0

    def can_buy_current_space(self, player: Player | None) -> bool:
        if player is None:
            return False
        space = BOARD[player.position]
        return (
            space["type"] in {"property", "railroad", "utility"}
            and player.position not in self.property_owner
            and player.money >= space["price"]
            and player.has_rolled
            and not player.bankrupt
        )

    def can_build(self, player_id: str, property_index: int) -> bool:
        if property_index not in self.property_owner:
            return False
        if self.property_owner[property_index] != player_id:
            return False
        space = BOARD[property_index]
        if space["type"] != "property":
            return False
        player = self.players[player_id]
        if player.bankrupt or player.money < space["house_cost"]:
            return False
        if not self.owns_monopoly(player_id, property_index):
            return False
        return self.property_houses.get(property_index, 0) < 5
    def property_cards(self, player_id: str | None) -> list[dict[str, Any]]:
        cards: list[dict[str, Any]] = []
        for index, space in enumerate(BOARD):
            if space["type"] not in {"property", "railroad", "utility"}:
                continue
            owner_id = self.property_owner.get(index)
            owner = self.players.get(owner_id) if owner_id else None
            houses = self.property_houses.get(index, 0)
            cards.append(
                {
                    "index": index,
                    "name": space["name"],
                    "type": space["type"],
                    "price": space["price"],
                    "rent": self.current_rent(index) if owner_id else (space.get("rents", [0])[0] if space["type"] == "property" else 25),
                    "ownerId": owner_id,
                    "ownerName": owner.name if owner else "Bank",
                    "color": space.get("color"),
                    "houseCost": space.get("house_cost"),
                    "houses": houses,
                    "levelLabel": self.property_level_label(houses),
                    "canBuild": bool(player_id and self.can_build(player_id, index)),
                    "canSell": bool(player_id and owner_id == player_id),
                    "mortgage": space.get("mortgage", 0),
                }
            )
        return cards

    def leaderboard(self) -> list[dict[str, Any]]:
        ranked = []
        for player in self.players.values():
            assets = player.money
            for property_index in player.properties:
                assets += BOARD[property_index]["price"]
                houses = self.property_houses.get(property_index, 0)
                if BOARD[property_index]["type"] == "property":
                    assets += houses * BOARD[property_index]["house_cost"]
            ranked.append(
                {
                    "id": player.id,
                    "name": player.name,
                    "cash": player.money,
                    "assets": assets,
                    "properties": len(player.properties),
                    "bankrupt": player.bankrupt,
                }
            )
        return sorted(ranked, key=lambda item: item["assets"], reverse=True)

    def trade_state(self) -> dict[str, Any] | None:
        if not self.trade_offer:
            return None
        offer = self.trade_offer
        return {
            "id": offer.id,
            "fromPlayerId": offer.from_player_id,
            "fromPlayerName": self.players[offer.from_player_id].name,
            "toPlayerId": offer.to_player_id,
            "toPlayerName": self.players[offer.to_player_id].name,
            "offerProperty": offer.offer_property,
            "offerPropertyName": BOARD[offer.offer_property]["name"] if offer.offer_property is not None else None,
            "requestProperty": offer.request_property,
            "requestPropertyName": BOARD[offer.request_property]["name"] if offer.request_property is not None else None,
            "offerMoney": offer.offer_money,
            "requestMoney": offer.request_money,
        }

    def state(self, player_id: str | None = None) -> dict[str, Any]:
        current = self.current_player
        me = self.players.get(player_id) if player_id else None
        return {
            "type": "state",
            "roomId": self.room_id,
            "started": self.started,
            "players": [serialize_player(self.players[pid]) for pid in self.turn_order],
            "propertyOwners": self.property_owner,
            "propertyHouses": self.property_houses,
            "propertyCards": self.property_cards(player_id),
            "currentTurn": current.id if current else None,
            "currentTurnName": current.name if current else None,
            "board": BOARD,
            "lastRoll": self.last_roll,
            "lastMessage": self.last_message,
            "log": self.log,
            "highlightedSpace": self.highlighted_space,
            "you": player_id,
            "winner": self.winner_name(),
            "canBuy": self.can_buy_current_space(me),
            "tradeOffer": self.trade_state(),
            "leaderboard": self.leaderboard(),
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
        self.highlighted_space = None
        self.trade_offer = None
        self.add_log(f"{self.current_player.name}'s turn.")

    def send_to_jail(self, player: Player) -> None:
        player.position = JAIL_INDEX
        player.in_jail = True
        player.has_rolled = True
        self.highlighted_space = JAIL_INDEX
        self.add_log(f"{player.name} was sent to jail.")

    def move_player(self, player: Player, target: int) -> None:
        if target < player.position:
            player.money += GO_MONEY
            self.add_log(f"{player.name} passed Go and collected {GO_MONEY}.")
        player.position = target
        self.highlighted_space = target

    def handle_roll(self, player_id: str) -> None:
        self.ensure_started()
        if not self.started:
            self.add_log("Need at least 2 players to start.")
            return
        if self.current_player is None or self.current_player.id != player_id:
            self.add_log("It is not your turn.")
            return

        player = self.players[player_id]
        if player.bankrupt:
            self.add_log(f"{player.name} is bankrupt and cannot play.")
            return
        if player.has_rolled:
            self.add_log("You already rolled this turn.")
            return

        player.has_rolled = True
        self.trade_offer = None

        if player.in_jail:
            player.in_jail = False
            self.last_roll = None
            self.last_roll_total = 0
            self.add_log(f"{player.name} used their turn to leave jail.")
            return

        die_one = random.randint(1, 6)
        die_two = random.randint(1, 6)
        total = die_one + die_two
        self.last_roll = (die_one, die_two)
        self.last_roll_total = total
        old_position = player.position
        player.position = (player.position + total) % len(BOARD)
        self.highlighted_space = player.position
        if player.position < old_position:
            player.money += GO_MONEY
            self.add_log(f"{player.name} passed Go and collected {GO_MONEY}.")
        self.resolve_landing(player, f"{player.name} rolled {die_one} + {die_two}.")

    def resolve_landing(self, player: Player, prefix: str | None = None) -> None:
        space = BOARD[player.position]
        base_message = f"{player.name} landed on {space['name']}."
        if prefix:
            base_message = f"{prefix} {base_message}"
        if space["type"] == "property":
            owner_id = self.property_owner.get(player.position)
            if owner_id and owner_id != player.id:
                rent = self.current_rent(player.position)
                owner = self.players[owner_id]
                player.money -= rent
                owner.money += rent
                self.add_log(f"{base_message} {player.name} paid {rent} rent to {owner.name}.")
            elif owner_id == player.id:
                self.add_log(f"{base_message} You own this block.")
            else:
                self.add_log(f"{base_message} Claim it for {space['price']}.")
        elif space["type"] == "railroad":
            owner_id = self.property_owner.get(player.position)
            if owner_id and owner_id != player.id:
                owner = self.players[owner_id]
                rent = self.railroad_rent(owner_id)
                player.money -= rent
                owner.money += rent
                self.add_log(f"{base_message} {player.name} paid railroad rent of {rent} to {owner.name}.")
            elif owner_id == player.id:
                self.add_log(f"{base_message} Your rail line is safe.")
            else:
                self.add_log(f"{base_message} Claim this railroad for {space['price']}.")
        elif space["type"] == "utility":
            owner_id = self.property_owner.get(player.position)
            if owner_id and owner_id != player.id:
                owner = self.players[owner_id]
                rent = self.utility_rent(owner_id)
                player.money -= rent
                owner.money += rent
                self.add_log(f"{base_message} {player.name} paid utility rent of {rent} to {owner.name}.")
            elif owner_id == player.id:
                self.add_log(f"{base_message} Your utility is humming.")
            else:
                self.add_log(f"{base_message} Claim this utility for {space['price']}.")
        elif space["type"] == "tax":
            amount = space["amount"]
            player.money -= amount
            self.add_log(f"{base_message} {player.name} paid tax of {amount}.")
        elif space["type"] == "chance":
            self.apply_card(player, random.choice(CHANCE_CARDS), "Chance", base_message)
        elif space["type"] == "chest":
            self.apply_card(player, random.choice(COMMUNITY_CARDS), "Community Chest", base_message)
        elif space["type"] == "go_to_jail":
            self.add_log(base_message)
            self.send_to_jail(player)
        else:
            self.add_log(base_message)
        self.check_bankruptcy(player)

    def apply_card(self, player: Player, card: dict[str, Any], deck_name: str, prefix: str) -> None:
        message = f"{prefix} {player.name} drew {deck_name}: {card['text']}."
        if "money" in card:
            player.money += card["money"]
            self.add_log(message)
        elif card.get("go_to_jail"):
            self.add_log(message)
            self.send_to_jail(player)
            return
        elif "move_to" in card:
            self.add_log(message)
            self.move_player(player, card["move_to"])
            self.resolve_landing(player)
            return
        else:
            self.add_log(message)
        self.check_bankruptcy(player)

    def railroad_rent(self, owner_id: str) -> int:
        if not owner_id:
            return 25
        owned = sum(
            1
            for position, holder in self.property_owner.items()
            if holder == owner_id and BOARD[position]["type"] == "railroad"
        )
        return 25 * max(1, 2 ** (owned - 1))

    def utility_rent(self, owner_id: str) -> int:
        if not owner_id:
            return 4 * max(1, self.last_roll_total)
        owned = sum(
            1
            for position, holder in self.property_owner.items()
            if holder == owner_id and BOARD[position]["type"] == "utility"
        )
        multiplier = 10 if owned >= 2 else 4
        return max(1, self.last_roll_total) * multiplier

    def handle_buy(self, player_id: str) -> None:
        if self.current_player is None or self.current_player.id != player_id:
            self.add_log("It is not your turn.")
            return

        player = self.players[player_id]
        if not self.can_buy_current_space(player):
            self.add_log("This space cannot be claimed right now.")
            return

        space = BOARD[player.position]
        player.money -= space["price"]
        player.properties.append(player.position)
        self.property_owner[player.position] = player.id
        self.property_houses.setdefault(player.position, 0)
        self.add_log(f"{player.name} claimed {space['name']} for {space['price']}.")
        self.check_bankruptcy(player)
    def handle_build(self, player_id: str, property_index: int) -> None:
        if self.current_player is None or self.current_player.id != player_id:
            self.add_log("Only the active player can build.")
            return
        if not self.can_build(player_id, property_index):
            self.add_log("That property cannot be upgraded right now.")
            return
        player = self.players[player_id]
        cost = BOARD[property_index]["house_cost"]
        player.money -= cost
        self.property_houses[property_index] = self.property_houses.get(property_index, 0) + 1
        houses = self.property_houses[property_index]
        label = "hotel" if houses >= 5 else f"house {houses}"
        self.add_log(f"{player.name} built {label} on {BOARD[property_index]['name']} for {cost}.")
        self.check_bankruptcy(player)

    def handle_sell(self, player_id: str, property_index: int) -> None:
        if self.property_owner.get(property_index) != player_id:
            self.add_log("You can only sell a property you own.")
            return
        player = self.players[player_id]
        space = BOARD[property_index]
        sale_value = space["price"] // 2
        houses = self.property_houses.get(property_index, 0)
        if space["type"] == "property" and houses:
            sale_value += (space["house_cost"] * houses) // 2
        player.money += sale_value
        player.properties = [item for item in player.properties if item != property_index]
        self.property_owner.pop(property_index, None)
        self.property_houses.pop(property_index, None)
        self.add_log(f"{player.name} sold {space['name']} back to the bank for {sale_value}.")

    def handle_trade_offer(self, player_id: str, payload: dict[str, Any]) -> None:
        if self.current_player is None or self.current_player.id != player_id:
            self.add_log("Only the active player can start a trade.")
            return
        to_player_id = str(payload.get("toPlayerId") or "")
        offer_property = payload.get("offerProperty")
        request_property = payload.get("requestProperty")
        offer_money = max(0, int(payload.get("offerMoney", 0)))
        request_money = max(0, int(payload.get("requestMoney", 0)))
        if to_player_id not in self.players or to_player_id == player_id:
            self.add_log("Choose another player for the trade.")
            return
        if offer_property is not None and self.property_owner.get(int(offer_property)) != player_id:
            self.add_log("You can only offer a property you own.")
            return
        if request_property is not None and self.property_owner.get(int(request_property)) != to_player_id:
            self.add_log("You can only request a property the other player owns.")
            return
        if offer_money > self.players[player_id].money:
            self.add_log("You do not have enough cash for that offer.")
            return
        if offer_property is None and request_property is None and offer_money == 0 and request_money == 0:
            self.add_log("Trade offers need money or a property on at least one side.")
            return
        self.trade_offer = TradeOffer(
            id=str(uuid4()),
            from_player_id=player_id,
            to_player_id=to_player_id,
            offer_property=int(offer_property) if offer_property is not None else None,
            request_property=int(request_property) if request_property is not None else None,
            offer_money=offer_money,
            request_money=request_money,
        )
        self.add_log(f"{self.players[player_id].name} proposed a trade to {self.players[to_player_id].name}.")

    def handle_trade_response(self, player_id: str, accept: bool) -> None:
        offer = self.trade_offer
        if not offer:
            self.add_log("There is no trade to respond to.")
            return
        if offer.to_player_id != player_id:
            self.add_log("That trade is not addressed to you.")
            return
        from_player = self.players[offer.from_player_id]
        to_player = self.players[offer.to_player_id]
        if not accept:
            self.trade_offer = None
            self.add_log(f"{to_player.name} rejected the trade offer.")
            return
        if offer.offer_money > from_player.money or offer.request_money > to_player.money:
            self.trade_offer = None
            self.add_log("The trade failed because one player no longer has enough cash.")
            return
        if offer.offer_property is not None and self.property_owner.get(offer.offer_property) != from_player.id:
            self.trade_offer = None
            self.add_log("The trade failed because the offered property changed hands.")
            return
        if offer.request_property is not None and self.property_owner.get(offer.request_property) != to_player.id:
            self.trade_offer = None
            self.add_log("The trade failed because the requested property changed hands.")
            return

        from_player.money -= offer.offer_money
        to_player.money += offer.offer_money
        to_player.money -= offer.request_money
        from_player.money += offer.request_money

        if offer.offer_property is not None:
            self.transfer_property(offer.offer_property, from_player.id, to_player.id)
        if offer.request_property is not None:
            self.transfer_property(offer.request_property, to_player.id, from_player.id)

        self.trade_offer = None
        self.add_log(f"{to_player.name} accepted the trade offer from {from_player.name}.")
        self.check_bankruptcy(from_player)
        self.check_bankruptcy(to_player)

    def transfer_property(self, property_index: int, from_player_id: str, to_player_id: str) -> None:
        if property_index in self.players[from_player_id].properties:
            self.players[from_player_id].properties.remove(property_index)
        if property_index not in self.players[to_player_id].properties:
            self.players[to_player_id].properties.append(property_index)
        self.property_owner[property_index] = to_player_id

    def handle_end_turn(self, player_id: str) -> None:
        if self.current_player is None or self.current_player.id != player_id:
            self.add_log("It is not your turn.")
            return
        if not self.players[player_id].has_rolled:
            self.add_log("Roll before ending your turn.")
            return
        self.next_turn()

    def check_bankruptcy(self, player: Player) -> None:
        if player.money >= 0 or player.bankrupt:
            return
        player.bankrupt = True
        player.in_jail = False
        for position in list(player.properties):
            self.property_owner.pop(position, None)
            self.property_houses.pop(position, None)
        player.properties.clear()
        if self.trade_offer and (self.trade_offer.from_player_id == player.id or self.trade_offer.to_player_id == player.id):
            self.trade_offer = None
        self.add_log(f"{player.name} has gone bankrupt.")

    async def broadcast_state(self) -> None:
        stale: list[str] = []
        for pid, websocket in self.connections.items():
            try:
                await websocket.send_text(json.dumps(self.state(pid)))
            except Exception:
                stale.append(pid)
        for pid in stale:
            self.remove_player(pid)


def load_rooms() -> dict[str, GameRoom]:
    if not ROOMS_FILE.exists():
        return {}
    try:
        data = json.loads(ROOMS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return {room_id: GameRoom.from_snapshot(snapshot) for room_id, snapshot in data.items()}


def save_rooms(rooms: dict[str, GameRoom]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {room_id: room.snapshot() for room_id, room in rooms.items()}
    ROOMS_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


app = FastAPI(title="Property Rush")
rooms: dict[str, GameRoom] = load_rooms()
static_dir = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def index() -> HTMLResponse:
    return HTMLResponse((static_dir / "index.html").read_text(encoding="utf-8"))


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
                save_rooms(rooms)
                await room.broadcast_state()
                await websocket.send_text(json.dumps({"type": "joined", "playerId": player_id}))
                continue

            if room is None or player_id is None:
                await websocket.send_text(json.dumps({"type": "error", "message": "Join a room first."}))
                continue

            if action == "roll":
                room.handle_roll(player_id)
            elif action == "buy":
                room.handle_buy(player_id)
            elif action == "build":
                room.handle_build(player_id, int(payload["propertyIndex"]))
            elif action == "sell":
                room.handle_sell(player_id, int(payload["propertyIndex"]))
            elif action == "trade_offer":
                room.handle_trade_offer(player_id, payload)
            elif action == "trade_response":
                room.handle_trade_response(player_id, bool(payload.get("accept")))
            elif action == "end_turn":
                room.handle_end_turn(player_id)
            else:
                await websocket.send_text(json.dumps({"type": "error", "message": "Unknown action."}))
                continue

            save_rooms(rooms)
            await room.broadcast_state()
    except WebSocketDisconnect:
        if room and player_id:
            room.remove_player(player_id)
            save_rooms(rooms)
            await room.broadcast_state()
