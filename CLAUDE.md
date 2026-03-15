# Planejamento Agent - PMAX

## Sobre
App web para geração semi-autônoma de planejamentos mensais de marketing de conteúdo.
Pipeline de 5 agents IA gera roteiros de vídeo, copies de artes e carrosséis personalizados por cliente.

## URLs
- **Produção**: https://planejamento.dynamicagents.tech
- **API Docs**: https://planejamento.dynamicagents.tech/docs (DEBUG=true)
- **GitHub**: https://github.com/nelpno/planejamento-agent
- **Portainer**: Stack ID 33

## Stack
- **Backend**: FastAPI 0.115 + Python 3.12 + SQLAlchemy 2.0 + asyncpg
- **Frontend**: React 19 + Vite 6 + Tailwind CSS 3.4 + TypeScript
- **Banco**: PostgreSQL 16 (rede nelsonNet, user: planner, db: planejamento_agent)
- **Fila**: Redis 7 (db 1) + Celery 5.4
- **IA**: OpenRouter API (Sonnet para criação, Haiku para fast, Perplexity Sonar para pesquisa web)
- **PDF**: Gotenberg 8 (HTML → PDF via Jinja2 template com autoescape)
- **DOCX**: python-docx (Word editável)
- **Deploy**: Docker Swarm via Portainer + Traefik + Cloudflare

## Estrutura
```
backend/app/
├── main.py                    # FastAPI app + middlewares + auth
├── database.py                # AsyncSession + engine (NÃO usar no Celery — ver Gotchas)
├── config/                    # Settings (pydantic-settings, sem defaults para DB/Redis)
├── models/                    # SQLAlchemy ORM (clientes, planejamentos, conteudos, historico, pipeline_logs)
├── schemas/                   # Pydantic I/O (variacoes_ab é LIST, não dict)
├── routers/
│   ├── clientes.py            # CRUD + kick-off/preview + discover (web search)
│   ├── planejamentos.py       # Gerar/listar/aprovar/ajustar/regerar/download PDF+DOCX
│   ├── config.py              # Tipos conteúdo, frameworks, focos, destinos, plataformas
│   └── websocket.py           # Pipeline real-time (10min timeout, reconexão)
├── agents/
│   ├── base_agent.py          # Classe base + parse_json_safe (3 fallbacks)
│   ├── orchestrator.py        # Pipeline controller (recebe session_factory do caller)
│   ├── pesquisador.py         # Perplexity Sonar (web search real) | temp 0.8
│   ├── estrategista.py        # Claude Sonnet | temp 0.6 | usa foco/destino/plataformas
│   ├── planejador.py          # Claude Sonnet | temp 0.7 | 12288 tokens | 3 few-shot
│   ├── revisor.py             # Claude Sonnet | temp 0.1 | score 0-100 | verifica A/B
│   └── ajustador.py           # Claude Sonnet | temp 0.3 | revisa sem refazer do zero
├── services/
│   ├── pdf_service.py         # Gotenberg + Jinja2 (autoescape ativado)
│   ├── docx_service.py        # python-docx (Word editável com logo)
│   ├── cliente_service.py     # CRUD helpers
│   └── storage_service.py     # Path validation (realpath guard)
├── providers/
│   └── openrouter_client.py   # HTTP/2, 120s timeout, retry 3x com backoff
├── utils/
│   └── json_parser.py         # parse_json_safe compartilhado (agents + routers)
├── prompts/                   # System prompts detalhados (PT-BR)
├── templates/                 # HTML/CSS para PDF + logos (claro/escuro)
├── tasks/
│   ├── celery_app.py          # Config (10min timeout, Redis db 1)
│   └── generation_tasks.py    # Pipeline async + ajuste + PDF + engine próprio
└── frameworks/                # Storytelling (AIDA/PAS/HSO) + pilares
```

## Pipeline de Agents
1. **Pesquisador** (Perplexity Sonar) — web search real: tendências, concorrentes, viral, sazonalidade
2. **Estrategista** (Sonnet, temp 0.6) — temas por pilar, calendário, anti-repetição, usa foco/destino
3. **Planejador** (Sonnet, temp 0.7, 12288 tokens) — roteiros, copies, CTAs, frameworks variados, A/B
4. **Revisor** (Sonnet, temp 0.1) — score 0-100, valida tom/CTAs/pilares, loop se < 70
5. **Ajustador** (Sonnet, temp 0.3) — revisa conteúdo existente com feedback, sem refazer do zero

