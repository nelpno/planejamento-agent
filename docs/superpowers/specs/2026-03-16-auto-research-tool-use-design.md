# Auto-Research via Tool Use + Extended Thinking

**Data:** 2026-03-16
**Status:** Draft (rev.2 — pós spec review)
**Escopo:** Otimizar pipeline de geração do Planejamento Agent

---

## Resumo

Substituir o pipeline de 2 agents sequenciais (Pesquisador → Gerador) por um único agent (Gerador) com tool use e (opcionalmente) extended thinking. O Gerador decide autonomamente o que pesquisar via tool `pesquisar_web`, que chama Perplexity Sonar internamente.

**Faseamento:**
- **Fase 1 (obrigatória):** Tool use — Gerador com `pesquisar_web` tool. Funciona garantidamente via OpenRouter.
- **Fase 2 (condicional):** Extended thinking — habilitado se OpenRouter suportar. Validar na documentação antes de implementar. Se não suportar, Fase 1 já entrega o valor principal.

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
    max_tokens: int = 12288,
    thinking: dict | None = None,
    max_tool_rounds: int = 5,
) -> tuple[str, list[dict]]:
    """
    Chat com suporte a tool use loop.

    Args:
        tools: definições de tools no formato OpenAI
        tool_executor: async callback (tool_name, arguments) -> result_string
        thinking: config de extended thinking (Fase 2, None na Fase 1)
        max_tool_rounds: máximo de rounds de tool use antes de abortar

    Returns:
        (content_final, tool_calls_history)
    """
```

**Parsing da resposta:**

O formato OpenAI/OpenRouter retorna tool calls em `choices[0].message.tool_calls`:
```python
message = data["choices"][0]["message"]
if message.get("tool_calls"):
    for tc in message["tool_calls"]:
        name = tc["function"]["name"]
        args = json.loads(tc["function"]["arguments"])
        result = await tool_executor(name, args)
        # Append tool result message
```

Se extended thinking estiver habilitado (Fase 2), a resposta pode conter blocos de thinking interleaved com content. O `parse_json_safe()` será atualizado para lidar com isso (ver seção de riscos).

**Fluxo interno:**
```
1. Monta payload com tools (+ thinking se Fase 2)
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

**Retry:** Mantém a mesma lógica de retry (429, timeout) do método `chat()` existente. Nota: com até 5 rounds × 120s timeout = 10min no pior caso. O Celery task não tem hard timeout configurado, então isso é seguro.

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
- Extended thinking habilitado (Fase 2, condicional)
- Sem `response_format: json_object` (incompatível com thinking; parse_json_safe já lida)
- Tool executor como closure com acesso ao `self.client` e `context`
- Popula `context.pesquisa` a partir dos tool calls (pra manter BD compatível)

**Wiring do tool_executor no GeradorAgent.execute():**
```python
async def execute(self, context: PipelineContext) -> PipelineContext:
    # ... monta system_prompt e user_prompt ...

    # Tool executor como closure com acesso ao context e client
    async def tool_executor(name: str, args: dict) -> str:
        if name == "pesquisar_web":
            query = args.get("query", "")
            context.log_decision("gerador", f"pesquisando: {query[:80]}", "auto-research")
            # Salva progresso no BD para WebSocket em tempo real
            if self._on_progress:
                await self._on_progress(context, "gerador")
            return await pesquisar_web(query, self.client)
        return f"Tool '{name}' não reconhecida"

    response, tool_history = await self.client.chat_with_tools(
        model=settings.LLM_MODEL,
        messages=messages,
        tools=TOOLS_DEFINITION,
        tool_executor=tool_executor,
        temperature=0.7,
        max_tokens=12288,
    )
    # ... parse JSON e popula context ...
```

O `_on_progress` callback é passado pelo Orchestrator para salvar PipelineLog entries no BD durante execução, permitindo que o WebSocket mostre pesquisas em tempo real.

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

Nota: `inputs_extras` é um texto concatenado (produtos + referências + feedback + extras) montado pela rota `POST /api/planejamentos`. O PipelineContext não tem campos separados — usa `context.inputs_extras` como texto único.

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
{inputs_extras}

--- RESTRIÇÕES ---
Tipos de conteúdo: {tipos_conteudo} (quantidades exatas)

