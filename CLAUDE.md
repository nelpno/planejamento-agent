# Planejamento Agent - PMAX

## Sobre
App web para geração semi-autônoma de planejamentos mensais de marketing de conteúdo.
Pipeline de 4 agents IA (Pesquisador → Estrategista → Planejador → Revisor) gera roteiros de vídeo, copies de artes e carrosséis personalizados por cliente.

## URLs
- **Produção**: https://planejamento.dynamicagents.tech
- **API Local**: http://localhost:8000
- **Frontend Local**: http://localhost:5173
- **Docs API**: http://localhost:8000/docs (apenas com DEBUG=true)

## Stack
- **Backend**: FastAPI 0.115 + Python 3.12 + SQLAlchemy 2.0 + asyncpg
- **Frontend**: React 19 + Vite 6 + Tailwind CSS 3.4 + TypeScript
- **Banco**: PostgreSQL 16 (rede nelsonNet)
- **Fila**: Redis 7 + Celery 5.4
- **IA**: OpenRouter API (Claude Sonnet/Haiku)
- **PDF**: Gotenberg 8 (HTML → PDF)
- **Deploy**: Docker Swarm via Portainer + Traefik + Cloudflare

## Estrutura
```
backend/app/
├── main.py                    # FastAPI app + middlewares
├── database.py                # AsyncSession + engine
├── config/                    # Settings (pydantic-settings)
├── models/                    # SQLAlchemy ORM
├── schemas/                   # Pydantic I/O
├── routers/                   # API endpoints
│   ├── clientes.py            # CRUD clientes
│   ├── planejamentos.py       # Gerar/listar/aprovar
│   ├── config.py              # Tipos conteúdo, frameworks
│   └── websocket.py           # Pipeline real-time
├── agents/                    # Pipeline de IA
│   ├── orchestrator.py        # Controller
│   ├── pesquisador.py         # Tendências, concorrência
│   ├── estrategista.py        # Temas, pilares, calendário
│   ├── planejador.py          # Roteiros, copies, CTAs
│   └── revisor.py             # Validação + score
├── services/                  # Business logic
│   ├── pdf_service.py         # Gotenberg integration
│   └── cliente_service.py     # CRUD helpers
├── providers/                 # External APIs
│   └── openrouter_client.py   # LLM calls
├── prompts/                   # System prompts (PT-BR)
├── templates/                 # HTML/CSS para PDF
├── tasks/                     # Celery tasks
└── frameworks/                # Storytelling + pilares
```

## Pipeline de Agents
1. **Pesquisador** (Haiku) — tendências, datas comemorativas, concorrência, viral
2. **Estrategista** (Sonnet) — define temas, pilares, calendário de publicação
3. **Planejador** (Sonnet) — gera roteiros, copies, CTAs com frameworks (AIDA/PAS/HSO)
4. **Revisor** (Sonnet) — valida tom, CTAs, pilares, score 0-100 (loop se < 70)

## Deploy
```bash
# Portainer Stack — restart via API
curl -X POST "http://PORTAINER_IP:9000/api/stacks/STACK_ID/stop?endpointId=1" -H "X-API-Key: KEY"
curl -X POST "http://PORTAINER_IP:9000/api/stacks/STACK_ID/start?endpointId=1" -H "X-API-Key: KEY"
```

## Convenções
- **Idioma**: Todo código e prompts em Português (PT-BR)
- **Backend**: async/await everywhere, type hints, Pydantic v2
- **Frontend**: TypeScript strict, Tailwind utility-first, sem CSS modules
- **Commits**: Português, imperativo ("Adiciona endpoint X", "Corrige bug Y")
- **Testes**: pytest + httpx para backend, vitest para frontend
