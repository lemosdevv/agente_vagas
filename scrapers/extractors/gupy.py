"""
==========================================================
  Extrator de Vagas Gupy
==========================================================
"""

from __future__ import annotations

from playwright.async_api import Page
from .base import BaseExtractor


class GupyExtractor(BaseExtractor):
    """Extrator especializado em portais de vagas da Gupy."""

    async def extrair(self, page: Page) -> str | None:
        partes: list[str] = []

        # Título
        for sel in ["h1", '[class*="title" i]', '[data-testid*="title"]']:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=1000):
                    partes.append(f"TÍTULO: {(await el.inner_text()).strip()}")
                    break
            except Exception:
                pass

        # Conteúdo da descrição
        for sel in ['[class*="description" i]', '[data-testid*="description"]', "article", "main"]:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=1500):
                    partes.append(f"DESCRIÇÃO:\n{(await el.inner_text()).strip()}")
                    break
            except Exception:
                pass

        return "\n\n".join(partes) if partes else None
