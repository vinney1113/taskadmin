const STORAGE_KEY = 'tasks';

function getTasks() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
  } catch {
    return [];
  }
}

function saveTasks(tasks) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
}

function createTask(title) {
  return {
    id: Date.now(),
    title: title.trim(),
    completed: false,
    createdAt: new Date().toISOString(),
  };
}

function renderTaskList() {
  const list = document.getElementById('task-list');
  const tasks = getTasks();
  list.innerHTML = tasks.map(task => `
    <li>
      <span class="task-title">${escapeHtml(task.title)}</span>
      <span class="task-date">${new Date(task.createdAt).toLocaleDateString()}</span>
    </li>
  `).join('');
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

const form = document.getElementById('task-form');
const input = document.getElementById('title');
const errorEl = document.getElementById('error');

form.addEventListener('submit', (e) => {
  e.preventDefault();
  const title = input.value.trim();

  if (!title) {
    errorEl.textContent = 'Task title cannot be empty.';
    errorEl.classList.remove('hidden');
    return;
  }

  errorEl.classList.add('hidden');
  const tasks = getTasks();
  tasks.push(createTask(title));
  saveTasks(tasks);
  input.value = '';
  renderTaskList();
});

renderTaskList();
