from fastapi import APIRouter

router = APIRouter(prefix="/api/config", tags=["config"])

TIPOS_CONTEUDO = [
    {
        "tipo": "video_roteiro",
        "label": "Roteiro de Vídeo",
        "descricao": "Roteiro completo com gancho, desenvolvimento e CTA",
        "campos": ["gancho", "desenvolvimento", "cta", "duracao", "timeline"],
    },
    {
        "tipo": "arte_estatica",
        "label": "Arte Estática",
        "descricao": "Título + copy persuasiva + CTA botão",
        "campos": ["titulo", "copy", "cta_botao"],
    },
    {
        "tipo": "carrossel",
        "label": "Carrossel",
        "descricao": "Capa impactante + slides informativos + CTA final",
        "campos": ["slides"],
    },
]

FRAMEWORKS = [
    {"id": "AIDA", "nome": "AIDA", "descricao": "Attention → Interest → Desire → Action"},
    {"id": "PAS", "nome": "PAS", "descricao": "Problem → Agitation → Solution"},
    {"id": "HSO", "nome": "Hook-Story-Offer", "descricao": "Gancho → História → Oferta"},
]

PILARES_EXEMPLO = [
    {"nome": "Educação", "percentual": 40, "descricao": "Conteúdo educativo sobre o nicho"},
    {"nome": "Prova Social", "percentual": 30, "descricao": "Resultados, depoimentos, casos de sucesso"},
    {"nome": "Conversão", "percentual": 20, "descricao": "CTA direto, urgência, oferta"},
    {"nome": "Humanização", "percentual": 10, "descricao": "Bastidores, equipe, valores"},
]


@router.get("/tipos-conteudo")
async def get_tipos_conteudo():
    return TIPOS_CONTEUDO


@router.get("/frameworks")
async def get_frameworks():
    return FRAMEWORKS


@router.get("/pilares-exemplo")
async def get_pilares_exemplo():
    return PILARES_EXEMPLO
