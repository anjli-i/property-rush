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
const tradePendingRoot = document.getElementById("trade-pending-root");
const tradeModal = document.getElementById("trade-modal");
const openTradeBtn = document.getElementById("open-trade-btn");
const closeTradeModal = document.getElementById("close-trade-modal");
const copyRoomBtn = document.getElementById("copy-room-btn");
const dieOne = document.getElementById("die-one");
const dieTwo = document.getElementById("die-two");
const propertyModal = document.getElementById("property-modal");
const propertyModalBody = document.getElementById("property-modal-body");
const buildBtn = document.getElementById("build-btn");
const sellBtn = document.getElementById("sell-btn");
const closeModalBtn = document.getElementById("close-modal-btn");

let socket = null;
const PLAYER_STORAGE_KEY = "property-rush-player-id";
let playerId = localStorage.getItem(PLAYER_STORAGE_KEY) || null;
if (!playerId && sessionStorage.getItem(PLAYER_STORAGE_KEY)) {
  playerId = sessionStorage.getItem(PLAYER_STORAGE_KEY);
  localStorage.setItem(PLAYER_STORAGE_KEY, playerId);
}
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

function bindTabs(container, selector, onActivate) {
  container.querySelectorAll(selector).forEach((tab) => {
    tab.addEventListener("click", () => {
      const key = tab.dataset.tab || tab.dataset.subtab || tab.dataset.rtab;
      onActivate(key, tab);
    });
  });
}

bindTabs(document, ".column-left .tablist .tab", (key, clicked) => {
  document.querySelectorAll(".column-left .tab").forEach((t) => {
    const on = t.dataset.tab === key;
    t.classList.toggle("active", on);
    t.setAttribute("aria-selected", on);
  });
  document.querySelectorAll(".column-left .tab-panel").forEach((panel) => {
    const id = panel.id;
    const show =
      (key === "table" && id === "panel-table") ||
      (key === "setup" && id === "panel-setup");
    panel.classList.toggle("active", show);
    panel.toggleAttribute("hidden", !show);
  });
});

bindTabs(document.querySelector(".sub-panel"), ".tablist-inline .tab", (key) => {
  document.querySelectorAll(".sub-panel .tab").forEach((t) => {
    const on = t.dataset.subtab === key;
    t.classList.toggle("active", on);
    t.setAttribute("aria-selected", on);
  });
  document.getElementById("pane-portfolio").classList.toggle("active", key === "portfolio");
  document.getElementById("pane-log").classList.toggle("active", key === "log");
  document.getElementById("pane-portfolio").toggleAttribute("hidden", key !== "portfolio");
  document.getElementById("pane-log").toggleAttribute("hidden", key !== "log");
});

bindTabs(document.querySelector(".column-right .tablist"), ".tab", (key) => {
  document.querySelectorAll(".column-right .tablist .tab").forEach((t) => {
    const on = t.dataset.rtab === key;
    t.classList.toggle("active", on);
    t.setAttribute("aria-selected", on);
  });
  document.getElementById("rpanel-players").classList.toggle("active", key === "players");
  document.getElementById("rpanel-ranks").classList.toggle("active", key === "ranks");
  document.getElementById("rpanel-players").toggleAttribute("hidden", key !== "players");
  document.getElementById("rpanel-ranks").toggleAttribute("hidden", key !== "ranks");
});

function openTradeDialog() {
  if (!tradeModal.open) tradeModal.showModal();
  if (currentState) renderTradeControls(currentState);
}

function closeTradeDialog() {
  tradeModal.close();
}

openTradeBtn.addEventListener("click", () => openTradeDialog());
closeTradeModal.addEventListener("click", () => closeTradeDialog());
tradeModal.addEventListener("click", (event) => {
  const rect = tradeModal.getBoundingClientRect();
  const outside =
    event.clientX < rect.left ||
    event.clientX > rect.right ||
    event.clientY < rect.top ||
    event.clientY > rect.bottom;
  if (outside) tradeModal.close();
});

