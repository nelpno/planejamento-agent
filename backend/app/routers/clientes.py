import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.providers.openrouter_client import OpenRouterClient
from app.schemas.cliente import ClienteCreate, ClienteUpdate, ClienteResponse, KickOffInput, DiscoverInput
from app.services import cliente_service
from app.utils.json_parser import parse_json_safe as _parse_json_safe

router = APIRouter(prefix="/api/clientes", tags=["clientes"])

KICKOFF_SYSTEM_PROMPT = """Você é um especialista em marketing digital. Analise as respostas do Kick Off de um novo cliente e extraia um perfil estruturado para planejamento de conteúdo.

Retorne APENAS JSON válido com esta estrutura:
{
  "publico_alvo": {
    "descricao": "Descrição detalhada do público-alvo principal",
    "faixa_etaria": "25-55",
    "localizacao": "Região/cidade",
    "dores": ["dor 1", "dor 2", "dor 3"]
  },
  "tom_de_voz": {
    "estilo": "Ex: Profissional e acolhedor",
    "palavras_chave": ["palavra1", "palavra2"],
    "evitar": ["termo1", "termo2"]
  },
  "pilares": [
    {"nome": "Nome do Pilar", "percentual": 40, "descricao": "Descrição"},
    {"nome": "Nome do Pilar", "percentual": 30, "descricao": "Descrição"},
    {"nome": "Nome do Pilar", "percentual": 20, "descricao": "Descrição"},
    {"nome": "Nome do Pilar", "percentual": 10, "descricao": "Descrição"}
  ],
  "tipos_conteudo": [
    {"tipo": "video_roteiro", "quantidade": 4, "formato": "Reels/Feed", "duracao": "60-90s"},
    {"tipo": "arte_estatica", "quantidade": 4, "formato": "Feed"},
    {"tipo": "carrossel", "quantidade": 2, "slides": "5-7"}
  ],
  "concorrentes": [
    {"nome": "Nome", "instagram": "@handle", "site": "url"}
  ],
  "redes_sociais": {"instagram": "@handle", "site": "url"},
  "nome_empresa": "Nome da empresa extraído do texto",
  "nicho": "Nicho/segmento de mercado da empresa",
  "instrucoes": "Instruções especiais baseadas no kick-off (PUV, sazonalidade, estratégias que funcionam, etc.)",
  "foco_padrao": "geracao_leads ou vendas_ecommerce ou crescimento_organico ou branding ou lancamento ou retencao",
  "destino_padrao": "whatsapp ou site ou dm_instagram ou loja_online ou agendamento ou telefone",
  "tipo_uso_padrao": "organico ou pago ou ambos",
  "plataformas_padrao": ["instagram", "tiktok", "...outras relevantes"]
}

Regras:
- Pilares devem somar 100%
- Baseie o tom de voz na PUV e na descrição da empresa
- Extraia concorrentes mencionados
- As dores devem vir do público-alvo e dos objetivos
- Tipos de conteúdo devem ser adequados ao nicho
- Instruções devem incluir PUV, sazonalidade e estratégias vencedoras mencionadas
- foco_padrao: escolha UM valor entre geracao_leads, vendas_ecommerce, crescimento_organico, branding, lancamento, retencao
- destino_padrao: escolha UM valor entre whatsapp, site, dm_instagram, loja_online, agendamento, telefone
- tipo_uso_padrao: escolha UM valor entre organico, pago, ambos
- plataformas_padrao: lista de plataformas relevantes (instagram, tiktok, youtube, linkedin, facebook)"""


@router.post("/kick-off/preview")
async def preview_kickoff(data: KickOffInput):
    """Processa respostas do Kick Off com IA e retorna preview do perfil (sem salvar)."""
    client = OpenRouterClient()
    try:
        response = await client.chat(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": KICKOFF_SYSTEM_PROMPT},
                {"role": "user", "content": data.kickoff_text},
            ],
            temperature=0.3,
            max_tokens=4096,
            response_format={"type": "json_object"},
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("OpenRouter call failed: %s", e)
        raise HTTPException(status_code=502, detail="Serviço de IA temporariamente indisponível. Tente novamente.")
    finally:
        await client.close()

    try:
        perfil = _parse_json_safe(response)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=f"Erro ao processar resposta da IA: {str(e)[:200]}")

    # Retorna preview completo para o frontend — operador confirma antes de salvar
    return {
        "nome_empresa": data.nome_empresa or perfil.get("nome_empresa", ""),
        "nicho": data.nicho or perfil.get("nicho", ""),
        "publico_alvo": perfil.get("publico_alvo"),
        "tom_de_voz": perfil.get("tom_de_voz"),
        "pilares": perfil.get("pilares"),
        "tipos_conteudo": perfil.get("tipos_conteudo"),
        "concorrentes": perfil.get("concorrentes"),
        "redes_sociais": perfil.get("redes_sociais"),
        "instrucoes": perfil.get("instrucoes"),
        "foco_padrao": perfil.get("foco_padrao"),
        "destino_padrao": perfil.get("destino_padrao"),
        "tipo_uso_padrao": perfil.get("tipo_uso_padrao"),
        "plataformas_padrao": perfil.get("plataformas_padrao"),
    }


