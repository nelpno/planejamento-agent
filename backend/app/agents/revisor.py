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
            "Voce e um revisor de conteudo digital especializado em controle "
            "de qualidade para planejamentos de marketing.\n\n"
            "Sua tarefa e revisar os conteudos gerados, validar a qualidade, "
            "consistencia e aderencia ao perfil do cliente, e atribuir uma "
            "nota de 0 a 100.\n\n"
            "Voce deve retornar APENAS um JSON valido (sem markdown, sem ```json) "
            "com a seguinte estrutura:\n"
            "{\n"
            '  "score": int,\n'
            '  "aprovado": bool,\n'
            '  "notas": [str],\n'
            '  "conteudos_revisados": [{}]\n'
            "}\n\n"
            "Criterios de avaliacao (peso igual):\n"
            "1. Tom de voz: Os conteudos respeitam o tom definido pelo cliente?\n"
            "2. CTAs: Todas as pecas possuem chamadas para acao claras?\n"
            "3. Distribuicao de pilares: Os pilares estao equilibrados?\n"
            "4. Variacao de frameworks: Ha diversidade nos frameworks usados?\n"
            "5. Qualidade do copy: Os textos sao persuasivos e sem erros?\n"
            "6. Coerencia estrategica: Os conteudos seguem a estrategia definida?\n"
            "7. Completude: Todos os campos obrigatorios estao preenchidos?\n"
            "8. Variacoes A/B: Os campos copy_alternativa estao preenchidos nas variacoes_ab?\n\n"
            "Diretrizes:\n"
            f"- Score minimo para aprovacao: {settings.QUALITY_THRESHOLD}\n"
            "- Se reprovar, liste os problemas especificos em 'notas'\n"
            "- Se aprovar, inclua pontos positivos em 'notas'\n"
            "- Em 'conteudos_revisados', inclua apenas os conteudos que "
            "precisaram de correcoes, com as correcoes ja aplicadas\n"
            "- Se o score ficar entre 70-79, aprove mas liste os ajustes menores aplicados\n"
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
            max_tokens=6144,
            response_format={"type": "json_object"},
        )

        data = self.parse_json_safe(response)
        context.revisao = RevisaoResult(
            score=data.get("score", 0),
            aprovado=data.get("aprovado", False),
            notas=data.get("notas", []),
            conteudos_revisados=data.get("conteudos_revisados", []),
        )
        return context

    def _get_completion_reasoning(self, context: PipelineContext) -> str:
        r = context.revisao
        if not r:
            return "Revisao concluida sem resultados"
        status = "APROVADO" if r.aprovado else "REPROVADO"
        return (
            f"Score: {r.score}/100 - {status}. "
            f"{len(r.notas)} notas, "
            f"{len(r.conteudos_revisados)} conteudos corrigidos"
        )
