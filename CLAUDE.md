# Planejamento Agent - PMAX

## Sobre
App web para geração semi-autônoma de planejamentos mensais de marketing de conteúdo.
Pipeline de 4 agents IA (Pesquisador → Estrategista → Planejador → Revisor) gera roteiros de vídeo, copies de artes e carrosséis personalizados por cliente.

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
- **PDF**: Gotenberg 8 (HTML → PDF)
- **Deploy**: Docker Swarm via Portainer + Traefik + Cloudflare

## Estrutura
```
backend/app/
├── main.py                    # FastAPI app + middlewares
├── database.py                # AsyncSession + engine
├── config/                    # Settings (pydantic-settings)
├── models/                    # SQLAlchemy ORM (clientes, planejamentos, conteudos, historico, pipeline_logs)
├── schemas/                   # Pydantic I/O
├── routers/
│   ├── clientes.py            # CRUD + kick-off/preview (IA extrai perfil)
│   ├── planejamentos.py       # Gerar/listar/aprovar/ajustar/download PDF
│   ├── config.py              # Tipos conteúdo, frameworks, focos, destinos, plataformas
│   └── websocket.py           # Pipeline real-time (10min timeout)
├── agents/
│   ├── base_agent.py          # Classe base + parse_json_safe (3 fallbacks)
│   ├── orchestrator.py        # Pipeline controller (usa session_factory do caller)
│   ├── pesquisador.py         # Perplexity Sonar (web search real) | temp 0.8
│   ├── estrategista.py        # Claude Sonnet | temp 0.6 | usa foco/destino/plataformas
│   ├── planejador.py          # Claude Sonnet | temp 0.7 | 12288 tokens | 3 few-shot
│   └── revisor.py             # Claude Sonnet | temp 0.1 | score 0-100 | verifica A/B
├── services/
│   ├── pdf_service.py         # Gotenberg (HTML→PDF) + Jinja2 template
│   ├── cliente_service.py     # CRUD helpers
│   └── storage_service.py     # Path validation
├── providers/
│   └── openrouter_client.py   # HTTP/2 client, 120s timeout
├── prompts/                   # System prompts detalhados (PT-BR)
├── templates/                 # HTML/CSS profissional para PDF
├── tasks/
│   ├── celery_app.py          # Config (10min timeout, Redis db 1)
│   └── generation_tasks.py    # Pipeline async + PDF generation + delete old conteudos
└── frameworks/                # Storytelling (AIDA/PAS/HSO) + pilares
```

## Pipeline de Agents
1. **Pesquisador** (Perplexity Sonar) — web search real: tendências, concorrentes, viral, sazonalidade
2. **Estrategista** (Sonnet, temp 0.6) — temas por pilar, calendário, anti-repetição, usa foco/destino
3. **Planejador** (Sonnet, temp 0.7, 12288 tokens) — roteiros, copies, CTAs, frameworks variados, A/B
4. **Revisor** (Sonnet, temp 0.1) — score 0-100, valida tom/CTAs/pilares, loop se < 70

## Configuração do Planejamento
Ao criar um planejamento, o operador define:
- **Foco**: Geração de Leads | Vendas E-commerce | Crescimento Orgânico | Branding | Lançamento | Retenção
- **Destino**: WhatsApp | Site | DM Instagram | Loja Online | Agendamento | Telefone
- **Tipo**: Orgânico | Pago (Ads) | Ambos
- **Plataformas**: Instagram, TikTok, YouTube, LinkedIn, Facebook

## Kick Off Inteligente
- Operador cola respostas do Google Forms ou anotações da reunião
- IA extrai automaticamente: nome, nicho, público, tom, pilares, concorrentes, tipos conteúdo
- Preview editável antes de salvar
- 31 perguntas mapeadas do formulário Kick Off da agência

## Deploy
```bash
# Portainer Stack 33 — restart via API
API_KEY="ptr_2bJkq4BVfY+LuE5WWbUryyK11OQQmsDIiAeVn6aLN/k="
curl -X POST "https://porto.dynamicagents.tech/api/stacks/33/stop?endpointId=1" -H "X-API-Key: $API_KEY"
curl -X POST "https://porto.dynamicagents.tech/api/stacks/33/start?endpointId=1" -H "X-API-Key: $API_KEY"
```

## Convenções
- **Idioma**: Todo código e prompts em Português (PT-BR)
- **Backend**: async/await, type hints, Pydantic v2, parse_json_safe para LLM responses
- **Frontend**: TypeScript strict, Tailwind utility-first
- **Commits**: Português, imperativo ("Adiciona endpoint X", "Corrige bug Y")
- **Agents**: Cada agent usa temperature otimizada para seu papel
- **API Keys**: Apenas no Portainer (NUNCA no código ou .env.example)

## Gotchas
- Containers fazem `git clone` no startup (~3min para npm install)
- Redis db 1 (db 0 é do Designer Agent)
- Se stack reinicia durante geração, task Celery se perde — status fica "em_geracao" para sempre
- Perplexity Sonar não suporta response_format — usar parse_json_safe
- Vite precisa de allowedHosts para domínio de produção
