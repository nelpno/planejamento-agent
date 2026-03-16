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
            "Editor de conteudo de marketing. Retorne APENAS JSON valido (sem markdown).\n\n"
            "Estrutura obrigatoria:\n"
            '{"resumo_ajustes": str, "conteudos": [{"ordem": int, "tipo": str, "pilar": str, '
            '"framework": str, "titulo": str, "conteudo": {}, "variacoes_ab": [{}], '
            '"referencia_visual": str, "alterado": bool}]}\n\n'
            "REGRAS:\n"
            "- Retorne TODOS os conteudos. Os NAO alterados devem ser copiados EXATAMENTE como estao.\n"
            "- Se o feedback menciona uma peca especifica (ex: 'video 3'), altere APENAS essa.\n"
            "- Se o feedback e generico (ex: 'melhorar ganchos'), aplique a todas as pecas relevantes.\n"
            "- NAO refaca do zero. Ajuste cirurgicamente.\n"
            "- Marque cada peca com 'alterado': true/false.\n"
            "- Mantenha tom de voz, pilares e frameworks do cliente.\n"
            "- Tudo em portugues brasileiro."
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
            model=settings.LLM_MODEL_FAST,  # Haiku — tarefa simples, mais econômico
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
