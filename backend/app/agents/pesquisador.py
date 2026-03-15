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
            "Voce e um pesquisador de marketing digital especializado em "
            "analise de tendencias e benchmarking competitivo.\n\n"
            "Sua tarefa e realizar uma pesquisa de mercado simulada para "
            "subsidiar o planejamento de conteudo mensal de um cliente.\n\n"
            "Voce deve retornar APENAS um JSON valido (sem markdown, sem ```json) "
            "com a seguinte estrutura:\n"
            "{\n"
            '  "tendencias": [{"termo": str, "volume": str, "contexto": str}],\n'
            '  "datas_comemorativas": [{"data": str, "nome": str, "relevancia": str}],\n'
            '  "insights_concorrencia": [{"concorrente": str, "insight": str}],\n'
            '  "conteudo_viral": [{"descricao": str, "porque_viralizou": str}],\n'
            '  "resumo": str\n'
            "}\n\n"
            "Diretrizes:\n"
            "- Identifique 5-8 tendencias relevantes para o nicho\n"
            "- Liste datas comemorativas e sazonais do mes com relevancia para o nicho\n"
            "- Analise os concorrentes e identifique oportunidades\n"
            "- Identifique 3-5 tipos de conteudo que estao viralizando no nicho\n"
            "- O resumo deve ser um paragrafo conciso com os principais insights\n"
            "- Seja especifico para o nicho do cliente, use dados realistas e atuais\n"
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

        response = await self.client.chat(
            model=settings.LLM_MODEL_FAST,
            messages=messages,
            temperature=0.8,
            max_tokens=4096,
            response_format={"type": "json_object"},
        )

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
