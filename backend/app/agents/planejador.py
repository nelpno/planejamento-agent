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
            "- Tudo em portugues brasileiro\n\n"
            "EXEMPLOS DE CONTEUDO DE ALTA QUALIDADE:\n\n"
            "--- EXEMPLO VIDEO_ROTEIRO (Framework PAS) ---\n"
            "{\n"
            '  "tipo": "video_roteiro",\n'
            '  "pilar": "Educacao",\n'
            '  "framework": "PAS",\n'
            '  "titulo": "Acidente de Trabalho - Seus Direitos",\n'
            '  "conteudo": {\n'
            '    "gancho": "Sofreu um acidente de trabalho e a empresa fingiu que nada aconteceu?",\n'
            '    "desenvolvimento": "Voce sente dor, ficou afastado e nao recebeu nada em troca? Isso e errado. Voce pode ter direito a: indenizacao por danos morais e esteticos, pensao mensal vitalicia, tratamento medico custeado pela empresa. Mas atencao: esses direitos so sao garantidos com um advogado especializado.",\n'
            '    "cta": "Nao deixe passar! Fale agora com nossa equipe e entenda o que e seu por lei.",\n'
            '    "duracao_estimada": "60s",\n'
            '    "formato": "reels"\n'
            "  },\n"
            '  "variacoes_ab": [\n'
            '    {"copy_alternativa": "Voce sabia que pode receber indenizacao por acidente de trabalho? A empresa e obrigada a pagar."}\n'
            "  ],\n"
            '  "referencia_visual": "Pessoa com expressao preocupada, transicao para advogado confiante",\n'
            '  "ordem": 1\n'
            "}\n\n"
            "--- EXEMPLO ARTE_ESTATICA (Framework AIDA) ---\n"
            "{\n"
            '  "tipo": "arte_estatica",\n'
            '  "pilar": "Conversao",\n'
            '  "framework": "AIDA",\n'
            '  "titulo": "Dispensa Discriminatoria",\n'
            '  "conteudo": {\n'
            '    "titulo_arte": "FOI DEMITIDO POR PRECONCEITO?",\n'
            '    "copy": "Quando a demissao ocorre por motivo de raca, genero, doenca ou gravidez, e nao pelo desempenho, o trabalhador tem direito a reintegracao ou indenizacao em dobro, alem de dano moral.",\n'
            '    "cta_botao": "CONVERSE COM NOSSA EQUIPE JURIDICA",\n'
            '    "hashtags": ["#direitotrabalhista", "#discriminacao", "#seudireito"]\n'
            "  },\n"
            '  "variacoes_ab": [\n'
            '    {"copy_alternativa": "Demissao por discriminacao e ILEGAL. Voce pode ter direito a indenizacao em DOBRO."}\n'
            "  ],\n"
            '  "referencia_visual": "Fundo escuro, texto branco em destaque, icone de justica",\n'
            '  "ordem": 2\n'
            "}\n\n"
            "--- EXEMPLO CARROSSEL (Framework Hook-Story-Offer) ---\n"
            "{\n"
            '  "tipo": "carrossel",\n'
            '  "pilar": "Educacao",\n'
            '  "framework": "HSO",\n'
            '  "titulo": "5 Direitos que Todo Trabalhador Tem",\n'
            '  "conteudo": {\n'
            '    "capa": {"titulo": "5 DIREITOS QUE VOCE NAO SABIA QUE TEM", "subtitulo": "Salve este post!"},\n'
            '    "slides": [\n'
            '      {"titulo": "1. Horas Extras", "conteudo": "Toda hora extra deve ser paga com adicional minimo de 50%. Se nao recebe, pode cobrar os ultimos 5 anos."},\n'
            '      {"titulo": "2. Intervalo", "conteudo": "Jornada de 6h+ exige 1h de intervalo. Se nao cumprem, devem pagar como hora extra."},\n'
            '      {"titulo": "3. FGTS", "conteudo": "A empresa DEVE depositar 8% do seu salario todo mes. Verifique no app FGTS."},\n'
            '      {"titulo": "4. Adicional Noturno", "conteudo": "Trabalhou entre 22h e 5h? Tem direito a 20% a mais no salario."},\n'
            '      {"titulo": "5. Ferias", "conteudo": "Ferias nao pagas geram multa em DOBRO. Nao aceite calado."}\n'
            "    ],\n"
            '    "cta_final": "Acha que seus direitos estao sendo violados? Fale com um especialista AGORA.",\n'
            '    "copy_legenda": "Salve esse post e compartilhe com quem precisa saber!",\n'
            '    "hashtags": ["#direitostrabalhistas", "#CLT", "#seudireito"]\n'
            "  },\n"
            '  "variacoes_ab": [],\n'
            '  "referencia_visual": "Design limpo, numeracao em destaque, cores da marca",\n'
            '  "ordem": 3\n'
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
