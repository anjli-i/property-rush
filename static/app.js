const joinForm = document.getElementById("join-form");
const roomInput = document.getElementById("room");
const nameInput = document.getElementById("name");
const connectionPill = document.getElementById("connection-pill");
const roomLabel = document.getElementById("room-label");
const turnLabel = document.getElementById("turn-label");
const messageLabel = document.getElementById("message-label");
const winnerLabel = document.getElementById("winner-label");
const playersRoot = document.getElementById("players");
const boardRoot = document.getElementById("board");
const rollLabel = document.getElementById("roll-label");
const rollBtn = document.getElementById("roll-btn");
const buyBtn = document.getElementById("buy-btn");
const endBtn = document.getElementById("end-btn");

let socket = null;
let playerId = sessionStorage.getItem("property-rush-player-id") || null;

function setConnected(connected) {
  connectionPill.textContent = connected ? "Online" : "Offline";
  connectionPill.classList.toggle("online", connected);
  connectionPill.classList.toggle("offline", !connected);
}

function send(action) {
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    return;
  }
  socket.send(JSON.stringify({ action, playerId }));
}

function formatStatus(player) {
  if (player.bankrupt) return "Bankrupt";
  if (player.inJail) return "In jail";
  return player.connected ? "Connected" : "Disconnected";
}

function renderPlayers(state) {
  playersRoot.innerHTML = "";
  state.players.forEach((player) => {
    const card = document.createElement("div");
    card.className = "player-card";
    if (player.id === state.currentTurn) card.classList.add("current");
    if (player.bankrupt) card.classList.add("bankrupt");
    const propertyNames = player.properties.map((index) => state.board[index].name);
    card.innerHTML = `
      <strong>${player.name}${player.id === state.you ? " (You)" : ""}</strong>
      <div>Cash: ${player.money}</div>
      <div>Position: ${state.board[player.position].name}</div>
      <div>Properties: ${propertyNames.length ? propertyNames.join(", ") : "None"}</div>
      <div>Status: ${formatStatus(player)}</div>
    `;
    playersRoot.appendChild(card);
  });
}

function stripeColor(space) {
  return space.color ? `var(--${space.color})` : "transparent";
}

function renderBoard(state) {
  boardRoot.innerHTML = "";
  const me = state.players.find((player) => player.id === state.you);
  state.board.forEach((space, index) => {
    const cell = document.createElement("div");
    cell.className = "space";
    cell.style.setProperty("--space-color", stripeColor(space));
    if (me?.position === index) {
      cell.classList.add("active");
    }
    if (state.canBuy && me?.position === index) {
      cell.classList.add("buyable");
    }
    const ownerId = state.propertyOwners[index];
    const owner = state.players.find((player) => player.id === ownerId);
    const occupants = state.players
      .filter((player) => player.position === index)
      .map((player) => player.name);
    const price = space.price ?? "-";
    const rent = space.rent ?? "-";
    cell.innerHTML = `
      <div class="space-top"></div>
      <strong>${index}. ${space.name}</strong>
      <div>Type: ${space.type}</div>
      <div>Price: ${price}</div>
      <div>Rent: ${rent}</div>
      <div class="owner">Owner: ${owner ? owner.name : "Bank"}</div>
      <div>${occupants.map((name) => `<span class="token">${name}</span>`).join("")}</div>
    `;
    boardRoot.appendChild(cell);
  });
}

function updateControls(state) {
  const me = state.players.find((player) => player.id === state.you);
  const isMyTurn = me && state.currentTurn === state.you && !me.bankrupt;
  rollBtn.disabled = !isMyTurn || me?.hasRolled;
  buyBtn.disabled = !state.canBuy;
  endBtn.disabled = !isMyTurn || !me?.hasRolled;
}

function renderState(state) {
  roomLabel.textContent = `Room: ${state.roomId}`;
  turnLabel.textContent = state.started
    ? `Turn: ${state.currentTurnName}`
    : "Turn: waiting for 2 players";
  messageLabel.textContent = `Message: ${state.lastMessage}`;
  winnerLabel.textContent = state.winner ? `Winner: ${state.winner}` : "";
  rollLabel.textContent = state.lastRoll
    ? `Last roll: ${state.lastRoll[0]} + ${state.lastRoll[1]}`
    : "No roll yet";
  renderPlayers(state);
  renderBoard(state);
  updateControls(state);
}

function connect(roomId, name) {
  if (socket) socket.close();
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  socket = new WebSocket(`${protocol}://${window.location.host}/ws`);

  socket.addEventListener("open", () => {
    setConnected(true);
    socket.send(JSON.stringify({ action: "join", roomId, name, playerId }));
  });

  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (message.type === "joined") {
      playerId = message.playerId;
      sessionStorage.setItem("property-rush-player-id", playerId);
      return;
    }
    if (message.type === "state") {
      renderState(message);
      return;
    }
    if (message.type === "error") {
      messageLabel.textContent = `Message: ${message.message}`;
    }
  });

  socket.addEventListener("close", () => {
    setConnected(false);
    rollBtn.disabled = true;
    buyBtn.disabled = true;
    endBtn.disabled = true;
  });
}

joinForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const name = nameInput.value.trim() || "Player";
  const roomId = roomInput.value.trim() || "demo";
  connect(roomId, name);
});

rollBtn.addEventListener("click", () => send("roll"));
buyBtn.addEventListener("click", () => send("buy"));
endBtn.addEventListener("click", () => send("end_turn"));

setConnected(false);
