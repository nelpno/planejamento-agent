"""Agent Gerador — unifica estratégia + criação de conteúdo em uma única chamada."""

import json
from app.agents.base_agent import BaseAgent
from app.agents.context import ConteudoGerado, EstrategiaResult, PipelineContext
from app.config import settings


class GeradorAgent(BaseAgent):
    name = "gerador"

    async def execute(self, context: PipelineContext) -> PipelineContext:
        cliente = context.cliente
        tipos_conteudo = context.tipos_conteudo_override or cliente.tipos_conteudo
        tipos_str = json.dumps(tipos_conteudo, ensure_ascii=False)

        # Build historical themes string
        historico_str = ""
        if context.historico_temas:
            historico_str = "Temas JA USADOS (NAO repetir):\n"
            for h in context.historico_temas:
                historico_str += f"- {h.get('mes', '')}: {', '.join(h.get('temas', []))}\n"

        system_prompt = (
            "Planejador de conteudo de marketing digital. Gere um planejamento mensal COMPLETO.\n\n"
            "Retorne APENAS JSON valido com esta estrutura:\n"
            "{\n"
            '  "resumo_estrategico": "3-5 frases sobre a estrategia do mes",\n'
            '  "temas": [{"tema": str, "pilar": str, "justificativa": str}],\n'
            '  "conteudos": [\n'
            "    {\n"
            '      "tipo": "video_roteiro | arte_estatica | carrossel",\n'
            '      "pilar": str,\n'
            '      "framework": "AIDA | PAS | HSO",\n'
            '      "titulo": str,\n'
            '      "conteudo": {},\n'
            '      "variacoes_ab": [{"copy_alternativa": str}],\n'
            '      "referencia_visual": str,\n'
            '      "ordem": int\n'
            "    }\n"
            "  ],\n"
            '  "calendario": [{"data": "DD/MM", "tipo": str, "titulo": str}]\n'
            "}\n\n"
            "ESTRUTURA do campo 'conteudo' POR TIPO:\n\n"
            "video_roteiro: {gancho, desenvolvimento, cta, duracao_estimada, formato}\n"
            "- Gancho: MAX 2 frases. Pergunta ou afirmacao CHOCANTE.\n"
            "- Desenvolvimento: roteiro completo.\n"
            "- CTA: mencionar EXATAMENTE o destino configurado.\n\n"
            "arte_estatica: {titulo_arte, copy, cta_botao, hashtags}\n"
            "- Copy: MAX 4 frases persuasivas.\n"
            "- CTA botao: texto curto e direto.\n\n"
            "carrossel: {capa: {titulo, subtitulo}, slides: [{titulo, conteudo}], cta_final, copy_legenda, hashtags}\n"
            "- Slides: 5-7, cada um MAX 3 frases.\n"
            "- Capa: headline que faz parar de scrollar.\n\n"
            "REGRAS DE OURO:\n"
            "1. EXATAMENTE o numero de pecas de cada tipo conforme solicitado\n"
            "2. Cada pilar DEVE ter pelo menos 1 peca\n"
            "3. Distribuir datas UNIFORMEMENTE ao longo do mes\n"
            "4. VARIAR frameworks entre pecas (nao usar o mesmo 3x seguidas)\n"
            "5. Cada CTA DEVE mencionar o destino configurado\n"
            "6. NAO repetir temas do historico\n"
            "7. Gerar 1-2 variacoes A/B nas pecas mais importantes\n"
            "8. Se ha produtos a promover, 50%+ dos temas devem girar em torno deles\n"
            "9. Perfil do cliente = CONTEXTO (como escrever). Inputs do mes = DIRECIONAMENTO (o que escrever)\n"
            "10. Tudo em portugues brasileiro"
        )

        user_prompt = (
            f"PERFIL DO CLIENTE (contexto):\n"
            f"Empresa: {cliente.nome_empresa}\n"
            f"Nicho: {cliente.nicho}\n"
            f"Tom de voz: {json.dumps(cliente.tom_de_voz, ensure_ascii=False)}\n"
            f"Publico-alvo: {json.dumps(cliente.publico_alvo, ensure_ascii=False)}\n"
            f"Pilares: {json.dumps(cliente.pilares, ensure_ascii=False)}\n"
            f"Tipos de conteudo: {tipos_str}\n"
        )

        if cliente.instrucoes:
            user_prompt += f"Instrucoes: {cliente.instrucoes}\n"

        user_prompt += f"\nMES: {context.mes_referencia}\n"

        # Pesquisa
        if context.pesquisa:
            user_prompt += f"\nPESQUISA DE MERCADO:\n{context.pesquisa.resumo}\n"
            if context.pesquisa.tendencias:
                user_prompt += "Tendencias: " + ", ".join(t.get("termo","") for t in context.pesquisa.tendencias[:5]) + "\n"
            if context.pesquisa.datas_comemorativas:
                user_prompt += "Datas: " + ", ".join(f"{d.get('data','')} {d.get('nome','')}" for d in context.pesquisa.datas_comemorativas[:3]) + "\n"

        # Direcionamento do mês
        if context.inputs_extras:
            user_prompt += f"\nDIRECIONAMENTO DO MES:\n{context.inputs_extras}\n"

        # Configuração
        if context.foco:
            user_prompt += f"\nFOCO: {context.foco}\n"
        if context.destino_conversao:
            user_prompt += f"DESTINO CONVERSAO: {context.destino_conversao} — TODOS os CTAs devem direcionar para: {context.destino_conversao}\n"
        if context.tipo_conteudo_uso:
            user_prompt += f"TIPO USO: {context.tipo_conteudo_uso}\n"
        if context.plataformas:
            user_prompt += f"PLATAFORMAS: {', '.join(context.plataformas)}\n"

        # Histórico
        if historico_str:
            user_prompt += f"\n{historico_str}\n"

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

        # Parse estratégia
        context.estrategia = EstrategiaResult(
            temas=data.get("temas", []),
            calendario=data.get("calendario", []),
            resumo_estrategico=data.get("resumo_estrategico", ""),
        )

        # Parse conteúdos
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
        temas = len(context.estrategia.temas) if context.estrategia else 0
        return f"Gerados {total} conteudos, {temas} temas, calendario completo"
