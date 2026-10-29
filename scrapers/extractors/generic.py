"""
==========================================================
  Extrator Genérico / Vagas.com
==========================================================
"""

from __future__ import annotations

from playwright.async_api import Page
from .base import BaseExtractor


class GenericExtractor(BaseExtractor):
    """Extrator com seletores genéricos e para Vagas.com.br."""

    async def extrair(self, page: Page) -> str | None:
        partes: list[str] = []

        # Título
        for sel in ["h1.job-title", "h1.cargo", "h1"]:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=1000):
                    partes.append(f"TÍTULO: {(await el.inner_text()).strip()}")
                    break
            except Exception:
                pass

        # Conteúdo
        for sel in [".job-tab-content", ".job-description", ".informacoes-vaga", "article", "main"]:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=1500):
                    partes.append((await el.inner_text()).strip())
                    break
            except Exception:
                pass

        if not partes:
            try:
                texto_body = await page.inner_text("body")
                return texto_body.strip() if texto_body else None
            except Exception:
                return None

        return "\n\n".join(partes)
