# Planejamento Agent - PMAX

## Sobre
App web para geração de planejamentos mensais de marketing de conteúdo.
Pipeline de 2 agents IA (Pesquisador → Gerador) cria roteiros, copies e carrosséis em ~40s.

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
- **IA**: OpenRouter (Sonnet para geração, Perplexity Sonar para pesquisa web)
- **PDF**: Gotenberg 8 (Jinja2 + autoescape)
- **DOCX**: python-docx
- **Deploy**: Docker Swarm via Portainer + Traefik + Cloudflare

## Pipeline (2 agents)
1. **Pesquisador** (Perplexity Sonar, temp 0.6) — web search real: tendências, concorrentes, viral
2. **Gerador** (Claude Sonnet, temp 0.7, 12288 tokens) — gera TUDO em 1 chamada: estratégia + conteúdos + calendário
- **Ajustador** (Sonnet, temp 0.3) — para feedback, revisa sem refazer do zero

## Kick Off (3 modos)
- **Colar Respostas** — cola texto do Google Forms
- **Pesquisa Automática** — Instagram + Site → Perplexity pesquisa na web
- **Manual** — formulário 5 steps

## Novo Planejamento (4 steps)
1. Cliente + Mês
2. Direcionamento (produtos a promover, referências, feedback reunião)
3. Configuração (foco/destino/tipo/plataformas — pré-preenchido do perfil)
4. Tipos de conteúdo (quantidades)

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
- LLM inventa tipos (`foto_produtos`) → prompt enforça "SOMENTE video_roteiro, arte_estatica, carrossel"
- Componentes React dentro de funções = remount → usar render helpers
- Deploy durante geração = task perdida, status "em_geracao" para sempre
- Perplexity Sonar: não suporta response_format, timeout na 1ª chamada
- `VITE_API_URL` é build-time → path relativo via nginx em produção
- Vite: allowedHosts necessário para domínio de produção
- Redis db 1 (db 0 é Designer Agent)
- `/storage/` protegido por API key
- Sem menção a IA nos documentos — footer: "PMAX Marketing de Performance"

## Convenções
- Idioma: PT-BR em código e prompts
- `parse_json_safe()` em `app/utils/json_parser.py` para TODA resposta LLM
- Erros genéricos no response (não vazar detalhes internos)
- Novas colunas: ALTER TABLE via Portainer exec
