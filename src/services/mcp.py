from sseclient import SSEClient
import requests, threading, json, time

class MCPClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.messages_url = None          # /messages/?session_id=...
        self.req_id = 1                   # contador de ids JSON-RPC
        self.initialize_sent = False      # já mandei "initialize"?
        self.initialized_ok = False       # já recebi resposta OK do initialize?
        self.session_ready = False        # handshake COMPLETO (já posso usar tools)
        self.last_results = {}            # respostas recebidas via SSE por id

        # thread que fica ouvindo SSE
        self.events_thread = threading.Thread(target=self._listen, daemon=True)
        self.events_thread.start()

    def _listen(self):
        """Fica escutando eventos SSE enviados pelo MCP."""
        sse_url = f"{self.base_url}/sse"

        with requests.get(
            sse_url,
            headers={"Accept": "text/event-stream"},
            stream=True,
        ) as resp:
            if resp.status_code != 200:
                print(f"⚠️ Falha ao conectar no SSE ({resp.status_code})")
                return

            print(f"✅ Conectado ao SSE: {sse_url}")
            client = SSEClient(resp)

            for event in client.events():
                data_raw = event.data.strip()
                if not data_raw:
                    continue

                # 1) Primeiro evento costuma ser tipo:
                #    /messages/?session_id=abcdef...
                if data_raw.startswith("/messages"):
                    self.messages_url = f"{self.base_url}{data_raw}"
                    continue

                # 2) Outros eventos são JSON (respostas do MCP)
                if data_raw.startswith("{"):
                    try:
                        payload = json.loads(data_raw)
                    except Exception:
                        continue

                    # Se é resposta de uma requisição com "id"
                    if "id" in payload:
                        self.last_results[payload["id"]] = payload

                        # Chegou resposta do initialize?
                        # Exemplo esperado:
                        # {
                        #   "jsonrpc": "2.0",
                        #   "id": 0,
                        #   "result": {
                        #       "protocolVersion": "...",
                        #       "serverInfo": {...},
                        #       "capabilities": {...}
                        #   }
                        # }
                        if payload.get("id") == 0 and "result" in payload and not self.initialized_ok:
                            self.initialized_ok = True
                            print("MCP aceitou initialize")

                            # Envia notificação de inicialização concluída
                            self._send_notification_initialized()

                            # Marca sessão como pronta
                            self.session_ready = True
                            print("Sessão MCP pronta para uso (tools/list, tools/call, etc.)")


    def _send_jsonrpc(self, body, expect_response=True):
        """POST cru pro MCP. Retorna (status_code, text)."""
        if not self.messages_url:
            print("⚠️ Tentou enviar antes de ter messages_url")
            return None, None

        # headers MCP exigem aceitar json e event-stream
        headers = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        }

        print(f"📤 Enviando para {self.messages_url}: {body}")
        res = requests.post(self.messages_url, headers=headers, json=body)

        # 202 = aceito, resposta vai chegar pelo SSE
        # 200 = resposta direta síncrona (raro aqui)
        if res.status_code not in (200, 202):
            print(f"⚠️ Erro HTTP {res.status_code} -> {res.text}")
        else:
            if res.status_code == 200 and expect_response:
                # alguns servidores podem devolver sync
                try:
                    self.last_results[body.get("id")] = res.json()
                except Exception:
                    pass

        return res.status_code, res.text

    def _do_handshake_if_needed(self):
        """
        Executa o handshake MCP completo SE ainda não foi feito:
        1. initialize
        2. aguarda resposta do initialize
        3. notifications/initialized
        """

        # já pronto? então não faz nada
        if self.session_ready:
            return True

        # precisamos ter o canal /messages primeiro
        if not self.messages_url:
            return False

        # passo 1: enviar "initialize" só uma vez
        if not self.initialize_sent:
            init_body = {
                "jsonrpc": "2.0",
                "id": 0,  # initialize quase sempre usa id 0
                "method": "initialize",
                "params": {
                    # versão do protocolo MCP. Datas tipo "2025-03-26" são aceitas
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},  # podemos mandar vazio
                    "clientInfo": {
                        "name": "ChatLLM API",
                        "version": "0.1.0",
                    },
                },
            }
            self._send_jsonrpc(init_body, expect_response=True)
            self.initialize_sent = True

        # passo 2: esperar resposta do initialize (self.initialized_ok)
        # damos algumas voltas pequenas
        for _ in range(50):  # ~5s (50 * 0.1)
            if self.initialized_ok:
                break
            time.sleep(0.1)

        if not self.initialized_ok:
            print("⛔ initialize não confirmou ainda")
            return False

        # se já marcamos initialized_ok, o listener vai mandar notifications/initialized
        # e setar session_ready = True
        for _ in range(50):  # mais ~5s pra finalizar handshake
            if self.session_ready:
                return True
            time.sleep(0.1)

        print("⛔ handshake não completou (faltou notifications/initialized?)")
        return False

    def _send_notification_initialized(self):
        """
        Envia o segundo passo do handshake:
        { "jsonrpc": "2.0", "method": "notifications/initialized" }
        Isso é uma notificação: sem 'id'.
        """
        body = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }
        # notificação -> não esperamos response
        self._send_jsonrpc(body, expect_response=False)


    def call(self, method, **params):
        """
        Envia comandos JSON-RPC depois que o handshake MCP estiver ok.
        Ex: tools/list, tools/call, resources/list...
        """
        # garante handshake primeiro
        ok = self._do_handshake_if_needed()
        if not ok:
            print("❌ MCP não está pronto, abortando chamada", method)
            return None

        # monta requisição normal
        req_id = self.req_id
        self.req_id += 1

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "id": req_id,
        }

        # params obrigatórios ou objeto vazio
        payload["params"] = params or {}

        self._send_jsonrpc(payload, expect_response=True)

        # agora esperamos a resposta desse id chegar via SSE
        for _ in range(100):  # ~10s (100 * 0.1)
            if req_id in self.last_results:
                resp = self.last_results.pop(req_id)
                if "result" in resp:
                    return resp["result"]
                else:
                    print("⚠️ Erro JSON-RPC:", resp.get("error"))
                    return None
            time.sleep(0.1)

        print("⏰ Timeout esperando resposta do método", method)
        return None

    def listar_tools(self):
        """Lista as tools disponíveis no MCP."""
        result = self.call("tools/list")
        tools = (result or {}).get("tools", [])
        print(f"🔧 {len(tools)} tool(s) disponíveis:")
        for t in tools:
            print(f"   → {t.get('name')}: {t.get('description', '')}")
        return tools
