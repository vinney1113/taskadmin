const API_BASE = '/api';

let tasks = [];
let projects = [];
let currentFilter = 'all';

async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body && body.error) message = body.error;
    } catch {
      // ignore non-JSON error bodies
    }
    throw new Error(message);
  }
  if (res.status === 204) return null;
  return res.json();
}

async function listTasks() {
  return apiFetch('/tasks');
}

async function createTask(payload) {
  return apiFetch('/tasks', { method: 'POST', body: JSON.stringify(payload) });
}

async function updateTask(id, fields) {
  return apiFetch(`/tasks/${id}`, { method: 'PUT', body: JSON.stringify(fields) });
}

async function removeTask(id) {
  return apiFetch(`/tasks/${id}`, { method: 'DELETE' });
}

async function listProjects() {
  return apiFetch('/projects');
}

async function createProject(payload) {
  return apiFetch('/projects', { method: 'POST', body: JSON.stringify(payload) });
}

function projectIcon(name) {
  const normalized = String(name || '').toLowerCase();
  if (normalized.includes('office')) return 'briefcase';
  if (normalized.includes('personal')) return 'user';
  if (normalized.includes('daily') || normalized.includes('study')) return 'book';
  return 'default';
}

function taskCounts(projectId, taskList) {
  const inProject = taskList.filter(t => t.projectId === projectId);
  const completed = inProject.filter(t => t.status === 'completed').length;
  return { total: inProject.length, completed };
}

function overallProgress(taskList) {
  if (taskList.length === 0) return 0;
  return Math.round((taskList.filter(t => t.status === 'completed').length / taskList.length) * 100);
}

function isValidDate(value) {
  if (!value) return true;
  return /^\d{4}-\d{2}-\d{2}$/.test(value) && !isNaN(new Date(value).getTime());
}

function isValidStartDate(value) {
  return isValidDate(value);
}

function formatDate(iso) {
  if (!iso) return '';
  const date = new Date(iso);
  return isNaN(date.getTime()) ? '' : date.toLocaleDateString();
}

function formatStartDate(startDate) {
  return formatDate(`${startDate}T00:00:00`);
}

function renderCard(task) {
  const completed = task.status === 'completed';
  return `
    <li data-id="${task.id}" draggable="true" class="list-group-item text-bg-${task.color || 'light'} d-flex justify-content-between align-items-center flex-wrap gap-2 kanban-card">
      <span class="d-flex align-items-center gap-2">
        <input type="checkbox" class="form-check-input m-0 task-complete" data-action="toggle" ${completed ? 'checked' : ''} aria-label="Mark task completed">
        <span class="fw-medium${completed ? ' text-decoration-line-through' : ''}">${escapeHtml(task.title)}</span>
      </span>
      <span class="d-flex flex-wrap gap-2 small opacity-75">
        <span>Created ${formatDate(task.createdAt)}</span>
        ${task.startDate ? `<span>Start ${formatStartDate(task.startDate)}</span>` : ''}
      </span>
      <span class="d-flex gap-2">
        <button type="button" class="btn btn-sm task-action-btn" data-action="edit">Edit</button>
        <button type="button" class="btn btn-sm task-action-btn" data-action="delete">Delete</button>
      </span>
    </li>
  `;
}

function renderTaskList() {
  document.querySelectorAll('#task-list [data-column]').forEach(column => {
    const cards = column.querySelector('ul');
    const status = column.dataset.column;
    cards.innerHTML = tasks
      .filter(task => task.status === status)
      .filter(task => taskMatchesFilter(task))
      .map(renderCard)
      .join('');
  });
  renderProgress();
  renderTaskGroups();
  renderProjectPicker();
}

function taskMatchesFilter(task) {
  if (currentFilter === 'all') return true;
  if (currentFilter === 'to-do') return task.status === 'prioritize';
  return task.status === currentFilter;
}

function renderProgress() {
  const percent = overallProgress(tasks);
  const label = document.getElementById('progress-percent');
  if (label) label.textContent = `${percent}%`;
  const ring = document.getElementById('progress-ring-bar');
  if (ring) {
    const radius = 52;
    const circumference = 2 * Math.PI * radius;
    ring.style.strokeDasharray = `${circumference}`;
    ring.style.strokeDashoffset = `${circumference * (1 - percent / 100)}`;
  }
}