## Kick Off Inteligente (3 modos)
- **Colar Respostas** — cola texto do Google Forms, IA extrai perfil
- **Pesquisa Automática** — só Instagram + Site, Perplexity pesquisa na web
- **Preencher Manualmente** — formulário 5 steps (31 perguntas do Kick Off)

## Direcionamento do Planejamento
- Perfil do cliente (Kick Off) = **CONTEXTO** — quem é o cliente (tom, público, pilares)
- Inputs do planejamento = **DIRECIONAMENTO** — o que fazer no mês
- Campos: produtos a promover, referências mês anterior, feedback reunião
- Foco: Leads | E-commerce | Orgânico | Branding | Lançamento | Retenção
- Destino: WhatsApp | Site | DM | Loja | Agendamento | Telefone
- Tipo: Orgânico | Pago | Ambos
- Plataformas: Instagram, TikTok, YouTube, LinkedIn, Facebook

## Fluxos
- **Novo planejamento**: Pesquisador → Estrategista → Planejador → Revisor (~2.5min)
- **Ajuste (feedback)**: Ajustador → Revisor (~30s, não refaz do zero)
- **Refazer (failed/travado)**: Pipeline completo via POST /regerar
- **Outputs**: PDF (logo clara no header escuro) + DOCX editável (logo escura)
- **Footer**: "PMAX Marketing de Performance" (sem menção a IA)

## Deploy
```bash
# NUNCA fazer deploy sem confirmação do operador
API_KEY="ptr_2bJkq4BVfY+LuE5WWbUryyK11OQQmsDIiAeVn6aLN/k="
curl -X POST "https://porto.dynamicagents.tech/api/stacks/33/stop?endpointId=1" -H "X-API-Key: $API_KEY"
curl -X POST "https://porto.dynamicagents.tech/api/stacks/33/start?endpointId=1" -H "X-API-Key: $API_KEY"
```

## DB Migrations Manuais
```bash
# Via Portainer exec no container postgres (ID: 7649e5f02ad3)
psql -U planner -d planejamento_agent -c "ALTER TABLE planejamentos ADD COLUMN IF NOT EXISTS coluna TYPE;"
```

## Convenções
- **Idioma**: Todo código e prompts em Português (PT-BR)
- **Backend**: async/await, type hints, Pydantic v2, parse_json_safe para TODA resposta LLM
- **Frontend**: TypeScript strict, Tailwind utility-first, render helpers (não componentes aninhados)
- **Commits**: Português, imperativo ("Adiciona endpoint X", "Corrige bug Y")
- **Agents**: Temperature otimizada por papel (criativo 0.7-0.8, analítico 0.1-0.3)
- **API Keys**: Apenas no Portainer (NUNCA no código ou .env.example)
- **Erros**: Mensagens genéricas no response (não vazar detalhes internos)
- **Segurança**: API_SECRET_KEY obrigatória em produção, /storage/ protegido

## Gotchas Críticos
- `item.conteudo.copy` no Jinja2 chama `dict.copy()` — usar `.get("copy")` para chave "copy"
- `selectattr` do Jinja2 incompatível com autoescape — usar loop com `if item.tipo == "x"` direto
- Celery + `AsyncSessionLocal` global = "Future attached to different loop" — criar engine dentro da task com `_create_session_factory()`
- Revisor `conteudos_revisados` parcial descarta originais — só substituir se `len(revisados) >= len(originais)`
- `variacoes_ab` é `list | None` no schema (não `dict`) — erro causa 500 silencioso no /conteudos
- Componentes React dentro de funções = remount a cada keystroke — usar funções renderizadoras puras
- Deploy durante geração = task Celery perdida, status "em_geracao" para sempre
- Perplexity Sonar: não suporta `response_format`, timeout na primeira chamada (retry 3x resolve)
- `VITE_API_URL` é build-time no Vite — em produção usar path relativo via nginx
- Vite precisa de `allowedHosts` no `vite.config.ts` para domínio de produção
- Redis db 1 (db 0 é do Designer Agent) — nunca mudar
- DATABASE_URL e REDIS_URL sem default no config — falha na inicialização se não configurado
