const joinForm = document.getElementById("join-form");
const roomInput = document.getElementById("room");
const nameInput = document.getElementById("name");
const connectionPill = document.getElementById("connection-pill");
const turnBanner = document.getElementById("turn-banner");
const roomLabel = document.getElementById("room-label");
const messageLabel = document.getElementById("message-label");
const rollLabel = document.getElementById("roll-label");
const winnerLabel = document.getElementById("winner-label");
const playersRoot = document.getElementById("players");
const boardRoot = document.getElementById("board");
const propertyCardsRoot = document.getElementById("property-cards");
const gameLogRoot = document.getElementById("game-log");
const leaderboardRoot = document.getElementById("leaderboard");
const rollBtn = document.getElementById("roll-btn");
const buyBtn = document.getElementById("buy-btn");
const endBtn = document.getElementById("end-btn");
const tradeForm = document.getElementById("trade-form");
const tradeTarget = document.getElementById("trade-target");
const tradeOfferProperty = document.getElementById("trade-offer-property");
const tradeRequestProperty = document.getElementById("trade-request-property");
const tradeOfferMoney = document.getElementById("trade-offer-money");
const tradeRequestMoney = document.getElementById("trade-request-money");
const tradeSubmit = document.getElementById("trade-submit");
const tradeOfferBox = document.getElementById("trade-offer-box");
const propertyModal = document.getElementById("property-modal");
const propertyModalBody = document.getElementById("property-modal-body");
const buildBtn = document.getElementById("build-btn");
const sellBtn = document.getElementById("sell-btn");
const closeModalBtn = document.getElementById("close-modal-btn");

let socket = null;
let playerId = sessionStorage.getItem("property-rush-player-id") || null;
let currentState = null;
let activePropertyIndex = null;
let lastRollKey = "";

function setConnected(connected) {
  connectionPill.textContent = connected ? "Connected" : "Offline";
  connectionPill.classList.toggle("online", connected);
  connectionPill.classList.toggle("offline", !connected);
}

function send(action, payload = {}) {
  if (!socket || socket.readyState !== WebSocket.OPEN) return;
  socket.send(JSON.stringify({ action, playerId, ...payload }));
}

function getMe(state) {
  return state.players.find((player) => player.id === state.you);
}

function isMyTurn(state) {
  return state.currentTurn === state.you;
}

function optionMarkup(value, label, selected = false) {
  return `<option value="${value}" ${selected ? "selected" : ""}>${label}</option>`;
}

function renderPlayers(state) {
  playersRoot.innerHTML = "";
  state.players.forEach((player) => {
    const card = document.createElement("article");
    card.className = "player-card";
    if (player.id === state.currentTurn) card.classList.add("active");
    if (player.bankrupt) card.classList.add("muted");
    const holdings = player.properties.length ? `${player.properties.length} deeds` : "No deeds";
    card.innerHTML = `
      <div class="player-row">
        <div class="avatar">${player.avatar}</div>
        <div>
          <h3>${player.name}${player.id === state.you ? " <span class='you-tag'>You</span>" : ""}</h3>
          <p>${player.inJail ? "In jail" : player.bankrupt ? "Bankrupt" : "At the table"}</p>
        </div>
      </div>
      <div class="player-stats">
        <span>Cash <strong>${player.money}</strong></span>
        <span>Space <strong>${state.board[player.position].name}</strong></span>
        <span>${holdings}</span>
      </div>
    `;
    playersRoot.appendChild(card);
  });
}

function renderLeaderboard(state) {
  leaderboardRoot.innerHTML = "";
  state.leaderboard.forEach((entry, index) => {
    const row = document.createElement("div");
    row.className = "leader-row";
    row.innerHTML = `
      <span class="place">${index + 1}</span>
      <div>
        <strong>${entry.name}</strong>
        <p>${entry.properties} properties</p>
      </div>
      <div class="leader-metrics">
        <span>$${entry.cash}</span>
        <span>$${entry.assets} assets</span>
      </div>
    `;
    leaderboardRoot.appendChild(row);
  });
}

