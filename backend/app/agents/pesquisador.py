import json

from app.agents.base_agent import BaseAgent
from app.agents.context import PesquisaResult, PipelineContext
from app.config import settings


class PesquisadorAgent(BaseAgent):
    name = "pesquisador"

    async def execute(self, context: PipelineContext) -> PipelineContext:
        cliente = context.cliente
        concorrentes_str = ", ".join(
            c.get("nome", "") for c in cliente.concorrentes
        ) or "nenhum informado"

        system_prompt = (
            "Pesquisador de marketing digital. Retorne APENAS JSON valido (sem markdown).\n\n"
            "Estrutura obrigatoria:\n"
            "{\n"
            '  "tendencias": [{"termo": str, "volume": str, "contexto": str}],\n'
            '  "datas_comemorativas": [{"data": str, "nome": str, "relevancia": str}],\n'
            '  "insights_concorrencia": [{"concorrente": str, "insight": str}],\n'
            '  "conteudo_viral": [{"descricao": str, "porque_viralizou": str}],\n'
            '  "resumo": str\n'
            "}\n\n"
            "Regras:\n"
            "- 5 tendencias relevantes para o nicho\n"
            "- 3 datas comemorativas/sazonais do mes\n"
            "- 3 insights de concorrencia com oportunidades\n"
            "- 3 conteudos virais do nicho\n"
            "- Resumo: 1 paragrafo com principais insights\n"
            "- Dados especificos e atuais para o nicho\n"
            "- Tudo em portugues brasileiro"
        )

        user_prompt = (
            f"Realize uma pesquisa de mercado para o seguinte cliente:\n\n"
            f"Empresa: {cliente.nome_empresa}\n"
            f"Nicho: {cliente.nicho}\n"
            f"Publico-alvo: {json.dumps(cliente.publico_alvo, ensure_ascii=False)}\n"
            f"Concorrentes: {concorrentes_str}\n"
            f"Mes de referencia: {context.mes_referencia}\n"
        )

        if cliente.instrucoes:
            user_prompt += f"\nInstrucoes adicionais: {cliente.instrucoes}\n"

        if context.inputs_extras:
            user_prompt += f"\nInputs extras do usuario: {context.inputs_extras}\n"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # Perplexity Sonar has native web search - no response_format support
        use_search = settings.LLM_MODEL_SEARCH and "perplexity" in settings.LLM_MODEL_SEARCH
        model = settings.LLM_MODEL_SEARCH if use_search else settings.LLM_MODEL_FAST
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": 0.6,
            "max_tokens": 4096,
        }
        if not use_search:
            kwargs["response_format"] = {"type": "json_object"}

        response = await self.client.chat(**kwargs)

        data = self.parse_json_safe(response)
        context.pesquisa = PesquisaResult(
            tendencias=data.get("tendencias", []),
            datas_comemorativas=data.get("datas_comemorativas", []),
            insights_concorrencia=data.get("insights_concorrencia", []),
            conteudo_viral=data.get("conteudo_viral", []),
            resumo=data.get("resumo", ""),
        )
        return context

    def _get_completion_reasoning(self, context: PipelineContext) -> str:
        p = context.pesquisa
        if not p:
            return "Pesquisa concluida sem resultados"
        return (
            f"Encontradas {len(p.tendencias)} tendencias, "
            f"{len(p.datas_comemorativas)} datas comemorativas, "
            f"{len(p.insights_concorrencia)} insights de concorrencia, "
            f"{len(p.conteudo_viral)} conteudos virais"
        )
