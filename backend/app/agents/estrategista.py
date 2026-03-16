import json

from app.agents.base_agent import BaseAgent
from app.agents.context import EstrategiaResult, PipelineContext
from app.config import settings


class EstrategistaAgent(BaseAgent):
    name = "estrategista"

    async def execute(self, context: PipelineContext) -> PipelineContext:
        cliente = context.cliente
        pesquisa = context.pesquisa

        pilares_str = json.dumps(cliente.pilares, ensure_ascii=False)
        tipos_conteudo = context.tipos_conteudo_override or cliente.tipos_conteudo
        tipos_str = json.dumps(tipos_conteudo, ensure_ascii=False)

        system_prompt = (
            "Estrategista de conteudo digital. Retorne APENAS JSON valido (sem markdown).\n\n"
            "Estrutura obrigatoria:\n"
            "{\n"
            '  "temas": [{"tema": str, "pilar": str, "justificativa": str}],\n'
            '  "calendario": [{"data": str, "tipo": str, "titulo": str}],\n'
            '  "resumo_estrategico": str\n'
            "}\n\n"
            "Regras:\n"
            "- Cada pilar DEVE ter pelo menos 1 peca de conteudo\n"
            "- Distribua as datas UNIFORMEMENTE ao longo do mes (nao concentre na 1a semana)\n"
            "- Varie os tipos de conteudo (video_roteiro, arte_estatica, carrossel)\n"
            "- Considere tendencias e datas comemorativas da pesquisa\n"
            "- Se o operador informou produtos a promover, pelo menos 50% dos temas devem girar em torno desses produtos\n"
            "- Se historico de temas foi fornecido, NUNCA repita temas identicos\n"
            "- Cada tema deve ter justificativa estrategica\n"
            "- Tudo em portugues brasileiro\n\n"
            "CONTEXTO vs DIRECIONAMENTO:\n"
            "- Perfil do cliente (nome, nicho, publico, tom, pilares) = CONTEXTO (quem e o cliente)\n"
            "- Inputs extras (produtos, referencias, feedback) = DIRECIONAMENTO (o que fazer este mes)\n"
            "- Temas devem seguir o DIRECIONAMENTO\n"
            "- Referencias do mes anterior = inspiracao para formatos e abordagens"
        )

        user_prompt = (
            f"Crie a estrategia de conteudo mensal para:\n\n"
            f"Empresa: {cliente.nome_empresa}\n"
            f"Nicho: {cliente.nicho}\n"
            f"Publico-alvo: {json.dumps(cliente.publico_alvo, ensure_ascii=False)}\n"
            f"Pilares de conteudo: {pilares_str}\n"
            f"Tipos de conteudo disponiveis: {tipos_str}\n"
            f"Mes de referencia: {context.mes_referencia}\n\n"
        )

        if pesquisa:
            user_prompt += (
                f"Pesquisa de mercado:\n"
                f"- Tendencias: {json.dumps(pesquisa.tendencias, ensure_ascii=False)}\n"
                f"- Datas comemorativas: {json.dumps(pesquisa.datas_comemorativas, ensure_ascii=False)}\n"
                f"- Insights concorrencia: {json.dumps(pesquisa.insights_concorrencia, ensure_ascii=False)}\n"
                f"- Conteudo viral: {json.dumps(pesquisa.conteudo_viral, ensure_ascii=False)}\n"
                f"- Resumo: {pesquisa.resumo}\n\n"
            )

        if context.historico_temas:
            user_prompt += (
                f"Historico de temas (ultimos 3 meses - NAO repetir):\n"
                f"{json.dumps(context.historico_temas, ensure_ascii=False)}\n\n"
            )

        if context.inputs_extras:
            user_prompt += f"Inputs extras do usuario: {context.inputs_extras}\n\n"

        if context.foco:
            user_prompt += f"\nFOCO DO MES: {context.foco}\n"
        if context.destino_conversao:
            user_prompt += f"\nDESTINO DA CONVERSAO: {context.destino_conversao} — Todos os CTAs devem direcionar para: {context.destino_conversao}\n"
        if context.tipo_conteudo_uso:
            user_prompt += f"\nTIPO DE USO: {context.tipo_conteudo_uso}\n"
        if context.plataformas:
            user_prompt += f"\nPLATAFORMAS: {', '.join(context.plataformas)} — Adapte formatos para estas plataformas\n"

        if cliente.instrucoes:
            user_prompt += f"Instrucoes do cliente: {cliente.instrucoes}\n"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = await self.client.chat(
            model=settings.LLM_MODEL,
            messages=messages,
            temperature=0.6,
            max_tokens=4096,
            response_format={"type": "json_object"},
        )

        data = self.parse_json_safe(response)
        context.estrategia = EstrategiaResult(
            temas=data.get("temas", []),
            calendario=data.get("calendario", []),
            resumo_estrategico=data.get("resumo_estrategico", ""),
        )
        return context

    def _get_completion_reasoning(self, context: PipelineContext) -> str:
        e = context.estrategia
        if not e:
            return "Estrategia concluida sem resultados"
        return (
            f"Definidos {len(e.temas)} temas e "
            f"{len(e.calendario)} datas no calendario"
        )
