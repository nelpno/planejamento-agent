import json

from app.agents.base_agent import BaseAgent
from app.agents.context import ConteudoGerado, PipelineContext
from app.config import settings


class PlanejadorAgent(BaseAgent):
    name = "planejador"

    async def execute(self, context: PipelineContext) -> PipelineContext:
        cliente = context.cliente
        estrategia = context.estrategia

        tipos_conteudo = context.tipos_conteudo_override or cliente.tipos_conteudo
        tipos_str = json.dumps(tipos_conteudo, ensure_ascii=False)

        system_prompt = (
            "Voce e um redator e planejador de conteudo digital especializado em "
            "criar conteudos persuasivos e engajantes para redes sociais.\n\n"
            "Sua tarefa e gerar cada peca de conteudo do calendario mensal, "
            "aplicando frameworks de copywriting e adaptando ao tom de voz do cliente.\n\n"
            "Voce deve retornar APENAS um JSON valido (sem markdown, sem ```json) "
            "com a seguinte estrutura:\n"
            "{\n"
            '  "conteudos": [\n'
            "    {\n"
            '      "tipo": str,\n'
            '      "pilar": str,\n'
            '      "framework": str,\n'
            '      "titulo": str,\n'
            '      "conteudo": {},\n'
            '      "variacoes_ab": [{}],\n'
            '      "referencia_visual": str,\n'
            '      "ordem": int\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            "Estrutura do campo 'conteudo' por tipo:\n\n"
            "video_roteiro:\n"
            "  - gancho (texto de 0-3 segundos para prender atencao)\n"
            "  - desenvolvimento (roteiro com timeline em segundos)\n"
            "  - cta (chamada para acao final)\n"
            "  - duracao_estimada (em segundos)\n"
            "  - formato (reels/stories/feed)\n\n"
            "arte_estatica:\n"
            "  - titulo_arte (texto principal da arte)\n"
            "  - copy (texto persuasivo para legenda)\n"
            "  - cta_botao (texto do botao/CTA)\n"
            "  - hashtags (lista de hashtags relevantes)\n\n"
            "carrossel:\n"
            "  - capa (titulo e subtitulo da capa)\n"
            "  - slides (lista de slides com titulo e conteudo)\n"
            "  - cta_final (ultimo slide com chamada para acao)\n"
            "  - copy_legenda (texto da legenda)\n"
            "  - hashtags (lista de hashtags)\n\n"
            "Diretrizes:\n"
            "- Aplique frameworks variados: AIDA, PAS, Hook-Story-Offer, BAB, 4Us\n"
            "- NAO repita o mesmo framework em pecas consecutivas\n"
            "- Gere 2-3 variacoes de copy (A/B) para pecas estrategicas\n"
            "- Adapte o tom de voz ao perfil do cliente\n"
            "- Inclua CTAs claros em TODAS as pecas\n"
            "- A referencia_visual deve descrever brevemente o estilo visual sugerido\n"
            "- Numere as pecas em ordem de publicacao (campo ordem)\n"
            "- Tudo em portugues brasileiro"
        )

        calendario_str = json.dumps(
            estrategia.calendario, ensure_ascii=False
        ) if estrategia else "[]"
        temas_str = json.dumps(
            estrategia.temas, ensure_ascii=False
        ) if estrategia else "[]"

        user_prompt = (
            f"Gere os conteudos para o planejamento mensal:\n\n"
            f"Empresa: {cliente.nome_empresa}\n"
            f"Nicho: {cliente.nicho}\n"
            f"Tom de voz: {json.dumps(cliente.tom_de_voz, ensure_ascii=False)}\n"
            f"Publico-alvo: {json.dumps(cliente.publico_alvo, ensure_ascii=False)}\n"
            f"Pilares: {json.dumps(cliente.pilares, ensure_ascii=False)}\n"
            f"Tipos de conteudo disponiveis: {tipos_str}\n\n"
            f"Temas definidos: {temas_str}\n"
            f"Calendario: {calendario_str}\n"
            f"Resumo estrategico: {estrategia.resumo_estrategico if estrategia else ''}\n"
        )

        if cliente.instrucoes:
            user_prompt += f"\nInstrucoes do cliente: {cliente.instrucoes}\n"

        # If this is a revision iteration, include reviewer feedback
        if context.revisao and not context.revisao.aprovado:
            user_prompt += (
                f"\n\nATENCAO - Revisao anterior reprovou o conteudo. "
                f"Score: {context.revisao.score}/100\n"
                f"Notas do revisor:\n"
            )
            for nota in context.revisao.notas:
                user_prompt += f"- {nota}\n"
            user_prompt += (
                "\nCorriga os problemas apontados e gere os conteudos novamente."
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = await self.client.chat(
            model=settings.LLM_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=8192,
            response_format={"type": "json_object"},
        )

        data = json.loads(response)
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
        return context

    def _get_completion_reasoning(self, context: PipelineContext) -> str:
        total = len(context.conteudos)
        tipos = {}
        for c in context.conteudos:
            tipos[c.tipo] = tipos.get(c.tipo, 0) + 1
        tipos_str = ", ".join(f"{k}: {v}" for k, v in tipos.items())
        return f"Gerados {total} conteudos ({tipos_str})"
