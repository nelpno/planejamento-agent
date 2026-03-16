import json

from app.agents.base_agent import BaseAgent
from app.agents.context import PipelineContext, RevisaoResult
from app.config import settings


class RevisorAgent(BaseAgent):
    name = "revisor"

    async def execute(self, context: PipelineContext) -> PipelineContext:
        cliente = context.cliente

        conteudos_para_revisao = [
            {
                "ordem": c.ordem,
                "tipo": c.tipo,
                "pilar": c.pilar,
                "framework": c.framework,
                "titulo": c.titulo,
                "conteudo": c.conteudo,
                "variacoes_ab": c.variacoes_ab,
                "referencia_visual": c.referencia_visual,
            }
            for c in context.conteudos
        ]

        system_prompt = (
            "Revisor de conteudo digital. Retorne APENAS JSON valido (sem markdown).\n\n"
            "Estrutura obrigatoria:\n"
            "{\n"
            '  "score": int (0-100),\n'
            '  "aprovado": bool,\n'
            '  "notas": [str],\n'
            '  "rubrica": {"tom_de_voz": int, "ctas_destino": int, "pilares_distribuidos": int, "storytelling_engajamento": int, "completude_tecnica": int}\n'
            "}\n\n"
            "RUBRICA (cada criterio 0-20, soma = score):\n"
            "- tom_de_voz (0-20): Conteudos respeitam o tom definido pelo cliente?\n"
            "- ctas_destino (0-20): Todos os CTAs sao claros e mencionam o destino correto?\n"
            "- pilares_distribuidos (0-20): Pilares equilibrados, datas bem distribuidas?\n"
            "- storytelling_engajamento (0-20): Ganchos impactantes, storytelling unico, nao generico?\n"
            "- completude_tecnica (0-20): Campos preenchidos, comprimentos adequados (gancho <=2 frases, copy arte <=4 frases, slides <=3 frases), variacoes A/B presentes?\n\n"
            f"Score minimo para aprovacao: {settings.QUALITY_THRESHOLD}\n"
            "- Se score < 70: REPROVAR. Notas devem listar problemas especificos para correcao.\n"
            "- Se score >= 70: APROVAR. Notas podem incluir sugestoes menores.\n"
            "- NAO retorne conteudos. Apenas score + rubrica + notas.\n"
            "- Tudo em portugues brasileiro"
        )

        user_prompt = (
            f"Revise os conteudos abaixo:\n\n"
            f"Perfil do cliente:\n"
            f"- Empresa: {cliente.nome_empresa}\n"
            f"- Nicho: {cliente.nicho}\n"
            f"- Tom de voz: {json.dumps(cliente.tom_de_voz, ensure_ascii=False)}\n"
            f"- Pilares: {json.dumps(cliente.pilares, ensure_ascii=False)}\n\n"
            f"Conteudos para revisao:\n"
            f"{json.dumps(conteudos_para_revisao, ensure_ascii=False, indent=2)}\n"
        )

        if context.destino_conversao:
            user_prompt += f"\nVERIFIQUE: Todos os CTAs direcionam para {context.destino_conversao}?\n"
        if context.foco:
            user_prompt += f"\nVERIFIQUE: O conteudo esta alinhado com o foco: {context.foco}?\n"

        if context.estrategia:
            user_prompt += (
                f"\nEstrategia definida:\n"
                f"- Resumo: {context.estrategia.resumo_estrategico}\n"
                f"- Temas: {json.dumps(context.estrategia.temas, ensure_ascii=False)}\n"
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = await self.client.chat(
            model=settings.LLM_MODEL,
            messages=messages,
            temperature=0.1,
            max_tokens=4096,
            response_format={"type": "json_object"},
        )

        data = self.parse_json_safe(response)
        context.revisao = RevisaoResult(
            score=data.get("score", 0),
            aprovado=data.get("aprovado", False),
            notas=data.get("notas", []),
            conteudos_revisados=[],  # Revisor nao retorna mais conteudos
        )
        return context

    def _get_completion_reasoning(self, context: PipelineContext) -> str:
        r = context.revisao
        if not r:
            return "Revisao concluida sem resultados"
        status = "APROVADO" if r.aprovado else "REPROVADO"
        return (
            f"Score: {r.score}/100 - {status}. "
            f"{len(r.notas)} notas"
        )
