"""Agent Gerador — gera estratégia + conteúdo com auto-research via tool use."""

import json
import logging

from app.agents.base_agent import BaseAgent
from app.agents.context import ConteudoGerado, EstrategiaResult, PesquisaResult, PipelineContext
from app.agents.tools import GERADOR_TOOLS, pesquisar_web
from app.config import settings

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = (
    "Você é um planejador de conteúdo de marketing digital de alto nível.\n\n"
    "## Seu Processo\n"
    "1. ANALISE o perfil do cliente e o direcionamento do mês\n"
    "2. PESQUISE usando a ferramenta pesquisar_web:\n"
    "   - Tendências atuais relevantes para o nicho\n"
    "   - Datas comemorativas e sazonais do mês\n"
    "   - Conteúdo viral que está funcionando no nicho\n"
    "   - Dados de concorrentes (se informados)\n"
    "   Faça quantas pesquisas forem necessárias. Seja específico nas queries.\n"
    "3. ELABORE uma estratégia coerente integrando pesquisa + direcionamento\n"
    "4. GERE todos os conteúdos seguindo a estratégia\n\n"
    "## Output\n"
    "Retorne APENAS JSON válido (sem markdown, sem texto antes/depois):\n"
    "{\n"
    '  "resumo_estrategico": "3-5 frases sobre a estratégia do mês",\n'
    '  "pesquisa_resumo": "Resumo dos dados pesquisados para referência",\n'
    '  "temas": [{"tema": str, "pilar": str, "justificativa": str}],\n'
    '  "conteudos": [\n'
    "    {\n"
    '      "tipo": "video_roteiro OU arte_estatica OU carrossel (SOMENTE esses 3 valores)",\n'
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
    "## Estrutura do campo 'conteudo' por tipo\n\n"
    "video_roteiro: {gancho, desenvolvimento, cta, duracao_estimada, formato}\n"
    "- Gancho: MAX 2 frases. Pergunta ou afirmação CHOCANTE.\n"
    "- Desenvolvimento: roteiro completo.\n"
    "- CTA: mencionar EXATAMENTE o destino configurado.\n\n"
    "arte_estatica: {titulo_arte, copy, cta_botao, hashtags}\n"
    "- Copy: MAX 4 frases persuasivas.\n"
    "- CTA botão: texto curto e direto.\n\n"
    "carrossel: {capa: {titulo, subtitulo}, slides: [{titulo, conteudo}], cta_final, copy_legenda, hashtags}\n"
    "- Slides: 5-7, cada um MAX 3 frases.\n"
    "- Capa: headline que faz parar de scrollar.\n\n"
    "## Regras de Ouro\n"
    "1. Campo 'tipo' DEVE ser EXATAMENTE: video_roteiro, arte_estatica ou carrossel. NUNCA outro valor.\n"
    "2. EXATAMENTE o número de peças de cada tipo conforme solicitado\n"
    "3. Cada pilar DEVE ter pelo menos 1 peça\n"
    "4. Distribuir datas UNIFORMEMENTE ao longo do mês\n"
    "5. VARIAR frameworks entre peças (não usar o mesmo 3x seguidas)\n"
    "6. Cada CTA DEVE mencionar o destino configurado\n"
    "7. NÃO repetir temas do histórico\n"
    "8. Gerar 1-2 variações A/B nas peças mais importantes\n"
    "9. Se há produtos a promover, 50%+ dos temas devem girar em torno deles\n"
    "10. Perfil do cliente = CONTEXTO (como escrever). Inputs do mês = DIRECIONAMENTO (o que escrever)\n"
    "11. Tudo em português brasileiro"
)


class GeradorAgent(BaseAgent):
    name = "gerador"

    def _build_user_prompt(self, context: PipelineContext) -> str:
        cliente = context.cliente
        tipos_conteudo = context.tipos_conteudo_override or cliente.tipos_conteudo
        tipos_str = json.dumps(tipos_conteudo, ensure_ascii=False)

        parts = [
            f"--- PERFIL DO CLIENTE (contexto) ---\n"
            f"Empresa: {cliente.nome_empresa}\n"
            f"Nicho: {cliente.nicho}\n"
            f"Tom de voz: {json.dumps(cliente.tom_de_voz, ensure_ascii=False)}\n"
            f"Público-alvo: {json.dumps(cliente.publico_alvo, ensure_ascii=False)}\n"
            f"Pilares: {json.dumps(cliente.pilares, ensure_ascii=False)}"
        ]

        if cliente.instrucoes:
            parts.append(f"Instruções especiais: {cliente.instrucoes}")

        parts.append(f"\n--- MÊS E CONFIGURAÇÃO ---\nMês: {context.mes_referencia}")

        if context.foco:
            parts.append(f"Foco: {context.foco}")
        if context.destino_conversao:
            parts.append(f"Destino conversão: {context.destino_conversao} — TODOS os CTAs devem direcionar para: {context.destino_conversao}")
        if context.tipo_conteudo_uso:
            parts.append(f"Tipo uso: {context.tipo_conteudo_uso}")
        if context.plataformas:
            parts.append(f"Plataformas: {', '.join(context.plataformas)}")

        if context.inputs_extras:
            parts.append(f"\n--- DIRECIONAMENTO DO MÊS (o que fazer) ---\n{context.inputs_extras}")

        parts.append(f"\n--- RESTRIÇÕES ---\nTipos de conteúdo: {tipos_str}")

        if context.historico_temas:
            historico = "Temas JÁ USADOS (NÃO repetir):\n"
            for h in context.historico_temas:
                historico += f"- {h.get('mes', '')}: {', '.join(h.get('temas', []))}\n"
            parts.append(historico)

        return "\n".join(parts)

    async def execute(self, context: PipelineContext) -> PipelineContext:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": self._build_user_prompt(context)},
        ]

        # Tool executor como closure com acesso ao context e client
        async def tool_executor(name: str, args: dict) -> str:
            if name == "pesquisar_web":
                query = args.get("query", "")
                context.log_decision("gerador", f"pesquisando: {query[:80]}", "auto-research")
                if self._on_progress:
                    await self._on_progress(context, "gerador")
                try:
                    return await pesquisar_web(query, self.client)
                except Exception as e:
                    logger.warning("Pesquisa web falhou para '%s': %s", query[:80], e)
                    return "Pesquisa indisponível no momento. Prossiga com conhecimento existente."
            return f"Tool '{name}' não reconhecida"

        response, _ = await self.client.chat_with_tools(
            model=settings.LLM_MODEL,
            messages=messages,
            tools=GERADOR_TOOLS,
            tool_executor=tool_executor,
            temperature=0.7,
            max_tokens=12288,
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

        # Popula pesquisa a partir do output (mantém BD compatível)
        context.pesquisa = PesquisaResult(
            resumo=data.get("pesquisa_resumo", ""),
        )

        return context

    def _get_completion_reasoning(self, context: PipelineContext) -> str:
        total = len(context.conteudos)
        temas = len(context.estrategia.temas) if context.estrategia else 0
        return f"Gerados {total} conteúdos, {temas} temas, calendário completo"
