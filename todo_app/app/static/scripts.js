// JavaScript to interact with todo-backend service

// Use value injected by Jinja, fallback only if not set
// DO NOT redeclare with const/let/var
// const backend_api = window.backend_api || '/todos/';
// assumes: <script>const backend_api = "{{ backend_api }}";</script> in HTML

async function loadTodos() {
  // Fetch todo list from todo-backend
  const res = await fetch(`${backend_api}`);
  const todos = await res.json();
  
  // Split into Todo and Done sections
  const todoList = document.getElementById('todoList');
  const doneList = document.getElementById('doneList');
  
  todoList.innerHTML = '';
  doneList.innerHTML = '';
  
  todos.forEach(todo => {
    const item = document.createElement('li');
    if (todo.completed) {
      // Done section - simple text only
      item.textContent = todo.text;
      doneList.appendChild(item);
    } else {
      // Todo section - add Mark as Done button
      item.innerHTML = `${todo.text} <button onclick="markDone(${todo.id})">Mark as Done</button>`;
      todoList.appendChild(item);
    }
  });
}

async function createTodo() {
  // Post new todo to todo-backend and refresh list
  console.log("Create todo clicked");
  const input = document.getElementById('todoInput');
  if (input.value.length === 0 || input.value.length > 140) {
    alert('Todo must be 1-140 characters long');
    return;
  }

  await fetch(`${backend_api}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: input.value }),
  });
  input.value = '';
  await loadTodos();
}

async function markDone(todoId) {
  await fetch(`${backend_api}${todoId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ completed: true }),
  });
  await loadTodos();  // Refresh lists
}

// Event listeners
document.getElementById('createTodoButton').onclick = createTodo;
window.onload = loadTodos;