copyRoomBtn.addEventListener("click", async () => {
  const room = roomInput.value.trim() || "demo";
  const url = `${window.location.origin}${window.location.pathname}?room=${encodeURIComponent(room)}`;
  const resetLabel = '<span class="btn-icon" aria-hidden="true">⎘</span> Copy link';
  try {
    await navigator.clipboard.writeText(url);
    copyRoomBtn.innerHTML = "Copied!";
    setTimeout(() => {
      copyRoomBtn.innerHTML = resetLabel;
    }, 1600);
  } catch {
    window.prompt("Copy this link:", url);
  }
});

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
          <p>${player.inJail ? "In jail" : player.bankrupt ? "Bankrupt" : "In game"}</p>
        </div>
      </div>
      <div class="player-stats">
        <span>Cash <strong>$${player.money}</strong></span>
        <span>On <strong>${state.board[player.position].name}</strong></span>
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
        <span>$${entry.assets} net</span>
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
      <span class="tile-meta">${owner ? `Owner: ${owner.name}` : space.price ? `$${space.price}` : "Unowned"}</span>
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

function formatTradeLines(offer) {
  const give = [
    offer.offerPropertyName || null,
    offer.offerMoney ? `$${offer.offerMoney}` : null,
  ].filter(Boolean);
  const get = [
    offer.requestPropertyName || null,
    offer.requestMoney ? `$${offer.requestMoney}` : null,
  ].filter(Boolean);
  return {
    give: give.length ? give.join(" + ") : "—",
    get: get.length ? get.join(" + ") : "—",
  };
}

function renderPendingTrades(state) {
  const offers = state.tradeOffers || [];
  const incoming = offers.filter((o) => o.toPlayerId === state.you);
  const outgoing = offers.filter((o) => o.fromPlayerId === state.you);

  openTradeBtn.classList.toggle("needs-attention", incoming.length > 0);

  if (incoming.length === 0 && outgoing.length === 0) {
    tradePendingRoot.innerHTML = '<p class="trade-empty">No active offers involving you.</p>';
    return;
  }

  const parts = [];
  if (incoming.length) {
    parts.push('<p class="trade-sub">Inbox — answer these</p>');
    incoming.forEach((o) => {
      const { give, get } = formatTradeLines(o);
      parts.push(`
        <div class="trade-pending-card incoming" data-offer-id="${o.id}">
          <div><strong>${o.fromPlayerName}</strong> offers you: <strong>${give}</strong></div>
          <div>They want: <strong>${get}</strong></div>
          <div class="offer-actions">
            <button type="button" class="primary-btn js-trade-accept" data-offer-id="${o.id}">Accept</button>
            <button type="button" class="ghost-btn js-trade-decline" data-offer-id="${o.id}">Decline</button>
          </div>
        </div>
      `);
    });
  }
  if (outgoing.length) {
    parts.push('<p class="trade-sub">Outgoing — waiting on them</p>');
    outgoing.forEach((o) => {
      const { give, get } = formatTradeLines(o);
      parts.push(`
        <div class="trade-pending-card">
          <div>To <strong>${o.toPlayerName}</strong></div>
          <div>You give: <strong>${give}</strong> · You want: <strong>${get}</strong></div>
          <p class="offer-waiting">Waiting for their answer…</p>
        </div>
      `);
    });
  }

  tradePendingRoot.innerHTML = parts.join("");

  tradePendingRoot.querySelectorAll(".js-trade-accept").forEach((btn) => {
    btn.addEventListener("click", () =>
      send("trade_response", { offerId: btn.getAttribute("data-offer-id"), accept: true }),
    );
  });
  tradePendingRoot.querySelectorAll(".js-trade-decline").forEach((btn) => {
    btn.addEventListener("click", () =>
      send("trade_response", { offerId: btn.getAttribute("data-offer-id"), accept: false }),
    );
  });
}

function renderTradeControls(state) {
  const me = getMe(state);
  const myProperties = state.propertyCards.filter((card) => card.ownerId === state.you);
  const otherPlayers = state.players.filter((player) => player.id !== state.you && !player.bankrupt);
  const targetId = tradeTarget.value || otherPlayers[0]?.id || "";
  tradeTarget.innerHTML = otherPlayers.length
    ? otherPlayers.map((player) => optionMarkup(player.id, player.name, player.id === targetId)).join("")
    : optionMarkup("", "No one to trade with", true);
  const targetCards = state.propertyCards.filter((card) => card.ownerId === tradeTarget.value);
  tradeOfferProperty.innerHTML =
    optionMarkup("", "None") + myProperties.map((card) => optionMarkup(card.index, card.name)).join("");
  tradeRequestProperty.innerHTML =
    optionMarkup("", "None") + targetCards.map((card) => optionMarkup(card.index, card.name)).join("");

  const canTrade = Boolean(me) && state.started && !me.bankrupt && otherPlayers.length > 0;
  [...tradeForm.elements].forEach((element) => {
    if (element.id !== "trade-submit") element.disabled = !canTrade;
  });
  tradeSubmit.disabled = !canTrade;

  if (me) {
    tradeOfferMoney.max = me.money;
    const target = state.players.find((p) => p.id === tradeTarget.value);
    tradeRequestMoney.max = target ? target.money : 0;
  }

  renderPendingTrades(state);
}

