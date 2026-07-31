const STORAGE_KEY = 'tasks';

const TASK_COLORS = ['primary', 'success', 'danger', 'warning', 'info', 'dark'];

function pickTaskColor(tasks) {
  const used = new Set(tasks.map(t => t.color));
  const available = TASK_COLORS.filter(color => !used.has(color));
  if (available.length > 0) return available[0];
  return TASK_COLORS[tasks.length % TASK_COLORS.length];
}

function getTasks() {
  try {
    const tasks = JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
    return migrateTaskColors(tasks);
  } catch {
    return [];
  }
}

function migrateTaskColors(tasks) {
  const used = new Set();
  let changed = false;
  tasks.forEach((task, index) => {
    if (!TASK_COLORS.includes(task.color)) {
      const available = TASK_COLORS.filter(color => !used.has(color));
      task.color = available.length > 0 ? available[0] : TASK_COLORS[index % TASK_COLORS.length];
      changed = true;
    }
    used.add(task.color);
  });
  if (changed) saveTasks(tasks);
  return tasks;
}

function saveTasks(tasks) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
}

function createTask(title, startDate, tasks) {
  return {
    id: Date.now(),
    title: title.trim(),
    completed: false,
    createdAt: new Date().toISOString(),
    startDate: startDate || null,
    color: pickTaskColor(tasks),
  };
}

function isValidStartDate(value) {
  if (!value) return true;
  return /^\d{4}-\d{2}-\d{2}$/.test(value) && !isNaN(new Date(value).getTime());
}

function formatStartDate(startDate) {
  if (!startDate) return '';
  return new Date(`${startDate}T00:00:00`).toLocaleDateString();
}

function renderTaskList() {
  const list = document.getElementById('task-list');
  const tasks = getTasks();
  list.innerHTML = tasks.map(task => `
    <li data-id="${task.id}" class="list-group-item text-bg-${task.color || 'light'} d-flex justify-content-between align-items-center flex-wrap gap-2">
      <span class="fw-medium">${escapeHtml(task.title)}</span>
      <span class="d-flex flex-wrap gap-2 small opacity-75">
        <span>Created ${new Date(task.createdAt).toLocaleDateString()}</span>
        ${task.startDate ? `<span>Start ${formatStartDate(task.startDate)}</span>` : ''}
      </span>
      <button type="button" class="btn btn-sm task-edit-btn" data-action="edit">Edit</button>
    </li>
  `).join('');
}

function startEdit(id) {
  const list = document.getElementById('task-list');
  const li = list.querySelector(`[data-id="${id}"]`);
  const task = getTasks().find(t => t.id === id);
  if (!task) return;

  li.innerHTML = `
    <input type="text" class="edit-input form-control form-control-sm flex-grow-1" value="${escapeHtml(task.title)}" maxlength="255" aria-label="Edit task title">
    <span class="d-flex gap-2">
      <button type="button" class="btn btn-primary btn-sm" data-action="save">Save</button>
      <button type="button" class="btn btn-secondary btn-sm" data-action="cancel">Cancel</button>
    </span>
  `;

  const input = li.querySelector('.edit-input');
  input.focus();
  input.setSelectionRange(input.value.length, input.value.length);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      saveEdit(id, input);
    } else if (e.key === 'Escape') {
      renderTaskList();
    }
  });
}

function saveEdit(id, context) {
  const li = context.closest('li');
  const input = li.querySelector('.edit-input');
  const title = input.value.trim();

  if (!title) {
    errorEl.textContent = 'Task title cannot be empty.';
    errorEl.classList.remove('hidden');
    input.focus();
    return;
  }

  errorEl.classList.add('hidden');
  const tasks = getTasks();
  const task = tasks.find(t => t.id === id);
  task.title = title;
  saveTasks(tasks);
  renderTaskList();
}

const list = document.getElementById('task-list');

list.addEventListener('click', (e) => {
  const btn = e.target.closest('button[data-action]');
  if (!btn) return;
  const id = Number(btn.closest('li').dataset.id);
  if (btn.dataset.action === 'edit') {
    startEdit(id);
  } else if (btn.dataset.action === 'save') {
    saveEdit(id, btn);
  } else if (btn.dataset.action === 'cancel') {
    renderTaskList();
  }
});

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

const form = document.getElementById('task-form');
const input = document.getElementById('title');
const startDateInput = document.getElementById('start-date');
const errorEl = document.getElementById('error');

form.addEventListener('submit', (e) => {
  e.preventDefault();
  const title = input.value.trim();
  const startDate = startDateInput.value;

  if (!title) {
    errorEl.textContent = 'Task title cannot be empty.';
    errorEl.classList.remove('hidden');
    return;
  }

  if (!isValidStartDate(startDate)) {
    errorEl.textContent = 'Start date is not a valid date.';
    errorEl.classList.remove('hidden');
    return;
  }

  errorEl.classList.add('hidden');
  const tasks = getTasks();
  tasks.push(createTask(title, startDate, tasks));
  saveTasks(tasks);
  input.value = '';
  startDateInput.value = '';
  renderTaskList();
});

renderTaskList();
