import base64
import os
import httpx
from jinja2 import Environment, FileSystemLoader

from app.config import settings


# Jinja2 template environment
_template_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
_jinja_env = Environment(loader=FileSystemLoader(_template_dir))

# Pre-load logo as base64
_logo_path = os.path.join(_template_dir, "logopmax.png")
_logo_b64 = ""
if os.path.exists(_logo_path):
    with open(_logo_path, "rb") as f:
        _logo_b64 = f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"


def render_planejamento_html(
    cliente: dict,
    planejamento: dict,
    conteudos: list[dict],
) -> str:
    """Render planning HTML from template."""
    template = _jinja_env.get_template("planejamento.html")
    return template.render(
        cliente=cliente,
        planejamento=planejamento,
        conteudos=conteudos,
        logo_b64=_logo_b64,
    )


async def html_to_pdf(html_content: str) -> bytes:
    """Convert HTML to PDF using Gotenberg."""
    # Read CSS file
    css_path = os.path.join(_template_dir, "estilos.css")
    css_content = ""
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()

    # Inject CSS into HTML
    if css_content and "<style>" not in html_content:
        html_content = html_content.replace(
            "</head>",
            f"<style>{css_content}</style></head>"
        )

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.GOTENBERG_URL}/forms/chromium/convert/html",
            files={"files": ("index.html", html_content.encode("utf-8"), "text/html")},
            data={
                "marginTop": "0.5",
                "marginBottom": "0.5",
                "marginLeft": "0.5",
                "marginRight": "0.5",
                "paperWidth": "8.27",
                "paperHeight": "11.69",
                "printBackground": "true",
            },
        )
        response.raise_for_status()
        return response.content


async def save_pdf(pdf_bytes: bytes, filename: str) -> str:
    """Save PDF to storage and return relative URL path."""
    storage_path = settings.STORAGE_PATH
    os.makedirs(storage_path, exist_ok=True)
    filepath = os.path.join(storage_path, filename)
    with open(filepath, "wb") as f:
        f.write(pdf_bytes)
    return f"/storage/{filename}"
