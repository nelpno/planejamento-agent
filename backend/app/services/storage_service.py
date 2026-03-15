import os
from app.config import settings


def get_pdf_path(filename: str) -> str | None:
    """Get full filesystem path for a PDF file."""
    filepath = os.path.join(settings.STORAGE_PATH, filename)
    real_path = os.path.realpath(filepath)
    if not real_path.startswith(os.path.realpath(settings.STORAGE_PATH)):
        return None
    if not os.path.exists(real_path):
        return None
    return real_path
