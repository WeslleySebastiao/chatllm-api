# **EM CONSTRUÇÃO!**

# 🚀 [Nome do Projeto]

> Esta API orquestra o ciclo de vida (registro e execução) de agentes personalizados, permitindo-lhes acessar opcionalmente tools hospedadas em um servidor MCP.

Este serviço atua como uma central de orquestração para agentes personalizados. O seu objetivo principal é simplificar e gerenciar todo o ciclo de vida desses agentes, desde o registro (criação) e gestão até a sua execução final.

Ele resolve o problema de ter que gerenciar agentes de forma manual ou descentralizada, fornecendo um ponto único e facilitado para sua criação e uso. Como parte de sua função no ecossistema, esta API gerencia o fluxo completo, permitindo que os agentes acessem e utilizem, opcionalmente, tools que estão localizadas em um servidor MCP.

---

### 🛠️ Tecnologias Utilizadas

#### Framework Web e Servidor
* **[Python 3.10+](https://www.python.org/)**: A linguagem de programação principal.
* **[FastAPI](https://fastapi.tiangolo.com/)**: O framework web de alta performance usado para construir a API.
* **[Uvicorn](https://www.uvicorn.org/)**: O servidor ASGI de alta velocidade que roda a aplicação.

#### Agentes & LLMs (LangChain)
* **[LangChain](https://www.langchain.com/)**: O framework principal para construir aplicações com LLMs.
* **[LangGraph](https://langchain-ai.github.io/langgraph/)**: Usado para criar fluxos de agentes robustos e cíclicos.
* **[OpenAI](https://openai.com/)**: A biblioteca oficial da OpenAI para interagir com os modelos de LLM.

#### Banco de Dados & Conexões
* **[HTTPX](https://www.python-httpx.org/)**: Um cliente HTTP moderno e assíncrono para fazer requisições a outras APIs (como o seu MCP).
* **[httpx-sse / sseclient-py]**: Bibliotecas usadas para gerenciar as conexões SSE (Server-Sent Events) com o servidor MCP.

#### Dados & Configuração
* **[Pydantic](https://docs.pydantic.dev/)**: Usado para validação de dados, parsing e gerenciamento de settings.
* **[python-dotenv](https://pypi.org/project/python-dotenv/)**: Para carregar variáveis de ambiente de arquivos `.env`.

---

## 💻 Começando

Siga estas instruções para obter uma cópia do projeto rodando na sua máquina local para desenvolvimento e testes.

### Pré-requisitos

Antes de começar, você vai precisar ter as seguintes ferramentas instaladas:

* **[Python 3.10+](https://www.python.org/)**: A versão do Python usada no projeto.
* **[Git](https://git-scm.com/)**: Para clonar o repositório.
* **(Opcional) Acesso ao MCP**: Confirme se o servidor MCP (`http://localhost:8000`) está acessível pela sua máquina.

### Instalação

Siga estes passos para configurar seu ambiente de desenvolvimento:

1.  **Clone o repositório:**
    ```bash
    git clone [URL_DO_SEU_REPOSITORIO]
    cd [NOME_DA_PASTA_DO_PROJETO]
    ```

2.  **Crie e ative um Ambiente Virtual (venv):**
    ```bash
    # No macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    
    # No Windows (PowerShell)
    python -m venv venv
    .\venv\Scripts\Activate
    ```

3.  **Instale todas as dependências:**
    (Este comando usa o arquivo que geramos anteriormente)
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as Variáveis de Ambiente:**
    O projeto usa um arquivo `.env` para carregar configurações (como chaves de API, URLs de banco de dados, etc.).
    
    ```bash
    DEBUG=True
    MCP_URL="MCP_ENDPOINT"
    OPENAI_API_KEY="sk..."
    MODEL_NAME="model_name"
    ```
    
    > ⚠️ **Importante**: Após copiar, abra o arquivo `.env` e preencha todas as variáveis com os valores corretos (chaves da OpenAI, URL do MCP, etc.).

---

## ▶️ Rodando a Aplicação

Com o ambiente virtual ativado e as dependências instaladas, você pode iniciar o servidor.

1.  **Inicie o Servidor (Modo de Desenvolvimento):**
    Este comando usa o Uvicorn para iniciar a aplicação. O "hot-reload" (`--reload`) faz com que o servidor reinicie automaticamente após qualquer alteração no código.

    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8080 --reload
    ```

2.  **Acesse a Aplicação:**
    Seu servidor estará rodando e acessível em: `http://localhost:8080`

### 📖 Documentação Interativa da API (Swagger)

Uma das maiores vantagens do FastAPI é a documentação gerada automaticamente. Você pode usá-la para testar todos os endpoints diretamente do seu navegador.

Acesse: **[http://localhost:8080/docs](http://localhost:8080/docs)**



### 📕 Documentação Alternativa (ReDoc)

O FastAPI também fornece um segundo estilo de documentação.

Acesse: **[http://localhost:8080/redoc](http://localhost:8080/redoc)**