function updateControls(state) {
  const me = getMe(state);
  const mine = Boolean(me) && isMyTurn(state) && !me.bankrupt;
  rollBtn.disabled = !mine || me.hasRolled;
  buyBtn.disabled = !state.canBuy;
  endBtn.disabled = !mine || !me.hasRolled;

  const meReady = Boolean(me) && !me.bankrupt;
  openTradeBtn.disabled = !meReady || !state.started || state.players.filter((p) => !p.bankrupt).length < 2;
  copyRoomBtn.disabled = !socket || socket.readyState !== WebSocket.OPEN;
}

function openPropertyModal(index) {
  activePropertyIndex = index;
  if (!currentState) return;
  const card = currentState.propertyCards.find((item) => item.index === index);
  const space = currentState.board[index];
  const owner = card?.ownerName || "Bank";
  propertyModalBody.innerHTML = `
    <div class="modal-band" style="background:${space.color ? `var(--${space.color})` : "linear-gradient(90deg, #8b5cf6, #34d399)"}"></div>
    <h3>${space.name}</h3>
    <p class="modal-subtitle">${space.type} · Owner: ${owner}</p>
    <div class="modal-grid">
      <span>Price <strong>${space.price ? `$${space.price}` : "—"}</strong></span>
      <span>Rent <strong>${card ? `$${card.rent}` : "—"}</strong></span>
      <span>Buildings <strong>${card ? card.levelLabel : "—"}</strong></span>
      <span>Mortgage <strong>${card ? `$${card.mortgage}` : "—"}</strong></span>
    </div>
  `;
  buildBtn.disabled = !card?.canBuild;
  sellBtn.disabled = !card?.canSell;
  propertyModal.showModal();
}

function renderDice(state) {
  if (state.lastRoll && state.lastRoll.length === 2) {
    dieOne.textContent = state.lastRoll[0];
    dieTwo.textContent = state.lastRoll[1];
  } else {
    dieOne.textContent = "—";
    dieTwo.textContent = "—";
  }
}

function renderState(state) {
  currentState = state;
  roomLabel.textContent = `Room: ${state.roomId}`;
  messageLabel.textContent = state.lastMessage;
  turnBanner.textContent = state.started ? `${state.currentTurnName}'s turn` : "Waiting for players (need 2)";
  winnerLabel.textContent = state.winner ? `${state.winner} wins.` : "";

  const rollKey = state.lastRoll ? state.lastRoll.join("-") : "none";
  rollLabel.textContent = state.lastRoll ? `${state.lastRoll[0]} + ${state.lastRoll[1]}` : "No roll yet";
  if (rollKey !== lastRollKey && state.lastRoll) {
    rollLabel.classList.remove("roll-pop");
    void rollLabel.offsetWidth;
    rollLabel.classList.add("roll-pop");
  }
  lastRollKey = rollKey;

  renderDice(state);
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
      localStorage.setItem(PLAYER_STORAGE_KEY, playerId);
      document.querySelector('.column-left .tab[data-tab="table"]')?.click();
      return;
    }
    if (message.type === "state") {
      renderState(message);
      return;
    }
    if (message.type === "error") {
      messageLabel.textContent = message.message || "Something went wrong.";
    }
  });

  socket.addEventListener("close", () => {
    setConnected(false);
    rollBtn.disabled = true;
    buyBtn.disabled = true;
    endBtn.disabled = true;
    openTradeBtn.disabled = true;
    copyRoomBtn.disabled = true;
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
  const isOutside =
    event.clientX < rect.left ||
    event.clientX > rect.right ||
    event.clientY < rect.top ||
    event.clientY > rect.bottom;
  if (isOutside) propertyModal.close();
});

function initFromQuery() {
  const params = new URLSearchParams(window.location.search);
  const r = params.get("room");
  if (r) roomInput.value = r;
}

initFromQuery();
setConnected(false);
