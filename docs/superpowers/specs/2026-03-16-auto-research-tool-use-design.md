# Auto-Research via Tool Use + Extended Thinking

**Data:** 2026-03-16
**Status:** Draft
**Escopo:** Otimizar pipeline de geração do Planejamento Agent

---

## Resumo

Substituir o pipeline de 2 agents sequenciais (Pesquisador → Gerador) por um único agent (Gerador) com extended thinking e tool use. O Gerador decide autonomamente o que pesquisar via tool `pesquisar_web`, que chama Perplexity Sonar internamente.

O Ajustador (Haiku) não muda.

## Motivação

1. **Pesquisa genérica** — O Pesquisador atual sempre pede as mesmas 5 categorias (tendências, datas, insights, viral, resumo), independente do direcionamento do mês. Se o operador diz "foco em lançamento do produto X", a pesquisa deveria buscar sobre o produto X.

2. **Gerador não raciocina** — Vai direto do input pro output JSON. Extended thinking permite que ele pense na estratégia antes de gerar, resultando em conteúdo mais coerente.

3. **Pipeline desnecessariamente complexo** — 2 agents com orquestrador para um fluxo linear simples. Um agent com tools é mais direto.

## Arquitetura

### Antes

```
PipelineOrchestrator
  ├── PesquisadorAgent (Perplexity Sonar) → PesquisaResult
  │     dump genérico: tendências, datas, insights, viral, resumo
  │
  └── GeradorAgent (Sonnet 4.6) → EstrategiaResult + ConteudoGerado[]
        recebe PesquisaResult no prompt, gera tudo em 1 chamada
```

### Depois

```
PipelineOrchestrator (simplificado)
  └── GeradorAgent (Sonnet 4.6 + Extended Thinking)
        tools: [pesquisar_web]
        1. Pensa na estratégia (extended thinking)
        2. Chama pesquisar_web(query) ×N sob demanda
        3. Integra pesquisa no raciocínio
        4. Gera estratégia + conteúdos
```

## Componentes

### 1. OpenRouterClient — chat_with_tools()

Novo método no client HTTP existente.

**Assinatura:**
```python
async def chat_with_tools(
    self,
    model: str,
    messages: list[dict],
    tools: list[dict],
    tool_executor: Callable[[str, dict], Awaitable[str]],
    temperature: float = 0.7,
    max_tokens: int = 16384,
    thinking: dict | None = None,
    max_tool_rounds: int = 5,
) -> tuple[str, list[dict]]:
    """
    Chat com suporte a tool use loop.

    Args:
        tools: definições de tools no formato OpenAI
        tool_executor: async callback (tool_name, arguments) -> result_string
        thinking: config de extended thinking, ex: {"type": "enabled", "budget_tokens": 10000}
        max_tool_rounds: máximo de rounds de tool use antes de abortar

    Returns:
        (content_final, tool_calls_history)
    """
```

**Fluxo interno:**
```
1. Monta payload com tools + thinking
2. POST /chat/completions
3. Se response.message.tool_calls:
   a. Executa cada tool via tool_executor callback
   b. Adiciona tool results às messages
   c. Volta pro step 2
4. Se response.message.content (sem tool_calls):
   → Retorna (content, historico)
5. Se excedeu max_tool_rounds:
   → Raise RuntimeError
```

**Retry:** Mantém a mesma lógica de retry (429, timeout) do método `chat()` existente.

**Não altera** o método `chat()` existente — o Ajustador e outros usos continuam funcionando.

### 2. Tool: pesquisar_web

**Definição (OpenAI format):**
```json
{
    "type": "function",
    "function": {
        "name": "pesquisar_web",
        "description": "Pesquisa informações atualizadas na web sobre um tópico específico. Use para buscar tendências de mercado, datas comemorativas, conteúdo viral, dados de concorrentes, ou qualquer informação atual relevante para criar o planejamento de conteúdo.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Consulta de pesquisa específica. Inclua o nicho/segmento, período temporal, e contexto relevante. Ex: 'tendências marketing digital restaurantes março 2026 Brasil'"
                }
            },
            "required": ["query"]
        }
    }
}
```

**Implementação:**
```python
async def pesquisar_web(query: str, client: OpenRouterClient) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "Pesquisador web especializado em marketing digital. "
                "Retorne informações atuais, específicas e factuais. "
                "Formato: texto corrido com dados relevantes. "
                "Tudo em português brasileiro."
            ),
        },
        {"role": "user", "content": query},
    ]
    return await client.chat(
        model=settings.LLM_MODEL_SEARCH,  # perplexity/sonar-pro
        messages=messages,
        temperature=0.6,
        max_tokens=2048,
    )
```

**Localização:** `backend/app/agents/tools.py` (novo arquivo).

### 3. GeradorAgent refatorado

**Mudanças principais:**
- Usa `chat_with_tools()` em vez de `chat()`
- Extended thinking habilitado
- Sem `response_format: json_object` (incompatível com thinking)
- Tool executor que mapeia "pesquisar_web" → função do item 2
- Popula `context.pesquisa` a partir dos tool calls (pra manter BD compatível)

