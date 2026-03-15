"""Agent Ajustador — revisa conteúdo existente com base em feedback sem refazer do zero."""

import json

from app.agents.base_agent import BaseAgent
from app.agents.context import ConteudoGerado, PipelineContext
from app.config import settings


class AjustadorAgent(BaseAgent):
    name = "ajustador"

    async def execute(self, context: PipelineContext) -> PipelineContext:
        cliente = context.cliente
        feedback = context.inputs_extras or ""

        # Serialize existing content for the LLM
        conteudos_atuais = json.dumps(
            [
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
            ],
            ensure_ascii=False,
            indent=2,
        )

        system_prompt = (
            "Voce e um editor de conteudo de marketing digital especializado em revisao e ajustes.\n\n"
            "Sua tarefa e AJUSTAR um planejamento de conteudo existente com base no feedback do operador.\n\n"
            "REGRAS IMPORTANTES:\n"
            "- NAO refaca tudo do zero. Ajuste APENAS o que foi solicitado no feedback.\n"
            "- Mantenha todo o conteudo que nao foi mencionado no feedback EXATAMENTE como esta.\n"
            "- Se o feedback menciona uma peca especifica (ex: 'video 2'), ajuste apenas essa peca.\n"
            "- Se o feedback e generico (ex: 'melhorar os ganchos'), aplique a todas as pecas relevantes.\n"
            "- Mantenha o tom de voz, pilares e frameworks do cliente.\n"
            "- Retorne TODOS os conteudos (ajustados e nao-ajustados) no mesmo formato.\n\n"
            "Retorne APENAS JSON valido com esta estrutura:\n"
            "{\n"
            '  "resumo_ajustes": "Descricao breve do que foi alterado",\n'
            '  "conteudos": [\n'
            "    {\n"
            '      "ordem": int,\n'
            '      "tipo": str,\n'
            '      "pilar": str,\n'
            '      "framework": str,\n'
            '      "titulo": str,\n'
            '      "conteudo": {},\n'
            '      "variacoes_ab": [{}],\n'
            '      "referencia_visual": str,\n'
            '      "alterado": true/false\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            "O campo 'alterado' indica se a peca foi modificada (true) ou mantida igual (false).\n"
            "Tudo em portugues brasileiro."
        )

        user_prompt = (
            f"PERFIL DO CLIENTE:\n"
            f"Empresa: {cliente.nome_empresa}\n"
            f"Nicho: {cliente.nicho}\n"
            f"Tom de voz: {json.dumps(cliente.tom_de_voz, ensure_ascii=False)}\n\n"
            f"FEEDBACK DO OPERADOR:\n{feedback}\n\n"
            f"CONTEUDO ATUAL A SER AJUSTADO:\n{conteudos_atuais}\n"
        )

        if cliente.instrucoes:
            user_prompt += f"\nInstrucoes do cliente: {cliente.instrucoes}\n"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = await self.client.chat(
            model=settings.LLM_MODEL,
            messages=messages,
            temperature=0.3,
            max_tokens=12288,
            response_format={"type": "json_object"},
        )

        data = self.parse_json_safe(response)
        conteudos_raw = data.get("conteudos", [])

        context.conteudos = [
            ConteudoGerado(
                tipo=c.get("tipo", ""),
                pilar=c.get("pilar", ""),
                framework=c.get("framework", ""),
                titulo=c.get("titulo", ""),
                conteudo=c.get("conteudo", {}),
                variacoes_ab=c.get("variacoes_ab", []),
                referencia_visual=c.get("referencia_visual", ""),
                ordem=c.get("ordem", i),
            )
            for i, c in enumerate(conteudos_raw)
        ]

        # Log what was changed
        alterados = [c.get("titulo", "") for c in conteudos_raw if c.get("alterado")]
        resumo = data.get("resumo_ajustes", "")
        context.log_decision(
            self.name,
            f"Ajustadas {len(alterados)} pecas: {', '.join(alterados[:3])}",
            resumo,
        )

        return context

    def _get_completion_reasoning(self, context: PipelineContext) -> str:
        return f"Ajuste concluido com {len(context.conteudos)} pecas"
