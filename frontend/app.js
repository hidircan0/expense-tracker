const API = '/api/v1';
const $ = (id) => document.getElementById(id);
let mode = 'login';
let token = localStorage.getItem('expense_token');
let categories = [];
let toastTimer;

function authHeaders() { return { Authorization: `Bearer ${token}` }; }
function localDateValue(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}
function money(value, currency = 'TRY') {
  return new Intl.NumberFormat('tr-TR', { style: 'currency', currency }).format(Number(value));
}
function showToast(message) {
  $('toast').textContent = message;
  $('toast').classList.remove('hidden');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => $('toast').classList.add('hidden'), 2600);
}
function setMode(nextMode) {
  mode = nextMode;
  document.querySelectorAll('.tab').forEach((tab) => tab.classList.toggle('active', tab.dataset.mode === mode));
  $('name-wrap').classList.toggle('hidden', mode === 'login');
  $('auth-title').textContent = mode === 'login' ? 'Tekrar hoş geldin' : 'Aramıza katıl';
  $('auth-subtitle').textContent = mode === 'login' ? 'Hesabına giriş yap ve devam et.' : 'Hemen ücretsiz hesabını oluştur.';
  $('auth-submit').innerHTML = mode === 'login' ? 'Giriş yap <span>→</span>' : 'Hesap oluştur <span>→</span>';
  $('password').autocomplete = mode === 'login' ? 'current-password' : 'new-password';
  $('auth-error').classList.add('hidden');
}
function showAuth() {
  token = null;
  localStorage.removeItem('expense_token');
  $('app-view').classList.add('hidden');
  $('auth-view').classList.remove('hidden');
  $('logout').classList.add('hidden');
}
async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, options);
  if (response.status === 401) {
    showAuth();
    throw new Error('Oturumun sona erdi. Lütfen tekrar giriş yap.');
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = Array.isArray(body.detail) ? body.detail.map((item) => item.msg).join(', ') : body.detail;
    throw new Error(detail || 'Bir hata oluştu. Tekrar dener misin?');
  }
  if (response.status === 204) return null;
  return response.json();
}
async function handleAuth(event) {
  event.preventDefault();
  const button = $('auth-submit');
  const error = $('auth-error');
  button.disabled = true;
  error.classList.add('hidden');
  try {
    const email = $('email').value.trim().toLowerCase();
    const password = $('password').value;
    if (mode === 'register') {
      await request('/auth/register', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password, full_name: $('full-name').value.trim() }) });
    }
    const form = new URLSearchParams({ username: email, password });
    const result = await request('/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: form });
    token = result.access_token;
    localStorage.setItem('expense_token', token);
    await loadApp();
  } catch (err) {
    error.textContent = err.message;
    error.classList.remove('hidden');
  } finally {
    button.disabled = false;
  }
}
async function loadApp() {
  const user = await request('/auth/me', { headers: authHeaders() });
  categories = await request('/categories/', { headers: authHeaders() });
  $('user-name').textContent = `${user.full_name.split(' ')[0]} 👋`;
  $('today').textContent = new Intl.DateTimeFormat('tr-TR', { dateStyle: 'long' }).format(new Date());
  $('date').value = localDateValue(new Date());
  $('category').innerHTML = categories.map((category) => `<option value="${category.id}">${escapeHtml(category.name)}</option>`).join('');
  $('auth-view').classList.add('hidden');
  $('app-view').classList.remove('hidden');
  $('logout').classList.remove('hidden');
  await Promise.all([loadExpenses(), loadSummary()]);
}
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character]);
}
async function loadExpenses() {
  const expenses = await request('/expenses/?limit=50', { headers: authHeaders() });
  $('expense-badge').textContent = `${expenses.length} kayıt`;
  if (!expenses.length) {
    $('expense-list').innerHTML = '<div class="empty">Henüz harcama eklemedin.<br><span>İlk kaydını soldaki formdan ekleyebilirsin.</span></div>';
    return;
  }
  const categoryNames = new Map(categories.map((category) => [category.id, category.name]));
  $('expense-list').innerHTML = expenses.map((expense) => `
    <article class="expense-item">
      <span class="expense-symbol">${symbolFor(categoryNames.get(expense.category_id))}</span>
      <div class="expense-info"><strong>${escapeHtml(expense.description)}</strong><small>${escapeHtml(categoryNames.get(expense.category_id) || 'Kategori')} · ${new Intl.DateTimeFormat('tr-TR').format(new Date(`${expense.date}T12:00:00`))}</small></div>
      <div class="expense-right"><strong>${money(expense.amount, expense.currency)}</strong><button type="button" data-delete="${expense.id}" aria-label="Harcamayı sil">Sil</button></div>
    </article>`).join('');
  document.querySelectorAll('[data-delete]').forEach((button) => button.addEventListener('click', () => deleteExpense(button.dataset.delete)));
}
function symbolFor(category = '') {
  const normalized = category.toLocaleLowerCase('tr-TR');
  if (normalized.includes('yemek') || normalized.includes('food')) return '⌁';
  if (normalized.includes('ulaşım') || normalized.includes('transport')) return '↗';
  if (normalized.includes('kira') || normalized.includes('rent')) return '⌂';
  if (normalized.includes('eğlence') || normalized.includes('entertainment')) return '✳';
  return '◌';
}
async function loadSummary() {
  const now = new Date();
  const start = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-01`;
  const end = localDateValue(new Date(now.getFullYear(), now.getMonth() + 1, 0));
  const summary = await request(`/analytics/summary?start_date=${start}&end_date=${end}`, { headers: authHeaders() });
  $('month-total').textContent = money(summary.total);
  $('month-count').textContent = summary.total ? 'İçinde bulunduğumuz ay' : 'Henüz harcama yok';
  const top = [...summary.by_category].sort((a, b) => Number(b.amount) - Number(a.amount))[0];
  $('top-category').textContent = top ? top.category_name : '—';
  $('top-category-total').textContent = top ? money(top.amount) : 'Kategori özeti';
}
async function addExpense(event) {
  event.preventDefault();
  const message = $('expense-message');
  message.classList.add('hidden');
  const payload = { amount: $('amount').value, currency: $('currency').value, description: $('description').value.trim(), date: $('date').value, category_id: Number($('category').value) };
  try {
    await request('/expenses/', { method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    $('expense-form').reset();
    $('date').value = localDateValue(new Date());
    if (categories.length) $('category').value = String(categories[0].id);
    await Promise.all([loadExpenses(), loadSummary()]);
    showToast('Harcama kaydedildi.');
  } catch (err) {
    message.textContent = err.message;
    message.className = 'message error';
  }
}
async function deleteExpense(id) {
  if (!confirm('Bu harcamayı silmek istiyor musun?')) return;
  try {
    await request(`/expenses/${id}`, { method: 'DELETE', headers: authHeaders() });
    await Promise.all([loadExpenses(), loadSummary()]);
    showToast('Harcama silindi.');
  } catch (err) { showToast(err.message); }
}
document.querySelectorAll('.tab').forEach((tab) => tab.addEventListener('click', () => setMode(tab.dataset.mode)));
$('auth-form').addEventListener('submit', handleAuth);
$('expense-form').addEventListener('submit', addExpense);
$('logout').addEventListener('click', showAuth);
if (token) loadApp().catch((error) => { showAuth(); showToast(error.message); });