**System prompt redesenhado:**

```
Você é um planejador de conteúdo de marketing digital de alto nível.

## Seu Processo
1. ANALISE o perfil do cliente e o direcionamento do mês
2. PESQUISE usando a ferramenta pesquisar_web:
   - Tendências atuais relevantes para o nicho
   - Datas comemorativas e sazonais do mês
   - Conteúdo viral que está funcionando no nicho
   - Dados de concorrentes (se informados)
   Faça quantas pesquisas forem necessárias. Seja específico nas queries.
3. ELABORE uma estratégia coerente integrando pesquisa + direcionamento
4. GERE todos os conteúdos seguindo a estratégia

## Output
Retorne APENAS JSON válido (sem markdown, sem texto antes/depois):
{
  "resumo_estrategico": "3-5 frases sobre a estratégia do mês",
  "pesquisa_resumo": "Resumo dos dados pesquisados para referência",
  "temas": [{"tema": str, "pilar": str, "justificativa": str}],
  "conteudos": [
    {
      "tipo": "video_roteiro | arte_estatica | carrossel",
      "pilar": str,
      "framework": "AIDA | PAS | HSO",
      "titulo": str,
      "conteudo": {},
      "variacoes_ab": [{"copy_alternativa": str}],
      "referencia_visual": str,
      "ordem": int
    }
  ],
  "calendario": [{"data": "DD/MM", "tipo": str, "titulo": str}]
}

## Estrutura do campo 'conteudo' por tipo

video_roteiro: {gancho, desenvolvimento, cta, duracao_estimada, formato}
- Gancho: MAX 2 frases. Pergunta ou afirmação CHOCANTE.
- Desenvolvimento: roteiro completo.
- CTA: mencionar EXATAMENTE o destino configurado.

arte_estatica: {titulo_arte, copy, cta_botao, hashtags}
- Copy: MAX 4 frases persuasivas.
- CTA botão: texto curto e direto.

carrossel: {capa: {titulo, subtitulo}, slides: [{titulo, conteudo}], cta_final, copy_legenda, hashtags}
- Slides: 5-7, cada um MAX 3 frases.
- Capa: headline que faz parar de scrollar.

## Regras de Ouro
1. Campo 'tipo' DEVE ser EXATAMENTE: video_roteiro, arte_estatica ou carrossel. NUNCA outro valor.
2. EXATAMENTE o número de peças de cada tipo conforme solicitado
3. Cada pilar DEVE ter pelo menos 1 peça
4. Distribuir datas UNIFORMEMENTE ao longo do mês
5. VARIAR frameworks entre peças (não usar o mesmo 3x seguidas)
6. Cada CTA DEVE mencionar o destino configurado
7. NÃO repetir temas do histórico
8. Gerar 1-2 variações A/B nas peças mais importantes
9. Se há produtos a promover, 50%+ dos temas devem girar em torno deles
10. Perfil do cliente = CONTEXTO (como escrever). Inputs do mês = DIRECIONAMENTO (o que escrever)
11. Tudo em português brasileiro
```

**User prompt com layered context:**

```
--- PERFIL DO CLIENTE (contexto) ---
Empresa: {nome_empresa}
Nicho: {nicho}
Tom de voz: {tom_de_voz}
Público-alvo: {publico_alvo}
Pilares: {pilares}
Instruções especiais: {instrucoes}

--- MÊS E CONFIGURAÇÃO ---
Mês: {mes_referencia}
Foco: {foco}
Destino conversão: {destino_conversao} — TODOS os CTAs devem direcionar para: {destino_conversao}
Tipo uso: {tipo_conteudo_uso}
Plataformas: {plataformas}

--- DIRECIONAMENTO DO MÊS (o que fazer) ---
Produtos a promover: {produtos_promover}
Referências anteriores: {referencias_anteriores}
Feedback reunião: {feedback_reuniao}
Observações: {inputs_extras}

--- RESTRIÇÕES ---
Tipos de conteúdo: {tipos_conteudo} (quantidades exatas)

Temas JÁ USADOS (NÃO repetir):
- 2026-01: tema1, tema2, ...
- 2026-02: tema3, tema4, ...
```

**Extended thinking config:**
```python
thinking = {
    "type": "enabled",
    "budget_tokens": 10000,  # ~10K tokens para pensar na estratégia
}
```

**Populando context.pesquisa:**

Após a geração, os resultados dos tool calls são compilados em um `PesquisaResult` simplificado:
```python
# Cada tool call retorna texto. Compilamos em um resumo.
context.pesquisa = PesquisaResult(
    tendencias=[],  # não estruturamos mais — o Gerador já integrou no raciocínio
    datas_comemorativas=[],
    insights_concorrencia=[],
    conteudo_viral=[],
    resumo=data.get("pesquisa_resumo", ""),  # novo campo no output JSON
)
```

O campo `pesquisa_resumo` no output JSON permite que o Gerador retorne um resumo do que pesquisou, que fica salvo no BD e visível na UI.

### 4. PipelineOrchestrator simplificado

