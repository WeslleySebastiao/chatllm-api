# 🚀 ChatLLM API
Autor: Weslley da Costa Sebastião

> Esta API orquestra o ciclo de vida (registro e execução) de agentes personalizados, permitindo que eles acessem tools hospedadas localmente no projeto (via pasta `src/mcp/tools`) ou, de forma opcional, um servidor MCP externo.

Este serviço atua como uma central de orquestração para agentes de LLM. Ele simplifica o gerenciamento do ciclo completo, desde o registro e a gestão dos agentes até a execução final, incluindo memória conversacional e telemetria de uso. O projeto também inclui um pipeline de **code review automático** para Pull Requests (PR) e endpoints de dashboard para análise de métricas.

---

## 📌 Sumário

- [Visão geral](#-visão-geral)
- [Principais funcionalidades](#-principais-funcionalidades)
- [Arquitetura e fluxo](#-arquitetura-e-fluxo)
- [Estrutura de pastas](#-estrutura-de-pastas)
- [Requisitos](#-requisitos)
- [Configuração (.env)](#-configuração-env)
- [Como rodar](#-como-rodar)
- [Documentação da API](#-documentação-da-api)
  - [Endpoints principais](#endpoints-principais)
  - [Endpoints de dashboard](#endpoints-de-dashboard)
  - [Endpoints de reviews de PR](#endpoints-de-reviews-de-pr)
- [MCP Tools](#-mcp-tools)
- [Telemetria e memória](#-telemetria-e-memória)
- [Problemas comuns](#-problemas-comuns)

---

## 🧭 Visão geral

O ChatLLM API fornece:

- **Cadastro de agentes** com prompt, modelo e lista de tools permitidas.
- **Execução de agentes** com memória conversacional e rastreamento de custo/uso.
- **Integração com MCP** (local via arquivos ou servidor externo).
- **Pipeline de reviews de PR**, que executa análises automáticas e registra resultados em banco.
- **Endpoints de dashboard** para métricas e relatórios.

---

## ✨ Principais funcionalidades

- **Gerenciamento de agentes** (criação e listagem).
- **Execução de agentes com LangChain + LangGraph**.
- **Ferramentas extensíveis** via `src/mcp/tools/*`.
- **Banco de dados Supabase (Postgres)** para persistência.
- **Memória de conversas** por sessão.
- **Telemetria de custo e tokens** por execução.
- **Review automático de Pull Requests** com histórico e estatísticas.

---

## 🏗️ Arquitetura e fluxo

### 1) Registro de agentes
- O endpoint `POST /agent` salva a configuração do agente no banco (Supabase).

### 2) Execução
- O endpoint `POST /agent/run/v2`:
  1. Carrega a configuração do agente.
  2. Carrega tools permitidas.
  3. Executa o agente usando LangChain.
  4. Registra telemetria, tokens e custo.

### 3) Reviews de PR
- O endpoint `POST /api/v1/reviews/pr/run`:
  - Exige autenticação com `Authorization: Bearer` e header `X-GitHub-Token`.
  - Executa o pipeline de review e retorna um relatório final.

---

## 🗂️ Estrutura de pastas

```
.
├── main.py                     # Ponto de entrada FastAPI
├── README.md
├── requirements.txt
└── src
    ├── api                      # Rotas HTTP
    │   ├── routes.py            # Agentes + health + list_tools
    │   ├── DashboardViews       # Endpoints do dashboard
    │   └── reviews              # Endpoints de review de PR
    ├── core                     # Configuração e logging
    ├── data                     # Persistência (Supabase/Postgres)
    ├── mcp                      # Loader/registry e tools locais
    ├── models                   # Schemas Pydantic
    ├── services                 # Lógicas de execução de agentes e reviews
    └── utils                    # Logs, helpers, telemetria
```

---

## ✅ Requisitos

- **Python 3.10+**
- **Git**
- **Supabase/Postgres acessível** (para persistência)
- **Chave OpenAI** (para execução de LLM)

---

## ⚙️ Configuração (.env)

O projeto usa `pydantic-settings` para carregar variáveis de ambiente via `.env`. As variáveis abaixo são obrigatórias:

```env
APP_NAME="ChatLLM API"
APP_VERSION="0.6.0"
DEBUG=True

OPENAI_API_KEY="sk-..."
MODEL_NAME="gpt-4o-mini"
FRONT_URL="http://localhost:3000"
API_KEY="sua-chave-de-api"

SUPABASE_DB_USER="postgres"
SUPABASE_DB_PASSWORD="senha"
SUPABASE_DB_HOST="db.xxxxx.supabase.co"
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME="postgres"
```

> ℹ️ **Notas**
> - `MODEL_NAME` é usado como fallback/valor padrão na aplicação.
> - `API_KEY` protege o endpoint de review de PR.

---

## ▶️ Como rodar

1) **Clone o repositório**
```bash
git clone [URL_DO_SEU_REPOSITORIO]
cd [NOME_DA_PASTA_DO_PROJETO]
```

2) **Crie um ambiente virtual**
```bash
python3 -m venv venv
source venv/bin/activate
```

3) **Instale as dependências**
```bash
pip install -r requirements.txt
```

4) **Configure o `.env`** (conforme exemplo acima)

5) **Inicie a aplicação**
```bash
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

A aplicação ficará disponível em: `http://localhost:8080`

---

## 📖 Documentação da API

A documentação interativa (Swagger) fica em:

- **http://localhost:8080/docs**

A documentação alternativa (ReDoc):

- **http://localhost:8080/redoc**

---

### Endpoints principais

#### ✅ Health Check
**GET `/health`**

Resposta:
```json
{
  "status": "ok",
  "app": "ChatLLM API",
  "version": "0.6.0"
}
```

---

#### 📌 Criar agente
**POST `/agent`**

Body:
```json
{
  "name": "Agente Suporte",
  "description": "Atende clientes",
  "provider": "openai",
  "model": "gpt-4o-mini",
  "prompt": "Você é um atendente virtual...",
  "temperature": 0.7,
  "max_tokens": 1024,
  "tools": ["hello_world"]
}
```

Resposta:
```json
{
  "message": "Agente criado com sucesso",
  "agent_id": "uuid",
  "agent": {"...": "..."}
}
```

---

#### 📌 Listar agentes
**GET `/agent`**

Resposta (exemplo):
```json
[
  {
    "id": "uuid",
    "name": "Agente Suporte",
    "model": "gpt-4o-mini",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

---

#### ▶️ Executar agente (recomendado)
**POST `/agent/run/v2`**

Body:
```json
{
  "agent_id": "uuid",
  "user_id": "usuario-123",
  "session_id": null,
  "message": "Qual o status do meu pedido?"
}
```

Resposta:
```json
{
  "response": "Resposta do agente...",
  "session_id": "uuid-session"
}
```

---

#### ⚠️ Executar agente (legado)
**POST `/agent/run`**

> Atualmente este endpoint aceita o schema `AgentRunRequest` (`user_prompt`, `id`) mas delega internamente para o runtime v2. Recomenda-se usar `/agent/run/v2` para evitar incompatibilidades.

---

#### 🧰 Listar tools disponíveis
**GET `/list_tools`**

Resposta:
```json
{
  "tools": [
    {
      "name": "hello_world",
      "schema": {"description": "...", "parameters": {...}}
    }
  ]
}
```

---

### Endpoints de dashboard

Prefixo: `/dashboard`

#### GET `/dashboard/overview`
Retorna visão geral (totais) com filtro opcional por `agent_id`.

#### GET `/dashboard/totals-by-agent`
Retorna métricas agregadas por agente.

#### GET `/dashboard/last-runs`
Lista execuções recentes. Parâmetros:
- `limit` (1–200)
- `agent_id` (opcional)
- `status` (opcional)

---

### Endpoints de reviews de PR

Prefixo: `/api/v1/reviews`

#### ▶️ Rodar review de PR
**POST `/api/v1/reviews/pr/run`**

Headers obrigatórios:
```
Authorization: Bearer <API_KEY>
X-GitHub-Token: <TOKEN_GITHUB>
```

Body:
```json
{
  "repo_full_name": "WeslleySebastiao/chatllm-api",
  "pr_number": 12,
  "head_sha": "abc123",
  "base_sha": "def456"
}
```

Resposta:
```json
{
  "repo_full_name": "WeslleySebastiao/chatllm-api",
  "pr_number": 12,
  "head_sha": "abc123",
  "result": {
    "summary": "...",
    "findings": []
  }
}
```

---

#### 🔎 Último review de um PR
**GET `/api/v1/reviews/pr/latest`**

Query:
- `repo_full_name`
- `pr_number`

---

#### 🔎 Review por job
**GET `/api/v1/reviews/jobs/{job_id}`**

---

#### 📜 Histórico de reviews por PR
**GET `/api/v1/reviews/pr/history`**

Query:
- `repo_full_name`
- `pr_number`
- `limit` (1–100)
- `offset`

---

#### 📚 Repositórios analisados
**GET `/api/v1/reviews/repos`**

---

#### 📂 PRs analisados
**GET `/api/v1/reviews/prs`**

Query:
- `repo_full_name`
- `limit` (1–200)
- `offset`

---

## 🧩 MCP Tools

As tools locais ficam em:
```
src/mcp/tools/<nome_da_tool>/
├── function.py
└── schema.json
```

Ao iniciar o servidor, o loader registra automaticamente todas as tools encontradas nessa pasta. Para adicionar uma nova tool:

1. Crie uma pasta com o nome da tool.
2. Adicione `function.py` com a função principal.
3. Adicione `schema.json` com `description` e `parameters`.

---

## 📊 Telemetria e memória

- **Telemetria**: cada execução registra tempo, tokens e custo (via `utils/log.py`).
- **Memória conversacional**: sessões são persistidas em banco para permitir contexto entre chamadas do mesmo usuário.

---

## 🧯 Problemas comuns

- **Erro 401 no endpoint de review**: confira se o `API_KEY` no `.env` está correto.
- **Erro de conexão com banco**: valide as credenciais do Supabase.
- **Erro de execução do agente**: confirme se o `OPENAI_API_KEY` é válido e se o modelo existe.
