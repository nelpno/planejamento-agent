import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.providers.openrouter_client import OpenRouterClient
from app.schemas.cliente import ClienteCreate, ClienteUpdate, ClienteResponse, KickOffInput
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
  "instrucoes": "Instruções especiais baseadas no kick-off (PUV, sazonalidade, estratégias que funcionam, etc.)"
}

Regras:
- Pilares devem somar 100%
- Baseie o tom de voz na PUV e na descrição da empresa
- Extraia concorrentes mencionados
- As dores devem vir do público-alvo e dos objetivos
- Tipos de conteúdo devem ser adequados ao nicho
- Instruções devem incluir PUV, sazonalidade e estratégias vencedoras mencionadas"""


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
    }


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