Temas JÁ USADOS (NÃO repetir):
- 2026-01: tema1, tema2, ...
- 2026-02: tema3, tema4, ...
```

**Extended thinking config (Fase 2 — condicional):**

Apenas se OpenRouter suportar. Validar documentação durante implementação.
```python
# Fase 1: thinking=None (sem extended thinking)
# Fase 2 (se suportado):
thinking = {
    "type": "enabled",
    "budget_tokens": 8000,  # 8K tokens para pensar na estratégia
}
```
Se habilitado, `response_format: json_object` NÃO pode ser usado (incompatíveis). O `parse_json_safe()` extrai JSON do response text.

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

        # Passa callback de progresso para o Gerador (WebSocket em tempo real)
        self.gerador._on_progress = self._save_progress

    async def run(self, context: PipelineContext) -> PipelineContext:
        context.started_at = datetime.now(timezone.utc).isoformat()
        context.current_status = "em_geracao"

        try:
            # Single step: Gerador com auto-research via tools
            # Nota: tool calls intermediários já são salvos via _on_progress
            # O save final aqui captura o "gerador completed" do BaseAgent
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

Nota: `_save_progress` usa `context.iteration` que será removido do PipelineContext. Atualizar para usar `iteration=1` hardcoded no PipelineLog insert.

### 5. PipelineContext cleanup

**Remover:**
- `RevisaoResult` dataclass (não usado em nenhum lugar)
- `revisao: RevisaoResult | None` field
- `iteration: int` field
- `max_iterations: int` field

**Manter:**
- `pesquisa: PesquisaResult | None` — populado pelo Gerador a partir dos tool calls
- Tudo mais permanece

### 5.1 BaseAgent — suporte a _on_progress

Adicionar campo `_on_progress: Callable[..., Awaitable[Any]] | None = None` ao BaseAgent para que subclasses possam disparar saves intermediários (usado pelo Gerador para logar tool calls no BD). Deve ser async pois `_save_progress` do Orchestrator é async.

### 6. Celery Task — generation_tasks.py

A task `generate_planejamento_task` não precisa de mudanças estruturais. Ela já:
1. Cria session factory
2. Carrega PipelineContext
3. Chama `PipelineOrchestrator.run()`
4. Salva resultados

A única diferença é que o orchestrator agora executa 1 step em vez de 2. O salvamento funciona igual.

### 7. Logging para WebSocket (tempo real)

O tool_executor dentro do GeradorAgent faz duas coisas ao executar cada pesquisa:
1. `context.log_decision()` — adiciona ao log in-memory
2. `self._on_progress(context, "gerador")` — persiste PipelineLog no BD via session_factory

Isso faz com que o WebSocket (que lê da tabela `pipeline_logs`) mostre cada pesquisa em tempo real:
```
gerador: pesquisando "tendências marketing digital restaurantes março 2026"
gerador: pesquisando "datas comemorativas março 2026 Brasil"
gerador: completed in 42000ms
```

### 8. Frontend — PipelineProgress.tsx (mudança mínima)

O componente tem um array hardcoded `PIPELINE_STEPS` com steps "pesquisador" e "gerador". Com a mudança, o step "pesquisador" nunca aparece nos logs.

**Mudanças necessárias:**
1. Atualizar `PIPELINE_STEPS` para refletir o novo pipeline:
```typescript
const PIPELINE_STEPS = [
  { key: 'gerador', label: 'Gerando Planejamento', icon: PlanIcon },
];
```
2. Remover exibição de "Iteração {log.iteration}" nos logs expandidos (iteration será sempre 1, sem valor informativo).

Ou melhor, tornar os steps dinâmicos baseados nos `pipeline_logs` recebidos via WebSocket, para que pesquisas apareçam como sub-steps do gerador. Decisão de implementação.

### 9. parse_json_safe — suporte a thinking blocks (Fase 2)

Se extended thinking estiver habilitado, a resposta pode conter blocos `<thinking>...</thinking>` antes do JSON. O `parse_json_safe()` deve:
1. Remover blocos `<thinking>...</thinking>` do texto
2. Então aplicar a lógica existente de extração JSON

```python
# Adicionar ao início de parse_json_safe():
import re
text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL)
```

Isso só é necessário na Fase 2. Na Fase 1 (sem thinking), o comportamento atual é suficiente.

## Arquivos Afetados

| Arquivo | Ação | Descrição |
|---------|------|-----------|
| `backend/app/providers/openrouter_client.py` | Editar | Adicionar `chat_with_tools()` |
| `backend/app/agents/tools.py` | **Criar** | Tool `pesquisar_web` + definição |
| `backend/app/agents/gerador.py` | Editar | Refatorar com tool use (+ thinking Fase 2) |
| `backend/app/agents/orchestrator.py` | Editar | Simplificar + passar _on_progress |
| `backend/app/agents/context.py` | Editar | Cleanup campos não usados |
| `backend/app/agents/base_agent.py` | Editar | Adicionar `_on_progress` callback |
| `backend/app/utils/json_parser.py` | Editar | Strip thinking blocks (Fase 2) |
| `backend/app/agents/pesquisador.py` | **Deletar** | Lógica movida para tools.py |
| `frontend/src/components/PipelineProgress.tsx` | Editar | Atualizar PIPELINE_STEPS |

**Cleanup opcional (aproveitando):**
| `backend/app/agents/estrategista.py` | **Deletar** | Legado, não usado |
| `backend/app/agents/planejador.py` | **Deletar** | Legado, não usado |
| `backend/app/agents/revisor.py` | **Deletar** | Legado, não usado |
| `backend/app/prompts/pesquisador.md` | **Deletar** | Legado do Pesquisador |

**Sem mudanças:**
- `backend/app/agents/ajustador.py` — mantém Haiku, sem tool use
- `backend/app/routers/planejamentos.py` — sem mudanças
- `backend/app/tasks/generation_tasks.py` — sem mudanças estruturais
- Banco de dados — sem migrações necessárias

## Constraints e Riscos

### ALTO: Extended Thinking via OpenRouter (Fase 2)
OpenRouter pode não expor a API de extended thinking da Anthropic de forma padrão. O formato `thinking: {"type": "enabled", "budget_tokens": N}` é da API direta. Via OpenRouter, pode ser via `provider.anthropic.thinking` ou não suportado.
**Mitigação:** Fase 2 é condicional. Validar docs do OpenRouter ANTES de implementar. Fase 1 (tool use only) é o plano principal e já entrega valor.

### ALTO: Extended Thinking + response_format
Incompatíveis na API Anthropic. Solução: remover `response_format: json_object`, confiar no prompt + `parse_json_safe()`. O Pesquisador atual já funciona assim com Sonar — padrão validado no projeto.

### MÉDIO: parse_json_safe com thinking blocks (Fase 2)
Se extended thinking retornar `<thinking>...</thinking>` no content, o regex de `parse_json_safe` pode pegar JSON do bloco thinking em vez do output real. Mitigação: strip thinking blocks antes de parsear (ver seção 9).

### MÉDIO: Tempo total do pipeline
Com tool use (2-4 chamadas Sonar) + extended thinking, o tempo pode subir de ~40s para 60-90s. A estimativa de <= 50s é otimista.
**Mitigação:** Celery não tem hard timeout configurado. Ajustar critério de sucesso para <= 60s (Fase 1) e <= 90s (Fase 2).

### MÉDIO: UI mostra pesquisa com arrays vazios
A UI renderiza `pesquisa.tendencias`, `pesquisa.datas_comemorativas`, etc. Com a mudança, esses arrays ficam vazios. O campo `pesquisa_resumo` é novo.
**Mitigação:** Verificar durante implementação como a UI renderiza. Se necessário, ajustar para mostrar `pesquisa_resumo` quando arrays estão vazios. Mudança mínima na UI.

### BAIXO: Tool Use Loop
O modelo pode entrar em loop ou fazer muitas pesquisas. Mitigação: `max_tool_rounds=5` como limite hard.

### BAIXO: Perplexity Sonar Rate Limits
Múltiplas chamadas Sonar em sequência podem bater rate limit. Mitigação: o OpenRouterClient já tem retry com backoff exponencial.

### BAIXO: Backward Compatibility do BD
O campo `pesquisa` (JSONB) continua sendo populado. Planejamentos antigos com pesquisa estruturada (tendências, datas) continuam visíveis. Novos planejamentos terão `resumo` preenchido e arrays vazios. Sem migração necessária.

## Custo Estimado

| Componente | Antes | Fase 1 | Fase 2 |
|------------|-------|--------|--------|
| Pesquisador (Sonar Pro) | ~$0.02 | — | — |
| Gerador (Sonnet 4.6) | ~$0.07 | ~$0.07 | ~$0.07 |
| Tool calls (Sonar ×2-4) | — | ~$0.03 | ~$0.03 |
| Extended thinking tokens | — | — | ~$0.10 |
| **Total por plano** | **~$0.09** | **~$0.10** | **~$0.20** |

Fase 1: custo praticamente igual ao atual (+$0.01). Fase 2: +$0.11/plano (~50 planos/mês = +$5.50/mês). Negligível.

## Critérios de Sucesso

### Fase 1 (Tool Use)
1. Pipeline gera planejamento com qualidade >= ao atual
2. Pesquisas são direcionadas ao contexto do mês (não genéricas)
3. Tempo total <= 60s
4. Frontend mostra progresso das pesquisas via WebSocket
5. Ajustes via Ajustador continuam funcionando
6. PDFs e DOCX gerados corretamente
7. Planejamentos antigos continuam visíveis sem quebrar

### Fase 2 (Extended Thinking — condicional)
8. Extended thinking habilitado via OpenRouter (se suportado)
9. Estratégia mais coerente e fundamentada
10. Tempo total <= 90s (thinking time adicional aceitável)
11. parse_json_safe lida com thinking blocks sem erros