function renderTaskGroups() {
  const container = document.getElementById('task-groups-list');
  if (!container) return;
  container.innerHTML = projects.map(project => {
    const { total, completed } = taskCounts(project.id, tasks);
    const percent = total === 0 ? 0 : Math.round((completed / total) * 100);
    const initial = escapeHtml((project.name || '?').trim().charAt(0).toUpperCase());
    return `
      <div class="col-12 col-sm-6 col-md-4">
        <div class="task-group-card" data-project="${escapeHtml(project.name)}">
          <div class="task-group-icon" data-icon="${projectIcon(project.name)}" aria-hidden="true">${initial}</div>
          <div class="task-group-info">
            <div class="task-group-name">${escapeHtml(project.name)}</div>
            <div class="task-group-meta">${total} ${total === 1 ? 'Task' : 'Tasks'}</div>
            <div class="progress" role="progressbar" aria-valuenow="${percent}" aria-valuemin="0" aria-valuemax="100">
              <div class="progress-bar" style="width: ${percent}%"></div>
            </div>
          </div>
          <div class="task-group-count">${percent}%</div>
        </div>
      </div>
    `;
  }).join('');
}

function renderProjectPicker() {
  const select = document.getElementById('project');
  if (!select) return;
  select.innerHTML = `
    <option value="">No project</option>
    ${projects.map(p => `<option value="${escapeHtml(p.id)}">${escapeHtml(p.name)}</option>`).join('')}
  `;
}

function setupDragAndDrop() {
  const board = document.getElementById('task-list');
  let draggedId = null;

  board.querySelectorAll('.kanban-column').forEach(column => {
    column.addEventListener('dragenter', (e) => {
      e.preventDefault();
      column.classList.add('drag-over');
    });
    column.addEventListener('dragleave', (e) => {
      if (!column.contains(e.relatedTarget)) {
        column.classList.remove('drag-over');
      }
    });
    column.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
    });
    column.addEventListener('drop', async (e) => {
      e.preventDefault();
      column.classList.remove('drag-over');
      if (!draggedId) return;
      const task = tasks.find(t => t.id === draggedId);
      if (!task) return;
      const status = column.dataset.column;
      if (task.status === status) return;
      try {
        await updateTask(draggedId, { ...task, status });
        task.status = status;
        renderTaskList();
      } catch (err) {
        showError(err.message);
      }
    });
  });

  board.addEventListener('dragstart', (e) => {
    const card = e.target.closest('li[data-id]');
    if (!card) return;
    draggedId = card.dataset.id;
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', draggedId);
    requestAnimationFrame(() => card.classList.add('dragging'));
  });

  board.addEventListener('dragend', () => {
    draggedId = null;
    board.querySelectorAll('.kanban-column').forEach(c => c.classList.remove('drag-over'));
    board.querySelectorAll('.dragging').forEach(c => c.classList.remove('dragging'));
  });
}

function setupFilterChips() {
  const chips = document.getElementById('filter-chips');
  if (!chips) return;
  chips.addEventListener('click', (e) => {
    const chip = e.target.closest('.filter-chip');
    if (!chip) return;
    chips.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    currentFilter = chip.dataset.filter;
    renderTaskList();
  });
}

function openProjectModal() {
  const modal = document.getElementById('project-modal');
  if (!modal) return;
  hideProjectError();
  modal.classList.add('show');
  modal.setAttribute('aria-hidden', 'false');
  const name = document.getElementById('project-name');
  if (name) name.focus();
}

function closeProjectModal() {
  const modal = document.getElementById('project-modal');
  if (!modal) return;
  modal.classList.remove('show');
  modal.setAttribute('aria-hidden', 'true');
}

function hideProjectError() {
  projectErrorEl.classList.add('hidden');
}

function showProjectError(message) {
  projectErrorEl.textContent = message;
  projectErrorEl.classList.remove('hidden');
}

function setupProjectModal() {
  const modal = document.getElementById('project-modal');
  if (!modal) return;
  document.getElementById('add-project-btn').addEventListener('click', openProjectModal);
  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeProjectModal();
    if (e.target.closest('[data-action="close-project-modal"]')) closeProjectModal();
  });
  modal.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeProjectModal();
  });
}

const projectForm = document.getElementById('project-form');
const projectErrorEl = document.getElementById('project-error');

projectForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const nameInput = document.getElementById('project-name');
  const startInput = document.getElementById('project-start');
  const endInput = document.getElementById('project-end');
  const descInput = document.getElementById('project-description');

  const name = nameInput.value.trim();

  if (!name) {
    showProjectError('Project name cannot be empty.');
    nameInput.focus();
    return;
  }

  if (!isValidDate(startInput.value) || !isValidDate(endInput.value)) {
    showProjectError('Start and end dates must be valid dates.');
    return;
  }

  if (startInput.value && endInput.value && endInput.value < startInput.value) {
    showProjectError('End date cannot be before start date.');
    return;
  }

  if (projects.some(p => p.name.toLowerCase() === name.toLowerCase())) {
    showProjectError('A project with that name already exists.');
    return;
  }

  hideProjectError();
  try {
    const project = await createProject({
      name,
      icon: 'default',
      startDate: startInput.value || null,
      endDate: endInput.value || null,
      description: descInput.value.trim(),
    });
    projects.push(project);
  } catch (err) {
    showProjectError(err.message);
    return;
  }
  nameInput.value = '';
  startInput.value = '';
  endInput.value = '';
  descInput.value = '';
  closeProjectModal();
  renderTaskList();
});

