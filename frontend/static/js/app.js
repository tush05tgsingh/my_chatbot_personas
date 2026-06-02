/* ── State ────────────────────────────────────────────────────────────────── */
const state = {
  token: localStorage.getItem('token'),
  username: localStorage.getItem('username'),
  personas: [],
  sessions: [],
  activeSessionId: null,
  activePersona: null,
  isLoading: false,
};

/* ── API ──────────────────────────────────────────────────────────────────── */
const API = window.location.origin;

async function apiFetch(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (state.token) headers['Authorization'] = `Bearer ${state.token}`;

  const res = await fetch(`${API}${path}`, { ...options, headers });
  if (res.status === 204) return null;
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Request failed');
  return data;
}

/* ── Auth ─────────────────────────────────────────────────────────────────── */
async function login(username, password) {
  const form = new URLSearchParams({ username, password });
  const res = await fetch(`${API}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: form,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Login failed');
  return data;
}

async function register(email, username, password) {
  return apiFetch('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, username, password }),
  });
}

async function guestLogin() {
  return apiFetch('/auth/guest', { method: 'POST' });
}

function saveAuth(token, username) {
  state.token = token;
  state.username = username;
  localStorage.setItem('token', token);
  localStorage.setItem('username', username);
}

function logout() {
  state.token = null;
  state.username = null;
  localStorage.removeItem('token');
  localStorage.removeItem('username');
  showAuth();
}

/* ── Personas ─────────────────────────────────────────────────────────────── */
async function loadPersonas() {
  state.personas = await apiFetch('/personas');
  renderPersonaGrid();
}

function renderPersonaGrid() {
  const grid = document.getElementById('persona-grid');
  grid.innerHTML = state.personas.map(p => `
    <div class="persona-card" data-key="${p.key}">
      <span class="persona-card-avatar">${p.avatar}</span>
      <div class="persona-card-name">${p.name}</div>
      <div class="persona-card-desc">${p.description}</div>
    </div>
  `).join('');
  grid.querySelectorAll('.persona-card').forEach(card => {
    card.addEventListener('click', () => startNewSession(card.dataset.key));
  });
}

function getPersona(key) {
  return state.personas.find(p => p.key === key);
}

/* ── Sessions ─────────────────────────────────────────────────────────────── */
async function loadSessions() {
  state.sessions = await apiFetch('/sessions');
  renderSessions();
}

function renderSessions() {
  const list = document.getElementById('sessions-list');
  if (!state.sessions.length) {
    list.innerHTML = '<p class="sessions-empty">No chats yet</p>';
    return;
  }
  list.innerHTML = state.sessions.map(s => {
    const persona = getPersona(s.persona_key);
    const avatar = persona ? persona.avatar : '💬';
    const active = s.id === state.activeSessionId ? 'active' : '';
    const date = new Date(s.updated_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    return `
      <div class="session-item ${active}" data-id="${s.id}">
        <span class="session-item-avatar">${avatar}</span>
        <div class="session-item-info">
          <div class="session-item-title">${s.title}</div>
          <div class="session-item-meta">${date}</div>
        </div>
      </div>`;
  }).join('');
  list.querySelectorAll('.session-item').forEach(item => {
    item.addEventListener('click', () => openSession(item.dataset.id));
  });
}

async function startNewSession(personaKey) {
  const persona = getPersona(personaKey);
  const data = await apiFetch('/sessions', {
    method: 'POST',
    body: JSON.stringify({ persona_key: personaKey }),
  });
  state.sessions.unshift(data);
  state.activeSessionId = data.id;
  state.activePersona = persona;
  renderSessions();
  openChatView(persona, []);
}

async function openSession(sessionId) {
  const data = await apiFetch(`/sessions/${sessionId}`);
  const persona = getPersona(data.persona_key);
  state.activeSessionId = sessionId;
  state.activePersona = persona;
  renderSessions();
  openChatView(persona, data.messages);
}

async function deleteActiveSession() {
  if (!state.activeSessionId) return;
  if (!confirm('Delete this chat?')) return;
  await apiFetch(`/sessions/${state.activeSessionId}`, { method: 'DELETE' });
  state.sessions = state.sessions.filter(s => s.id !== state.activeSessionId);
  state.activeSessionId = null;
  state.activePersona = null;
  renderSessions();
  showPersonaPicker();
}

/* ── Chat ─────────────────────────────────────────────────────────────────── */
function openChatView(persona, messages) {
  document.getElementById('persona-picker').classList.add('hidden');
  const view = document.getElementById('chat-view');
  view.classList.remove('hidden');

  document.getElementById('chat-avatar').textContent = persona.avatar;
  document.getElementById('chat-persona-name').textContent = persona.name;
  document.getElementById('chat-persona-desc').textContent = persona.description;

  const msgContainer = document.getElementById('messages');
  msgContainer.innerHTML = '';
  messages.forEach(m => appendMessage(m.role, m.content));
  scrollToBottom();
}

function showPersonaPicker() {
  document.getElementById('chat-view').classList.add('hidden');
  document.getElementById('persona-picker').classList.remove('hidden');
}

function appendMessage(role, content) {
  const container = document.getElementById('messages');
  const persona = state.activePersona;
  const avatarContent = role === 'user' ? '👤' : (persona ? persona.avatar : '🤖');

  const div = document.createElement('div');
  div.className = `message ${role}`;
  div.innerHTML = `
    <div class="message-avatar">${avatarContent}</div>
    <div class="message-bubble">${escapeHtml(content)}</div>`;
  container.appendChild(div);
  return div;
}

function showTyping() {
  const container = document.getElementById('messages');
  const div = document.createElement('div');
  div.className = 'message assistant';
  div.id = 'typing-indicator';
  div.innerHTML = `
    <div class="message-avatar">${state.activePersona ? state.activePersona.avatar : '🤖'}</div>
    <div class="message-bubble">
      <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    </div>`;
  container.appendChild(div);
  scrollToBottom();
  return div;
}

function removeTyping() {
  document.getElementById('typing-indicator')?.remove();
}

async function sendMessage() {
  const input = document.getElementById('message-input');
  const message = input.value.trim();
  if (!message || state.isLoading || !state.activeSessionId) return;

  state.isLoading = true;
  input.value = '';
  resizeTextarea(input);
  document.getElementById('send-btn').disabled = true;

  appendMessage('user', message);
  scrollToBottom();
  const typingEl = showTyping();

  try {
    const data = await apiFetch(`/sessions/${state.activeSessionId}/chat`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
    removeTyping();
    appendMessage('assistant', data.reply);
    scrollToBottom();

    // Update session updated_at in sidebar
    const s = state.sessions.find(s => s.id === state.activeSessionId);
    if (s) s.updated_at = new Date().toISOString();
    renderSessions();
  } catch (err) {
    removeTyping();
    appendMessage('assistant', `⚠️ Error: ${err.message}`);
  } finally {
    state.isLoading = false;
    document.getElementById('send-btn').disabled = false;
    input.focus();
  }
}

/* ── UI helpers ───────────────────────────────────────────────────────────── */
function scrollToBottom() {
  const el = document.getElementById('messages');
  el.scrollTop = el.scrollHeight;
}

function escapeHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function resizeTextarea(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 140) + 'px';
}

function showError(id, msg) {
  const el = document.getElementById(id);
  el.textContent = msg;
  el.classList.remove('hidden');
}

function hideError(id) {
  document.getElementById(id).classList.add('hidden');
}

/* ── Views ────────────────────────────────────────────────────────────────── */
function showAuth() {
  document.getElementById('auth-screen').classList.remove('hidden');
  document.getElementById('app').classList.add('hidden');
}

async function showApp() {
  document.getElementById('auth-screen').classList.add('hidden');
  document.getElementById('app').classList.remove('hidden');
  const isGuest = state.username?.startsWith('guest_');
  const guestTag = isGuest ? '<span class="guest-badge">guest</span>' : '';
  document.getElementById('username-display').innerHTML = state.username + guestTag;
  await loadPersonas();
  await loadSessions();
}

/* ── Event listeners ─────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {

  // Tab switching
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const target = tab.dataset.tab;
      document.getElementById('login-form').classList.toggle('hidden', target !== 'login');
      document.getElementById('register-form').classList.toggle('hidden', target !== 'register');
    });
  });

  // Login
  document.getElementById('login-form').addEventListener('submit', async e => {
    e.preventDefault();
    hideError('login-error');
    try {
      const data = await login(
        document.getElementById('login-username').value,
        document.getElementById('login-password').value,
      );
      saveAuth(data.access_token, data.username);
      showApp();
    } catch (err) {
      showError('login-error', err.message);
    }
  });

  // Register
  document.getElementById('register-form').addEventListener('submit', async e => {
    e.preventDefault();
    hideError('register-error');
    try {
      const data = await register(
        document.getElementById('reg-email').value,
        document.getElementById('reg-username').value,
        document.getElementById('reg-password').value,
      );
      saveAuth(data.access_token, data.username);
      showApp();
    } catch (err) {
      showError('register-error', err.message);
    }
  });

  // New chat
  document.getElementById('new-chat-btn').addEventListener('click', showPersonaPicker);

  // Delete session
  document.getElementById('delete-session-btn').addEventListener('click', deleteActiveSession);

  // Logout
  document.getElementById('logout-btn').addEventListener('click', logout);

  // Send button
  document.getElementById('send-btn').addEventListener('click', sendMessage);

  // Enter to send (shift+enter = newline)
  document.getElementById('message-input').addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Auto-resize textarea
  document.getElementById('message-input').addEventListener('input', function() {
    resizeTextarea(this);
  });

  // Guest login
  document.getElementById('guest-btn').addEventListener('click', async () => {
    try {
      const data = await guestLogin();
      saveAuth(data.access_token, data.username);
      showApp();
    } catch (err) {
      alert('Could not start guest session: ' + err.message);
    }
  });

  // Init
  if (state.token) {
    showApp().catch(() => logout()); // token expired → back to auth
  } else {
    showAuth();
  }
});