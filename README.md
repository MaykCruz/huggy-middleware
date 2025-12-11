# 🤖 Huggy Middleware (Empreste Digital)

Middleware de orquestração para atendimento automatizado via WhatsApp (Huggy), integrando simulações de crédito (Facta/FGTS) e gerenciamento de estados de conversação.

## 🚀 Tecnologias
- **Backend:** Python 3.11 + FastAPI
- **Worker:** Celery (Gevent Pool)
- **Banco/Cache:** Redis
- **Monitoramento:** Better Stack (Logtail)

---

## ⚠️ PONTOS DE ATENÇÃO (Hardcoded)
Algumas configurações de negócio estão fixas no código e exigem alteração manual + deploy caso mudem na plataforma de origem.

### 1. Huggy (Integração)
* **Company ID:** O ID da empresa (`351946`) está fixo na URL base.
    * Arquivo: `app/integrations/huggy/client.py`
    * *Ação:* Se mudar de conta na Huggy, alterar este arquivo.

### 2. Facta (Tabelas de Juros)
* **Tabela FGTS:** O código da tabela (`62170` - Gold Preference) e a taxa (`1.80`) estão fixos.
    * Arquivo: `app/integrations/facta/fgts/client.py`
    * Método: `_selecionar_melhor_tabela`
    * *Ação:* Se a Facta mudar a tabela comercial, atualizar este dicionário.

### 3. Regras de Timeout
* **Tempos de Espera:** As regras de quanto tempo esperar em cada menu (ex: 10min, 5h) estão em um dicionário Python.
    * Arquivo: `app/core/timeouts.py`

---

## 📝 Gerenciamento de Conteúdo (Mensagens)
O bot utiliza um sistema híbrido de mensagens (Gist + Redis + Arquivo Local).

### Fluxo de Atualização (Sem Deploy)
1.  Edite o arquivo `messages.json` no **GitHub Gist**.
2.  Chame o endpoint administrativo para limpar o cache:
    `POST /admin/refresh-messages`
3.  O bot baixará a nova versão na próxima interação.

### Sincronizando o Ambiente Local
Para garantir que o repositório tenha a versão mais recente das mensagens (backup), execute o script de sincronização antes de commitar:

```bash
# Na raiz do projeto
python app/sync_messages.py

# Depois commite a atualização
git add app/services/bot/content/messages.json
git commit -m "chore: sync messages from gist"
```
## 🛠️ Comandos Úteis
### Rodar Localmente (Docker)
```bash
docker-compose up --build
```
### Limpar Redis (Hard Reset)
Se precisar limpar todas as sessões e caches:
```bash
redis-cli -u "SUA_REDIS_KEY" FLUSHALL
```
### Variáveis de Ambiente Obrigatórias
* `HUGGY_API_TOKEN`: Token da API V3.
* `FACTA_USER`/`FACTA_PASSWORD`: Credenciais da Facta.
* `MESSAGES_URL`: Link RAW do Gist (ex: `gist.githubusercontent.com/.../raw/messages.json`).
* `CELERY_RESULT_BACKEND`: URL do Redis.

