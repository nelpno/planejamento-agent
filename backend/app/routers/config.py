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


FOCOS = [
    {"id": "geracao_leads", "label": "Geração de Leads", "descricao": "Captar contatos qualificados (advocacia, clínicas, consultoria)", "icon": "users"},
    {"id": "vendas_ecommerce", "label": "Vendas no Site / E-commerce", "descricao": "Direcionar para compra online (Shopify, Mercado Livre)", "icon": "shopping-cart"},
    {"id": "crescimento_organico", "label": "Crescimento Orgânico", "descricao": "Aumentar seguidores, engajamento e alcance", "icon": "trending-up"},
    {"id": "branding", "label": "Branding / Posicionamento", "descricao": "Fortalecer marca e autoridade no nicho", "icon": "award"},
    {"id": "lancamento", "label": "Lançamento", "descricao": "Lançar produto, serviço ou evento novo", "icon": "rocket"},
    {"id": "retencao", "label": "Retenção / Relacionamento", "descricao": "Fidelizar e engajar clientes existentes", "icon": "heart"},
]

DESTINOS = [
    {"id": "whatsapp", "label": "WhatsApp", "cta_exemplo": "Fale conosco no WhatsApp"},
    {"id": "site", "label": "Site / Landing Page", "cta_exemplo": "Acesse o link na bio"},
    {"id": "dm_instagram", "label": "DM Instagram", "cta_exemplo": "Comente EU QUERO"},
    {"id": "loja_online", "label": "Loja Online", "cta_exemplo": "Compre agora / Link na bio"},
    {"id": "agendamento", "label": "Agendamento", "cta_exemplo": "Agende sua consulta"},
    {"id": "telefone", "label": "Telefone", "cta_exemplo": "Ligue agora"},
]

TIPOS_USO = [
    {"id": "organico", "label": "Orgânico", "descricao": "Conteúdo para feed/stories/reels orgânicos"},
    {"id": "pago", "label": "Tráfego Pago (Ads)", "descricao": "Criativos para campanhas pagas Meta/Google"},
    {"id": "ambos", "label": "Ambos", "descricao": "Mix de orgânico e criativos para ads"},
]

PLATAFORMAS = [
    {"id": "instagram", "label": "Instagram"},
    {"id": "tiktok", "label": "TikTok"},
    {"id": "youtube", "label": "YouTube"},
    {"id": "linkedin", "label": "LinkedIn"},
    {"id": "facebook", "label": "Facebook"},
]


@router.get("/focos")
async def get_focos():
    return FOCOS


@router.get("/destinos")
async def get_destinos():
    return DESTINOS


@router.get("/tipos-uso")
async def get_tipos_uso():
    return TIPOS_USO


@router.get("/plataformas")
async def get_plataformas():
    return PLATAFORMAS