DISCOVER_SYSTEM_PROMPT = """Você é um pesquisador de marketing digital. Pesquise na internet sobre a empresa abaixo e extraia um perfil completo para planejamento de conteúdo.

PESQUISE os seguintes dados na web:
- Site da empresa: analise todas as páginas, serviços, sobre, depoimentos
- Instagram: analise o tipo de conteúdo publicado, frequência, engajamento, tom de voz
- Concorrentes: identifique 3-5 concorrentes do mesmo nicho

Retorne APENAS JSON válido com esta estrutura:
{
  "nome_empresa": "Nome da empresa extraído",
  "nicho": "Nicho/segmento de mercado",
  "publico_alvo": {
    "descricao": "Descrição detalhada do público-alvo",
    "faixa_etaria": "25-55",
    "localizacao": "Região",
    "dores": ["dor 1", "dor 2"]
  },
  "tom_de_voz": {
    "estilo": "Tom identificado no Instagram/site",
    "palavras_chave": ["palavra1", "palavra2"],
    "evitar": ["termo1"]
  },
  "pilares": [
    {"nome": "Pilar", "percentual": 40, "descricao": "Baseado no conteúdo atual"}
  ],
  "tipos_conteudo": [
    {"tipo": "video_roteiro", "quantidade": 4, "formato": "Reels/Feed"}
  ],
  "concorrentes": [
    {"nome": "Nome", "instagram": "@handle", "site": "url"}
  ],
  "redes_sociais": {"instagram": "@handle", "site": "url"},
  "instrucoes": "Insights encontrados na pesquisa: PUV, diferenciais, estratégia atual",
  "foco_padrao": "geracao_leads ou vendas_ecommerce ou crescimento_organico ou branding ou lancamento ou retencao",
  "destino_padrao": "whatsapp ou site ou dm_instagram ou loja_online ou agendamento ou telefone",
  "tipo_uso_padrao": "organico ou pago ou ambos",
  "plataformas_padrao": ["instagram", "tiktok", "...outras relevantes"]
}

Pilares devem somar 100%. Baseie tudo em dados REAIS encontrados na pesquisa.
- foco_padrao: escolha UM valor entre geracao_leads, vendas_ecommerce, crescimento_organico, branding, lancamento, retencao
- destino_padrao: escolha UM valor entre whatsapp, site, dm_instagram, loja_online, agendamento, telefone
- tipo_uso_padrao: escolha UM valor entre organico, pago, ambos
- plataformas_padrao: lista de plataformas relevantes (instagram, tiktok, youtube, linkedin, facebook)"""


@router.post("/kick-off/discover")
async def discover_kickoff(data: DiscoverInput):
    """Pesquisa automática: IA busca na web e gera perfil do cliente."""
    if not data.instagram and not data.site:
        raise HTTPException(status_code=400, detail="Informe pelo menos Instagram ou Site")

    client = OpenRouterClient()
    try:
        user_prompt = "Pesquise sobre esta empresa:\n"
        if data.instagram:
            user_prompt += f"Instagram: {data.instagram}\n"
        if data.site:
            user_prompt += f"Site: {data.site}\n"
        if data.notas:
            user_prompt += f"\nInformações adicionais: {data.notas}\n"

        response = await client.chat(
            model=settings.LLM_MODEL_SEARCH,
            messages=[
                {"role": "system", "content": DISCOVER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=4096,
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error("Discover failed: %s", e)
        raise HTTPException(status_code=502, detail="Serviço de pesquisa temporariamente indisponível")
    finally:
        await client.close()

    try:
        perfil = _parse_json_safe(response)
    except ValueError:
        raise HTTPException(status_code=502, detail="Não foi possível extrair dados da pesquisa. Tente novamente.")

    # Ensure redes_sociais has the input values
    redes = perfil.get("redes_sociais", {})
    if data.instagram and not redes.get("instagram"):
        redes["instagram"] = data.instagram
    if data.site and not redes.get("site"):
        redes["site"] = data.site
    perfil["redes_sociais"] = redes

    # Garantir que os campos de defaults existam no retorno
    for key in ("foco_padrao", "destino_padrao", "tipo_uso_padrao", "plataformas_padrao"):
        perfil.setdefault(key, None)

    return perfil


@router.post("", response_model=ClienteResponse, status_code=201)
async def create_cliente(
    data: ClienteCreate,
    session: AsyncSession = Depends(get_session),
):
    cliente = await cliente_service.create_cliente(session, data.model_dump(exclude_none=True))
    return cliente


@router.get("", response_model=list[ClienteResponse])
async def list_clientes(session: AsyncSession = Depends(get_session)):
    return await cliente_service.get_clientes(session)


@router.get("/{cliente_id}", response_model=ClienteResponse)
async def get_cliente(
    cliente_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    cliente = await cliente_service.get_cliente(session, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente


@router.put("/{cliente_id}", response_model=ClienteResponse)
async def update_cliente(
    cliente_id: uuid.UUID,
    data: ClienteUpdate,
    session: AsyncSession = Depends(get_session),
):
    cliente = await cliente_service.update_cliente(
        session, cliente_id, data.model_dump(exclude_none=True)
    )
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente


@router.delete("/{cliente_id}", status_code=204)
async def delete_cliente(
    cliente_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    deleted = await cliente_service.delete_cliente(session, cliente_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
