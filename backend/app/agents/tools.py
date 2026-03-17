"""Tools disponíveis para agents via tool use."""

from app.config import settings
from app.providers.openrouter_client import OpenRouterClient

# Definição da tool no formato OpenAI
PESQUISAR_WEB_TOOL = {
    "type": "function",
    "function": {
        "name": "pesquisar_web",
        "description": (
            "Pesquisa informações atualizadas na web sobre um tópico específico. "
            "Use para buscar tendências de mercado, datas comemorativas, conteúdo viral, "
            "dados de concorrentes, ou qualquer informação atual relevante para criar "
            "o planejamento de conteúdo."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Consulta de pesquisa específica. Inclua o nicho/segmento, "
                        "período temporal, e contexto relevante. "
                        "Ex: 'tendências marketing digital restaurantes março 2026 Brasil'"
                    ),
                }
            },
            "required": ["query"],
        },
    },
}

GERADOR_TOOLS = [PESQUISAR_WEB_TOOL]


async def pesquisar_web(query: str, client: OpenRouterClient) -> str:
    """Executa pesquisa web via Perplexity Sonar."""
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
        model=settings.LLM_MODEL_SEARCH,
        messages=messages,
        temperature=0.6,
        max_tokens=2048,
    )
