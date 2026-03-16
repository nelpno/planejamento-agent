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
            "Redator de conteudo digital. Retorne APENAS JSON valido (sem markdown).\n\n"
            "Estrutura obrigatoria:\n"
            '{"conteudos": [{"tipo": str, "pilar": str, "framework": str, "titulo": str, '
            '"conteudo": {}, "variacoes_ab": [{}], "referencia_visual": str, "ordem": int}]}\n\n'
            "Campo 'conteudo' por tipo:\n"
            "video_roteiro: gancho, desenvolvimento, cta, duracao_estimada, formato\n"
            "arte_estatica: titulo_arte, copy, cta_botao, hashtags\n"
            "carrossel: capa{titulo,subtitulo}, slides[{titulo,conteudo}], cta_final, copy_legenda, hashtags\n\n"
            "REGRAS DE QUALIDADE:\n"
            "- Gere EXATAMENTE o numero de pecas de cada tipo conforme o calendario\n"
            "- Ganchos de video: DEVEM ser pergunta ou afirmacao chocante (max 2 frases)\n"
            "- Copies de arte: max 4 frases\n"
            "- Slides de carrossel: max 3 frases cada\n"
            "- Cada CTA DEVE mencionar especificamente o destino configurado (ex: WhatsApp, link na bio)\n"
            "- NUNCA use frameworks genericos. Cada peca deve ter storytelling unico\n"
            "- Varie frameworks (AIDA, PAS, HSO, BAB, 4Us) — NAO repita em pecas consecutivas\n"
            "- Gere 1-2 variacoes A/B para pecas estrategicas\n"
            "- Numere em ordem de publicacao\n"
            "- Tudo em portugues brasileiro\n\n"
            "DIRECIONAMENTO: O perfil do cliente e o COMO escrever, nao o QUE. "
            "Inputs extras e foco do mes definem O QUE escrever.\n\n"
            "EXEMPLO (video_roteiro, framework PAS):\n"
            "{\n"
            '  "tipo": "video_roteiro", "pilar": "Educacao", "framework": "PAS",\n'
            '  "titulo": "Acidente de Trabalho - Seus Direitos",\n'
            '  "conteudo": {\n'
            '    "gancho": "Sofreu um acidente de trabalho e a empresa fingiu que nada aconteceu?",\n'
            '    "desenvolvimento": "Voce sente dor, ficou afastado e nao recebeu nada. Isso e errado. Direitos: indenizacao, pensao vitalicia, tratamento custeado pela empresa.",\n'
            '    "cta": "Fale agora com nossa equipe no WhatsApp e entenda seus direitos.",\n'
            '    "duracao_estimada": "60s", "formato": "reels"\n'
            "  },\n"
            '  "variacoes_ab": [{"copy_alternativa": "Voce sabia que pode receber indenizacao por acidente de trabalho?"}],\n'
            '  "referencia_visual": "Pessoa preocupada, transicao para advogado confiante", "ordem": 1\n'
            "}"
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

        if context.foco:
            user_prompt += f"\nFOCO DO MES: {context.foco}\n"
            if context.foco == "vendas_ecommerce":
                user_prompt += "CTAs devem direcionar para compra, usar urgencia e escassez\n"
            elif context.foco == "geracao_leads":
                user_prompt += "CTAs devem captar contato, usar prova social\n"
        if context.destino_conversao:
            user_prompt += f"\nDESTINO DA CONVERSAO: {context.destino_conversao} — Todos os CTAs devem direcionar para: {context.destino_conversao}\n"
            if context.destino_conversao == "whatsapp":
                user_prompt += "Todos os CTAs devem incluir chamada para WhatsApp\n"
            elif context.destino_conversao == "loja_online":
                user_prompt += "CTAs devem incluir 'link na bio', 'compre agora', mencionar site\n"
        if context.tipo_conteudo_uso:
            user_prompt += f"\nTIPO DE USO: {context.tipo_conteudo_uso}\n"
            if context.tipo_conteudo_uso == "pago":
                user_prompt += "Copies curtas e diretas, hooks nos primeiros 3 segundos, formato ads\n"
            elif context.tipo_conteudo_uso == "organico":
                user_prompt += "Tom mais natural, storytelling, hashtags relevantes\n"
        if context.plataformas:
            user_prompt += f"\nPLATAFORMAS: {', '.join(context.plataformas)} — Adapte formatos para estas plataformas\n"

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
        return context

    def _get_completion_reasoning(self, context: PipelineContext) -> str:
        total = len(context.conteudos)
        tipos = {}
        for c in context.conteudos:
            tipos[c.tipo] = tipos.get(c.tipo, 0) + 1
        tipos_str = ", ".join(f"{k}: {v}" for k, v in tipos.items())
        return f"Gerados {total} conteudos ({tipos_str})"
