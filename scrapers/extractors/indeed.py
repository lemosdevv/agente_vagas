"""
==========================================================
  Extrator Indeed & InfoJobs
==========================================================
"""

from __future__ import annotations

from playwright.async_api import Page
from .base import BaseExtractor


class IndeedExtractor(BaseExtractor):
    """Extrator especializado em Indeed e InfoJobs."""

    async def extrair(self, page: Page) -> str | None:
        partes: list[str] = []

        # Título
        for sel in ["h1.jobsearch-JobInfoHeader-title", 'h1[class*="JobTitle"]', "h1"]:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=1000):
                    partes.append(f"TÍTULO: {(await el.inner_text()).strip()}")
                    break
            except Exception:
                pass

        # Descrição
        for sel in ["#jobDescriptionText", ".jobsearch-JobComponent-description", '[class*="jobDescription"]']:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=1500):
                    partes.append(f"DESCRIÇÃO:\n{(await el.inner_text()).strip()}")
                    break
            except Exception:
                pass

        return "\n\n".join(partes) if partes else None