function renderBoard(state) {
  boardRoot.innerHTML = "";
  const me = getMe(state);
  state.board.forEach((space, index) => {
    const cell = document.createElement("button");
    cell.type = "button";
    cell.className = "board-space";
    if (state.highlightedSpace === index) cell.classList.add("highlighted");
    if (me?.position === index) cell.classList.add("current-position");
    if (space.color) cell.style.setProperty("--tile-accent", `var(--${space.color})`);
    const ownerId = state.propertyOwners[index];
    const owner = state.players.find((player) => player.id === ownerId);
    const houses = state.propertyHouses[index] || 0;
    const occupants = state.players.filter((player) => player.position === index).map((player) => player.name);
    cell.innerHTML = `
      <span class="tile-band"></span>
      <strong>${space.name}</strong>
      <span class="tile-type">${space.type}</span>
      <span class="tile-meta">${owner ? `Owner: ${owner.name}` : space.price ? `$${space.price}` : "Bank space"}</span>
      <span class="tile-meta">${houses ? (houses >= 5 ? "Hotel" : `${houses} house${houses > 1 ? "s" : ""}`) : ""}</span>
      <div class="tile-tokens">${occupants.map((name) => `<span class="token">${name.slice(0, 2).toUpperCase()}</span>`).join("")}</div>
    `;
    cell.addEventListener("click", () => openPropertyModal(index));
    boardRoot.appendChild(cell);
  });
}

function renderPropertyCards(state) {
  propertyCardsRoot.innerHTML = "";
  state.propertyCards.forEach((card) => {
    const item = document.createElement("button");
    item.type = "button";
    item.className = "property-card";
    if (card.color) item.style.setProperty("--property-accent", `var(--${card.color})`);
    if (card.ownerId === state.you) item.classList.add("owned");
    item.innerHTML = `
      <span class="property-band"></span>
      <strong>${card.name}</strong>
      <p>${card.ownerName}</p>
      <div class="property-metrics">
        <span>Rent $${card.rent}</span>
        <span>${card.levelLabel}</span>
      </div>
    `;
    item.addEventListener("click", () => openPropertyModal(card.index));
    propertyCardsRoot.appendChild(item);
  });
}

function renderLog(state) {
  gameLogRoot.innerHTML = state.log.slice().reverse().map((entry) => `<p>${entry}</p>`).join("");
}

function renderTradeOffer(state) {
  const offer = state.tradeOffer;
  tradeOfferBox.classList.toggle("hidden", !offer);
  if (!offer) {
    tradeOfferBox.innerHTML = "";
    return;
  }
  const isRecipient = offer.toPlayerId === state.you;
  tradeOfferBox.innerHTML = `
    <div class="offer-copy">
      <strong>${offer.fromPlayerName}</strong> offered <strong>${offer.toPlayerName}</strong><br>
      <span>Giving: ${offer.offerPropertyName || "no property"}${offer.offerMoney ? ` + $${offer.offerMoney}` : ""}</span><br>
      <span>Asking: ${offer.requestPropertyName || "no property"}${offer.requestMoney ? ` + $${offer.requestMoney}` : ""}</span>
    </div>
    ${isRecipient ? '<div class="offer-actions"><button id="accept-trade" class="primary-btn">Accept</button><button id="reject-trade" class="ghost-btn">Reject</button></div>' : '<p class="offer-waiting">Waiting for response…</p>'}
  `;
  if (isRecipient) {
    document.getElementById("accept-trade").addEventListener("click", () => send("trade_response", { accept: true }));
    document.getElementById("reject-trade").addEventListener("click", () => send("trade_response", { accept: false }));
  }
}

function renderTradeControls(state) {
  const me = getMe(state);
  const myProperties = state.propertyCards.filter((card) => card.ownerId === state.you);
  const otherPlayers = state.players.filter((player) => player.id !== state.you && !player.bankrupt);
  const targetId = tradeTarget.value || otherPlayers[0]?.id || "";
  tradeTarget.innerHTML = otherPlayers.length
    ? otherPlayers.map((player) => optionMarkup(player.id, player.name, player.id === targetId)).join("")
    : optionMarkup("", "No trade targets", true);
  const targetCards = state.propertyCards.filter((card) => card.ownerId === tradeTarget.value);
  tradeOfferProperty.innerHTML = optionMarkup("", "No property")
    + myProperties.map((card) => optionMarkup(card.index, card.name)).join("");
  tradeRequestProperty.innerHTML = optionMarkup("", "No property")
    + targetCards.map((card) => optionMarkup(card.index, card.name)).join("");
  const enabled = Boolean(me) && isMyTurn(state) && !me.bankrupt && otherPlayers.length > 0;
  [...tradeForm.elements].forEach((element) => {
    if (element.id !== "trade-submit") element.disabled = !enabled;
  });
  tradeSubmit.disabled = !enabled;
  renderTradeOffer(state);
}

