class TaskManager {
    constructor() {
        this.tasks = [];
        this.currentEditId = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadTasks();
        this.loadStats();
    }

    bindEvents() {
        // Modal events
        const addTaskBtn = document.getElementById('addTaskBtn');
        const closeModal = document.getElementById('closeModal');
        const cancelBtn = document.getElementById('cancelBtn');
        const taskForm = document.getElementById('taskForm');

        if (addTaskBtn) addTaskBtn.addEventListener('click', () => this.openModal());
        if (closeModal) closeModal.addEventListener('click', () => this.closeModal());
        if (cancelBtn) cancelBtn.addEventListener('click', () => this.closeModal());
        if (taskForm) taskForm.addEventListener('submit', (e) => this.handleSubmit(e));

        // Filter events
        const statusFilter = document.getElementById('statusFilter');
        const priorityFilter = document.getElementById('priorityFilter');
        const searchInput = document.getElementById('searchInput');

        if (statusFilter) statusFilter.addEventListener('change', () => this.filterTasks());
        if (priorityFilter) priorityFilter.addEventListener('change', () => this.filterTasks());
        if (searchInput) searchInput.addEventListener('input', () => this.filterTasks());

        // Click outside modal to close
        const taskModal = document.getElementById('taskModal');
        if (taskModal) {
            taskModal.addEventListener('click', (e) => {
                if (e.target.id === 'taskModal') {
                    this.closeModal();
                }
            });
        }
    }