function startEdit(id) {
  const list = document.getElementById('task-list');
  if (list.querySelector('.edit-input')) {
    renderTaskList();
  }
  const li = list.querySelector(`[data-id="${id}"]`);
  const task = tasks.find(t => t.id === id);
  if (!task || !li) return;

  hideError();
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
    if (e.isComposing) return;
    if (e.key === 'Enter') {
      e.preventDefault();
      saveEdit(id, input);
    } else if (e.key === 'Escape') {
      e.preventDefault();
      hideError();
      renderTaskList();
    }
  });
}

async function saveEdit(id, trigger) {
  const li = trigger.closest('li');
  const input = li ? li.querySelector('.edit-input') : null;
  const task = tasks.find(t => t.id === id);
  if (!task || !input) return;

  const title = input.value.trim();

  if (!title) {
    errorEl.textContent = 'Task title cannot be empty.';
    errorEl.classList.remove('hidden');
    input.focus();
    return;
  }

  hideError();
  try {
    const updated = await updateTask(id, { ...task, title });
    const index = tasks.findIndex(t => t.id === id);
    if (index !== -1) tasks[index] = updated;
  } catch (err) {
    showError(err.message);
    return;
  }
  renderTaskList();
}

async function deleteTask(id) {
  const task = tasks.find(t => t.id === id);
  if (!task) return;
  if (!window.confirm(`Delete task "${task.title}"?`)) return;
  try {
    await removeTask(id);
    tasks = tasks.filter(t => t.id !== id);
  } catch (err) {
    showError(err.message);
    return;
  }
  renderTaskList();
}

const list = document.getElementById('task-list');

list.addEventListener('click', (e) => {
  const btn = e.target.closest('button[data-action]');
  if (!btn) return;
  const id = btn.closest('li').dataset.id;
  if (btn.dataset.action === 'edit') {
    startEdit(id);
  } else if (btn.dataset.action === 'save') {
    saveEdit(id, btn);
  } else if (btn.dataset.action === 'cancel') {
    hideError();
    renderTaskList();
  } else if (btn.dataset.action === 'delete') {
    deleteTask(id);
  }
});

list.addEventListener('change', async (e) => {
  const checkbox = e.target.closest('input[data-action="toggle"]');
  if (!checkbox) return;
  const id = checkbox.closest('li').dataset.id;
  const task = tasks.find(t => t.id === id);
  if (!task) return;
  const status = checkbox.checked ? 'completed' : 'in-progress';
  try {
    await updateTask(id, { ...task, status });
    task.status = status;
  } catch (err) {
    showError(err.message);
    return;
  }
  renderTaskList();
});

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function showError(message) {
  errorEl.textContent = message;
  errorEl.classList.remove('hidden');
}

function hideError() {
  errorEl.classList.add('hidden');
}

const form = document.getElementById('task-form');
const input = document.getElementById('title');
const startDateInput = document.getElementById('start-date');
const projectSelect = document.getElementById('project');
const errorEl = document.getElementById('error');

const viewTaskBtn = document.getElementById('view-task-btn');
if (viewTaskBtn) {
  viewTaskBtn.addEventListener('click', () => {
    document.getElementById('task-list').scrollIntoView({ behavior: 'smooth' });
  });
}

form.addEventListener('submit', async (e) => {
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

  hideError();
  try {
    const task = await createTask({
      title,
      startDate: startDate || null,
      projectId: projectSelect ? projectSelect.value || null : null,
    });
    tasks.push(task);
  } catch (err) {
    showError(err.message);
    return;
  }
  input.value = '';
  startDateInput.value = '';
  renderTaskList();
});

async function loadAll() {
  try {
    const [taskList, projectList] = await Promise.all([listTasks(), listProjects()]);
    tasks = taskList;
    projects = projectList;
  } catch (err) {
    showError(`Failed to load data: ${err.message}`);
    tasks = [];
    projects = [];
  }
  renderTaskList();
}

setupDragAndDrop();
setupFilterChips();
setupProjectModal();
loadAll();
