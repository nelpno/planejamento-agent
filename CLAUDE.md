# Planejamento Agent - PMAX

## Sobre
App web para geração de planejamentos mensais de marketing de conteúdo.
Gerador com auto-research via tool use (pesquisa web sob demanda) cria roteiros, copies e carrosséis.

## URLs
- **Produção**: https://planejamento.dynamicagents.tech
- **API Docs**: https://planejamento.dynamicagents.tech/docs (DEBUG=true)
- **GitHub**: https://github.com/nelpno/planejamento-agent
- **Portainer**: Stack ID 33

## Stack
- **Backend**: FastAPI 0.115 + Python 3.12 + SQLAlchemy 2.0 + asyncpg
- **Frontend**: React 19 + Vite 6 + Tailwind CSS 3.4 + TypeScript
- **Banco**: PostgreSQL 16 (nelsonNet, user: planner, db: planejamento_agent)
- **Fila**: Redis 7 (db 1) + Celery 5.4
- **IA**: OpenRouter (Sonnet 4.6 para geração, Haiku 4.5 para ajustes, Perplexity Sonar para pesquisa web)
- **PDF**: Gotenberg 8 (Jinja2 + autoescape)
- **DOCX**: python-docx
- **Deploy**: Docker Swarm via Portainer + Traefik + Cloudflare

## Modelos LLM
- **Gerador**: `anthropic/claude-sonnet-4-6` (temp 0.7, 12288 tokens, reasoning 8K) — tool use + extended thinking
- **Pesquisa Web**: `perplexity/sonar-pro` (temp 0.6) — chamado como tool pelo Gerador sob demanda
- **Ajustador**: `anthropic/claude-haiku-4-5` (temp 0.3) — econômico para ajustes
- **Kick Off**: `anthropic/claude-sonnet-4-6` (temp 0.3) — extrai perfil do texto

## Pipeline (1 agent com tool use)
1. **Gerador** (Sonnet 4.6) — recebe tool `pesquisar_web`, decide o que pesquisar, gera estratégia + conteúdos + calendário
   - Tool `pesquisar_web` → chama Perplexity Sonar internamente
   - Pesquisa é direcionada ao contexto do mês (não dump genérico)
   - Extended thinking (reasoning: 8K tokens) — pensa na estratégia antes de gerar
   - Tools definidas em `app/agents/tools.py`, tool use loop em `OpenRouterClient.chat_with_tools()`
- **Ajustador** (Haiku 4.5) — para feedback, revisa sem refazer do zero

## Kick Off (3 modos)
- **Colar Respostas** — cola texto do Google Forms
- **Pesquisa Automática** — Instagram + Site → Perplexity pesquisa na web
- **Manual** — formulário 5 steps

## Novo Planejamento (4 steps)
1. Cliente + Mês
2. Direcionamento (produtos a promover, referências, feedback reunião)
3. Configuração (foco/destino/tipo/plataformas — pré-preenchido do perfil)
4. Tipos de conteúdo (quantidades)

## Features Operacionais
- **Dashboard**: clientes pendentes este mês + stats + planejamentos recentes
- **Deletar** planejamento (com confirmação)
- **Duplicar** planejamento para próximo mês
- **Marcar como Enviado** (timestamp + badge no histórico)
- **Editar** cliente (tela dedicada)
- **Collapse** por tipo de conteúdo na preview
- **Download**: PDF + DOCX editável
- **Refazer** (pipeline completo) / **Ajustar** (só modifica o que pediu)

## Separação Importante
- **Kick Off** = perfil do cliente (CONTEXTO — quem é)
- **Planejamento** = direcionamento do mês (O QUE fazer)
- Defaults salvos no perfil: foco_padrao, destino_padrao, tipo_uso_padrao, plataformas_padrao

## Deploy
```bash
# NUNCA deploy sem confirmação do operador
API_KEY="ptr_2bJkq4BVfY+LuE5WWbUryyK11OQQmsDIiAeVn6aLN/k="
curl -X POST "https://porto.dynamicagents.tech/api/stacks/33/stop?endpointId=1" -H "X-API-Key: $API_KEY"
curl -X POST "https://porto.dynamicagents.tech/api/stacks/33/start?endpointId=1" -H "X-API-Key: $API_KEY"
```

## DB Migrations
```bash
# Via Portainer exec no container postgres (ID: 7649e5f02ad3)
psql -U planner -d planejamento_agent -c "ALTER TABLE x ADD COLUMN IF NOT EXISTS y TYPE;"
```

## Gotchas Críticos
- `item.conteudo.copy` no Jinja2 → chama `dict.copy()`. Usar `.get("copy")`
- `selectattr` incompatível com autoescape → usar loop com `if "tipo" in item.tipo`
- Celery + engine global = "Future attached to different loop" → criar engine dentro da task
- `variacoes_ab` é `list | None` no schema (não `dict`)
- LLM inventa tipos → prompt enforça "SOMENTE video_roteiro, arte_estatica, carrossel"
- Frontend normaliza tipos com `includes()` (aceita variantes do LLM)
- Componentes React dentro de funções = remount → usar render helpers
- Deploy durante geração = task perdida
- Perplexity Sonar: não suporta response_format
- `VITE_API_URL` é build-time → path relativo via nginx
- Vite: allowedHosts para domínio de produção
- Redis db 1 (db 0 é Designer Agent)
- `/storage/` protegido por API key
- Footer documentos: "PMAX Marketing de Performance" (sem menção a IA)
- Logo clara no header PDF (fundo escuro), logo escura no DOCX (fundo branco)
- OpenRouter: usar `reasoning: {max_tokens: N}` (NÃO `thinking`). Variante `:thinking` deprecated para Anthropic
- Extended thinking + `response_format: json_object` são incompatíveis → confiar no prompt + `parse_json_safe()`
- Tool use: Gerador não usa `response_format: json_object` (incompatível com tool use/thinking)
- Pesquisa Sonar pode falhar → tool_executor tem fallback gracioso
- httpx timeout: read=300s para suportar tool use com múltiplas pesquisas

## Convenções
- Idioma: PT-BR em código e prompts
- `parse_json_safe()` em `app/utils/json_parser.py` para TODA resposta LLM
- Erros genéricos no response (não vazar detalhes internos)
- Novas colunas: ALTER TABLE via Portainer exec
- handleDelete/handleX sempre com `finally { setActionLoading(false) }`
- Spec de design em `docs/superpowers/specs/` — consultar antes de mudanças arquiteturais