    async loadTasks() {
        try {
            this.showLoading(true);
            const response = await fetch('/api/tasks');
            if (!response.ok) throw new Error('Failed to load tasks');

            this.tasks = await response.json();
            this.renderTasks();
        } catch (error) {
            this.showNotification('Erro ao carregar tarefas: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async loadStats() {
        try {
            const response = await fetch('/api/stats');
            if (!response.ok) throw new Error('Failed to load stats');

            const stats = await response.json();
            this.updateStats(stats);
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    updateStats(stats) {
        document.getElementById('totalTasks').textContent = stats.total;
        document.getElementById('completedTasks').textContent = stats.completed;
        document.getElementById('pendingTasks').textContent = stats.pending;
        document.getElementById('highPriorityTasks').textContent = stats.high_priority;
    }

    renderTasks(tasksToRender = null) {
        const container = document.getElementById('tasksContainer');
        const tasks = tasksToRender || this.tasks;

        if (tasks.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-clipboard-list"></i>
                    <h3>Nenhuma tarefa encontrada</h3>
                    <p>Comece criando sua primeira tarefa!</p>
                </div>
            `;
            return;
        }

        container.innerHTML = tasks.map(task => this.createTaskCard(task)).join('');
        this.bindTaskEvents();
    }

    createTaskCard(task) {
        const createdDate = new Date(task.created_at).toLocaleDateString('pt-BR');
        const priorityClass = `priority-${task.priority}`;
        const completedClass = task.completed ? 'completed' : '';

        return `
            <div class="task-card ${priorityClass} ${completedClass}" data-id="${task.id}">
                <div class="task-header">
                    <div>
                        <h3 class="task-title">${this.escapeHtml(task.title)}</h3>
                        <span class="task-priority ${task.priority}">${this.getPriorityLabel(task.priority)}</span>
                    </div>
                    <div class="task-actions">
                        <button class="btn btn-success toggle-btn" onclick="taskManager.toggleTask(${task.id})" title="${task.completed ? 'Marcar como pendente' : 'Marcar como concluída'}">
                            <i class="fas ${task.completed ? 'fa-undo' : 'fa-check'}"></i>
                        </button>
                        <button class="btn btn-edit edit-btn" onclick="taskManager.editTask(${task.id})" title="Editar tarefa">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-danger delete-btn" onclick="taskManager.deleteTask(${task.id})" title="Excluir tarefa">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
                ${task.description ? `<p class="task-description">${this.escapeHtml(task.description)}</p>` : ''}
                <div class="task-meta">
                    <span><i class="fas fa-calendar"></i> Criada em ${createdDate}</span>
                    <span class="task-status">
                        <i class="fas ${task.completed ? 'fa-check-circle' : 'fa-clock'}"></i>
                        ${task.completed ? 'Concluída' : 'Pendente'}
                    </span>
                </div>
            </div>
        `;
    }

    bindTaskEvents() {
        // Events are bound inline in the template for simplicity
        // In a real application, you might use event delegation
    }

    getPriorityLabel(priority) {
        const labels = {
            high: 'Alta',
            medium: 'Média',
            low: 'Baixa'
        };
        return labels[priority] || priority;
    }

    filterTasks() {
        const statusFilter = document.getElementById('statusFilter').value;
        const priorityFilter = document.getElementById('priorityFilter').value;
        const searchTerm = document.getElementById('searchInput').value.toLowerCase();

        let filteredTasks = this.tasks;

        // Filter by status
        if (statusFilter !== '') {
            const isCompleted = statusFilter === 'true';
            filteredTasks = filteredTasks.filter(task => task.completed === isCompleted);
        }

        // Filter by priority
        if (priorityFilter) {
            filteredTasks = filteredTasks.filter(task => task.priority === priorityFilter);
        }

        // Filter by search term
        if (searchTerm) {
            filteredTasks = filteredTasks.filter(task =>
                task.title.toLowerCase().includes(searchTerm) ||
                (task.description && task.description.toLowerCase().includes(searchTerm))
            );
        }

        this.renderTasks(filteredTasks);
    }

    openModal(task = null) {
        const modal = document.getElementById('taskModal');
        const modalTitle = document.getElementById('modalTitle');
        const form = document.getElementById('taskForm');

        if (!modal || !modalTitle || !form) return;

        if (task) {
            modalTitle.textContent = 'Editar Tarefa';
            const taskTitleInput = document.getElementById('taskTitle');
            const taskDescInput = document.getElementById('taskDescription');
            const taskPriorityInput = document.getElementById('taskPriority');

            if (taskTitleInput) taskTitleInput.value = task.title;
            if (taskDescInput) taskDescInput.value = task.description || '';
            if (taskPriorityInput) taskPriorityInput.value = task.priority;
            this.currentEditId = task.id;
        } else {
            modalTitle.textContent = 'Nova Tarefa';
            form.reset();
            this.currentEditId = null;
        }

        modal.classList.add('show');
        const taskTitleInput = document.getElementById('taskTitle');
        if (taskTitleInput) taskTitleInput.focus();
    }

    closeModal() {
        const modal = document.getElementById('taskModal');
        if (modal) {
            modal.classList.remove('show');
        }
        this.currentEditId = null;
    }

    async handleSubmit(e) {
        e.preventDefault();

        const taskTitleInput = document.getElementById('taskTitle');
        const taskDescInput = document.getElementById('taskDescription');
        const taskPriorityInput = document.getElementById('taskPriority');

        if (!taskTitleInput || !taskDescInput || !taskPriorityInput) {
            this.showNotification('Erro: Elementos do formulário não encontrados', 'error');
            return;
        }

        const title = taskTitleInput.value.trim();
        const description = taskDescInput.value.trim();
        const priority = taskPriorityInput.value;

        if (!title) {
            this.showNotification('Título é obrigatório', 'error');
            return;
        }

        const taskData = {
            title,
            description: description || null,
            priority
        };

        try {
            let response;
            if (this.currentEditId) {
                response = await fetch(`/api/tasks/${this.currentEditId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(taskData)
                });
            } else {
                response = await fetch('/api/tasks', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(taskData)
                });
            }

            if (!response.ok) throw new Error('Failed to save task');

            this.showNotification(
                this.currentEditId ? 'Tarefa atualizada com sucesso!' : 'Tarefa criada com sucesso!',
                'success'
            );

            this.closeModal();
            await this.loadTasks();
            await this.loadStats();
        } catch (error) {
            this.showNotification('Erro ao salvar tarefa: ' + error.message, 'error');
        }
    }

    async toggleTask(id) {
        try {
            const task = this.tasks.find(t => t.id === id);
            if (!task) return;

            const response = await fetch(`/api/tasks/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    completed: !task.completed
                })
            });

            if (!response.ok) throw new Error('Failed to update task');

            this.showNotification(
                task.completed ? 'Tarefa marcada como pendente' : 'Tarefa concluída!',
                'success'
            );

            await this.loadTasks();
            await this.loadStats();
        } catch (error) {
            this.showNotification('Erro ao atualizar tarefa: ' + error.message, 'error');
        }
    }

    editTask(id) {
        const task = this.tasks.find(t => t.id === id);
        if (task) {
            this.openModal(task);
        }
    }

    async deleteTask(id) {
        if (!confirm('Tem certeza que deseja excluir esta tarefa?')) {
            return;
        }

        try {
            const response = await fetch(`/api/tasks/${id}`, {
                method: 'DELETE'
            });

            if (!response.ok) throw new Error('Failed to delete task');

            this.showNotification('Tarefa excluída com sucesso!', 'success');

            await this.loadTasks();
            await this.loadStats();
        } catch (error) {
            this.showNotification('Erro ao excluir tarefa: ' + error.message, 'error');
        }
    }

    showLoading(show) {
        const loading = document.getElementById('loading');
        if (loading) {
            if (show) {
                loading.style.display = 'block';
            } else {
                loading.style.display = 'none';
            }
        }
    }

    showNotification(message, type = 'success') {
        const notification = document.getElementById('notification');
        if (!notification) return;

        const messageElement = notification.querySelector('.notification-message');
        const icon = notification.querySelector('i');

        if (messageElement) {
            messageElement.textContent = message;
        }

        if (icon) {
            if (type === 'error') {
                notification.classList.add('error');
                icon.className = 'fas fa-exclamation-circle';
            } else {
                notification.classList.remove('error');
                icon.className = 'fas fa-check-circle';
            }
        }

        notification.classList.add('show');

        setTimeout(() => {
            notification.classList.remove('show');
        }, 3000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the application
const taskManager = new TaskManager();

// Add some sample data on first load (optional)
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('/api/tasks');
        const tasks = await response.json();

        // If no tasks exist, add sample data
        if (tasks.length === 0) {
            const sampleTasks = [
                {
                    title: 'Configurar CI/CD Pipeline',
                    description: 'Implementar pipeline automatizada com GitHub Actions para build, testes e deploy',
                    priority: 'high'
                },
                {
                    title: 'Adicionar testes unitários',
                    description: 'Criar suite completa de testes para cobertura da API',
                    priority: 'medium'
                },
                {
                    title: 'Documentar API endpoints',
                    description: 'Criar documentação completa dos endpoints da API',
                    priority: 'low'
                }
            ];

            for (const task of sampleTasks) {
                await fetch('/api/tasks', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(task)
                });
            }

            // Reload tasks and stats
            await taskManager.loadTasks();
            await taskManager.loadStats();
        }
    } catch (error) {
        console.log('Sample data not added:', error);
    }
});