function updateControls(state) {
  const me = getMe(state);
  const mine = Boolean(me) && isMyTurn(state) && !me.bankrupt;
  rollBtn.disabled = !mine || me.hasRolled;
  buyBtn.disabled = !state.canBuy;
  endBtn.disabled = !mine || !me.hasRolled;
}

function openPropertyModal(index) {
  activePropertyIndex = index;
  if (!currentState) return;
  const card = currentState.propertyCards.find((item) => item.index === index);
  const space = currentState.board[index];
  const owner = card?.ownerName || "Bank";
  propertyModalBody.innerHTML = `
    <div class="modal-band" style="background:${space.color ? `var(--${space.color})` : "linear-gradient(90deg, #6366F1, #22C55E)"}"></div>
    <h3>${space.name}</h3>
    <p class="modal-subtitle">${space.type} • Owner: ${owner}</p>
    <div class="modal-grid">
      <span>Price <strong>${space.price ? `$${space.price}` : "-"}</strong></span>
      <span>Rent <strong>${card ? `$${card.rent}` : "-"}</strong></span>
      <span>Upgrades <strong>${card ? card.levelLabel : "-"}</strong></span>
      <span>Mortgage <strong>${card ? `$${card.mortgage}` : "-"}</strong></span>
    </div>
  `;
  buildBtn.disabled = !card?.canBuild;
  sellBtn.disabled = !card?.canSell;
  propertyModal.showModal();
}

function renderState(state) {
  currentState = state;
  roomLabel.textContent = `Room: ${state.roomId}`;
  messageLabel.textContent = `Message: ${state.lastMessage}`;
  turnBanner.textContent = state.started ? `${state.currentTurnName}'s Turn` : "Waiting for players";
  winnerLabel.textContent = state.winner ? `${state.winner} wins the table.` : "";
  const rollKey = state.lastRoll ? state.lastRoll.join("-") : "none";
  rollLabel.textContent = state.lastRoll ? `Dice ${state.lastRoll[0]} + ${state.lastRoll[1]}` : "No roll yet";
  if (rollKey !== lastRollKey && state.lastRoll) {
    rollLabel.classList.remove("roll-pop");
    void rollLabel.offsetWidth;
    rollLabel.classList.add("roll-pop");
  }
  lastRollKey = rollKey;
  renderPlayers(state);
  renderLeaderboard(state);
  renderBoard(state);
  renderPropertyCards(state);
  renderLog(state);
  renderTradeControls(state);
  updateControls(state);
}

function connect(roomId, name) {
  if (socket) socket.close();
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  socket = new WebSocket(`${protocol}://${window.location.host}/ws`);

  socket.addEventListener("open", () => {
    setConnected(true);
    send("join", { roomId, name });
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
  connect(roomInput.value.trim() || "demo", nameInput.value.trim() || "Player");
});

rollBtn.addEventListener("click", () => send("roll"));
buyBtn.addEventListener("click", () => send("buy"));
endBtn.addEventListener("click", () => send("end_turn"));

tradeTarget.addEventListener("change", () => currentState && renderTradeControls(currentState));
tradeForm.addEventListener("submit", (event) => {
  event.preventDefault();
  send("trade_offer", {
    toPlayerId: tradeTarget.value,
    offerProperty: tradeOfferProperty.value || null,
    requestProperty: tradeRequestProperty.value || null,
    offerMoney: Number(tradeOfferMoney.value || 0),
    requestMoney: Number(tradeRequestMoney.value || 0),
  });
});

buildBtn.addEventListener("click", () => {
  if (activePropertyIndex !== null) send("build", { propertyIndex: activePropertyIndex });
});

sellBtn.addEventListener("click", () => {
  if (activePropertyIndex !== null) send("sell", { propertyIndex: activePropertyIndex });
});

closeModalBtn.addEventListener("click", () => propertyModal.close());
propertyModal.addEventListener("click", (event) => {
  const rect = propertyModal.getBoundingClientRect();
  const isOutside = event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom;
  if (isOutside) propertyModal.close();
});

setConnected(false);
