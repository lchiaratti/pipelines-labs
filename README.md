# Task Manager - Pipelines Labs

Aplicação full-stack simples para gerenciamento de tarefas, usada como laboratório de CI/CD com GitHub Actions.

## Visão Geral

O projeto é composto por:

- Backend em FastAPI (`main.py`)
- Banco local SQLite (`tasks.db`)
- Frontend estático (`static/index.html`, `static/script.js`, `static/style.css`)
- Testes automatizados com `pytest` (`tests/test_main.py`)
- Pipeline CI/CD em `.github/workflows/pipeline.yml`

Fluxo funcional:

1. O frontend chama a API (`/api/*`) via `fetch`.
2. A API persiste tarefas no SQLite usando SQLAlchemy.
3. A pipeline valida qualidade, segurança, testes, build Docker, testes de integração/performance e estágios de deploy.

## Estrutura do Repositório

```text
.
├── .github/workflows/
│   ├── pipeline.yml
│   └── locustfile.py
├── main.py
├── requirements.txt
├── Dockerfile
├── static/
│   ├── index.html
│   ├── script.js
│   └── style.css
└── tests/
    └── test_main.py
```

## Backend (FastAPI)

Arquivo principal: `main.py`.

### Principais recursos

- CRUD de tarefas
- Filtros por status e prioridade
- Estatísticas agregadas (`/api/stats`)
- Servimento de arquivos estáticos para o frontend

### Modelo de tarefa

Campos persistidos:

- `id` (int)
- `title` (str)
- `description` (str | null)
- `completed` (bool)
- `priority` (`low` | `medium` | `high` por convenção do frontend)
- `created_at` (datetime UTC)
- `updated_at` (datetime UTC)

### Endpoints

- `GET /` retorna o HTML da aplicação
- `GET /api/health` health check
- `GET /api/tasks` lista tarefas com filtros opcionais:
  - `skip`
  - `limit`
  - `completed`
  - `priority`
- `POST /api/tasks` cria tarefa
- `GET /api/tasks/{task_id}` busca por ID
- `PUT /api/tasks/{task_id}` atualiza tarefa
- `DELETE /api/tasks/{task_id}` remove tarefa
- `GET /api/stats` retorna estatísticas (`total`, `completed`, `pending`, `high_priority`)

## Frontend

Arquivos em `static/`.

- `index.html`: layout da aplicação (dashboard, filtros, modal)
- `script.js`: lógica de interface, chamadas de API e manipulação de estado
- `style.css`: estilos e responsividade

Comportamentos importantes:

- Carrega tarefas e estatísticas ao iniciar
- Permite criar, editar, concluir e excluir tarefas
- Filtro por status, prioridade e busca por texto
- Insere dados de exemplo automaticamente no primeiro carregamento (quando não há tarefas)

## Testes

Arquivo: `tests/test_main.py`.

Cobertura principal:

- Health check
- CRUD completo
- Filtros e paginação
- Estatísticas
- Acesso à página principal
- Validações básicas

O teste usa banco SQLite local de teste (`test.db`) com setup/teardown por função.

## Como Rodar Localmente

### Pré-requisitos

- Python 3.11+ (recomendado)
- `pip`

### 1) Instalar dependências

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2) Executar aplicação

```bash
python main.py
```

A aplicação sobe em `http://localhost:8000`.

### 3) Rodar testes

```bash
pytest -v --tb=short
```

### 4) Rodar lint/format checks localmente (opcional)

```bash
pip install flake8 black isort
black --check --diff .
isort --profile black --check-only --diff .
flake8 . --count --show-source --statistics --max-line-length=88 --extend-ignore=E203,W503
```

### Rodando com Docker

```bash
docker build -t task-manager:local .
docker run --rm -p 8000:8000 task-manager:local
```

## Pipeline GitHub Actions

Arquivo: `.github/workflows/pipeline.yml`.

### Gatilhos

A pipeline roda em:

- `push` nas branches `main` e `develop`
- `pull_request` para `main`
- execução manual (`workflow_dispatch`)

### Jobs e ordem de execução

1. `lint`
2. `test` (matrix Python 3.9/3.10/3.11)
3. `security`
4. `build`
5. `integration-test` (apenas em eventos que não são PR)
6. `performance-test` (apenas em eventos que não são PR)
7. `deploy-staging` (push em `develop`)
8. `deploy-production` (push em `main`)
9. `notify`

### O que cada job faz

- `lint`: executa `black`, `isort` e `flake8`
- `test`: roda `pytest` com cobertura e envia para Codecov (Python 3.11)
- `security`: roda `pip-audit` e `bandit`
- `build`: builda imagem Docker multi-arquitetura e faz push (exceto PR)
- `integration-test`: build local da imagem e testes HTTP de ponta a ponta
- `performance-test`: build local da imagem e teste de carga com Locust
- `deploy-*`: placeholders de deploy por ambiente
- `notify`: saída final de status de deploy

### Segredos necessários no GitHub

Configurar em **Settings > Secrets and variables > Actions**:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

Observações:

- Sem esses segredos, etapas de login/push Docker podem falhar.
- Em PRs, a pipeline já evita push de imagem (`push: false`).

### Como executar a pipeline manualmente

1. Acesse a aba **Actions** no GitHub.
2. Selecione o workflow **CI/CD Pipeline - Task Manager**.
3. Clique em **Run workflow**.
4. Escolha a branch e execute.

### Como acompanhar falhas

1. Abra o run com falha em **Actions**.
2. Entre no job e step que falhou.
3. Leia o log do comando executado.
4. Corrija localmente, faça commit e push para disparar novo run.

### Melhorias futuras recomendadas

- Implementar deploy real nos jobs `deploy-staging` e `deploy-production`
- Publicar artefatos de performance (relatórios Locust)
- Adicionar validação estrita de valores de prioridade no backend
- Adicionar migrações de banco (ex.: Alembic)