```python
class PipelineOrchestrator:
    def __init__(self, session_factory=None):
        self.client = OpenRouterClient()
        self.gerador = GeradorAgent(self.client)
        self._session_factory = session_factory

    async def run(self, context: PipelineContext) -> PipelineContext:
        context.started_at = datetime.now(timezone.utc).isoformat()
        context.current_status = "em_geracao"

        try:
            # Single step: Gerador com auto-research via tools
            context = await self.gerador.run(context)
            await self._save_progress(context, "gerador")

            context.completed_at = datetime.now(timezone.utc).isoformat()
            context.current_status = "concluido"
        except Exception as e:
            context.current_status = "failed"
            context.completed_at = datetime.now(timezone.utc).isoformat()
            raise
        finally:
            await self.client.close()

        return context
```

Remove import e instanciação do `PesquisadorAgent`.

### 5. PipelineContext cleanup

**Remover:**
- `RevisaoResult` dataclass (não usado em nenhum lugar)
- `revisao: RevisaoResult | None` field
- `iteration: int` field
- `max_iterations: int` field

**Manter:**
- `pesquisa: PesquisaResult | None` — populado pelo Gerador a partir dos tool calls
- Tudo mais permanece

### 6. Celery Task — generation_tasks.py

A task `generate_planejamento_task` não precisa de mudanças estruturais. Ela já:
1. Cria session factory
2. Carrega PipelineContext
3. Chama `PipelineOrchestrator.run()`
4. Salva resultados

A única diferença é que o orchestrator agora executa 1 step em vez de 2. O salvamento funciona igual.

### 7. Logging para WebSocket

O Gerador deve logar cada tool call no `context.decision_log` para que o WebSocket mostre progresso granular:

```python
# Dentro do tool_executor, antes de chamar Sonar:
context.log_decision(
    "gerador",
    f"pesquisando: {query[:80]}",
    "auto-research via tool use",
)
```

O frontend já renderiza `pipeline_logs` — mostrará as pesquisas em tempo real.

## Arquivos Afetados

| Arquivo | Ação | Descrição |
|---------|------|-----------|
| `backend/app/providers/openrouter_client.py` | Editar | Adicionar `chat_with_tools()` |
| `backend/app/agents/tools.py` | **Criar** | Tool `pesquisar_web` |
| `backend/app/agents/gerador.py` | Editar | Refatorar com tool use + extended thinking |
| `backend/app/agents/orchestrator.py` | Editar | Simplificar (remover pesquisador) |
| `backend/app/agents/context.py` | Editar | Cleanup campos não usados |
| `backend/app/agents/pesquisador.py` | **Deletar** | Lógica movida para tools.py |

**Sem mudanças:**
- `backend/app/agents/ajustador.py` — mantém Haiku, sem tool use
- `backend/app/agents/base_agent.py` — sem mudanças
- `backend/app/routers/planejamentos.py` — sem mudanças
- `backend/app/tasks/generation_tasks.py` — sem mudanças estruturais
- `frontend/*` — zero mudanças

## Constraints e Riscos

### Extended Thinking + response_format
Incompatíveis na API Anthropic. Solução: remover `response_format: json_object`, confiar no prompt + `parse_json_safe()`. O Pesquisador atual já funciona assim com Sonar — é um padrão validado no projeto.

### Extended Thinking via OpenRouter
A forma exata de habilitar extended thinking via OpenRouter pode variar. Durante implementação, validar com a documentação atual do OpenRouter. Fallback: se não suportar, remover thinking e manter apenas tool use (já é uma melhoria significativa).

### Tool Use Loop
O modelo pode entrar em loop ou fazer muitas pesquisas. Mitigação: `max_tool_rounds=5` como limite hard.

### Perplexity Sonar Rate Limits
Múltiplas chamadas Sonar em sequência podem bater rate limit. Mitigação: o OpenRouterClient já tem retry com backoff exponencial.

### Backward Compatibility do BD
O campo `pesquisa` (JSONB) continua sendo populado. Planejamentos antigos com pesquisa estruturada (tendências, datas) continuam visíveis. Novos planejamentos terão `resumo` preenchido e arrays vazios — a UI mostra o resumo.

## Custo Estimado

| Componente | Antes | Depois |
|------------|-------|--------|
| Pesquisador (Sonar Pro) | ~$0.02 | — |
| Gerador (Sonnet 4.6) | ~$0.07 | ~$0.07 |
| Tool calls (Sonar ×2-4) | — | ~$0.03 |
| Extended thinking tokens | — | ~$0.10 |
| **Total por plano** | **~$0.09** | **~$0.20** |

Aumento de ~$0.11/plano. Para ~50 planos/mês = +$5.50/mês. Negligível.

## Critérios de Sucesso

1. Pipeline gera planejamento com qualidade >= ao atual
2. Pesquisas são direcionadas ao contexto do mês (não genéricas)
3. Extended thinking produz estratégia mais coerente
4. Tempo total <= 50s (não mais que 25% mais lento)
5. Frontend continua funcionando sem mudanças
6. Ajustes via Ajustador continuam funcionando
7. PDFs e DOCX gerados corretamente
