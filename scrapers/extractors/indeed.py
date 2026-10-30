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
        for sel in [
            "h1.jobsearch-JobInfoHeader-title",
            '[data-testid="jobsearch-JobInfoHeader-title"]',
            'h1[class*="JobTitle"]',
            "h1",
        ]:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=1000):
                    partes.append(f"TÍTULO: {(await el.inner_text()).strip()}")
                    break
            except Exception:
                pass

        # Descrição
        for sel in [
            "#jobDescriptionText",
            '[data-testid="jobsearch-JobComponent-description"]',
            ".jobsearch-JobComponent-description",
            '[class*="jobDescription"]',
        ]:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=1500):
                    partes.append(f"DESCRIÇÃO:\n{(await el.inner_text()).strip()}")
                    break
            except Exception:
                pass

        if partes:
            return "\n\n".join(partes)

        # O Indeed altera os seletores e, em alguns casos, entrega o conteúdo
        # renderizado sem as classes antigas. Evita perder a vaga nesse caso,
        # mas rejeita páginas de bloqueio/erro claramente identificadas.
        try:
            corpo = (await page.locator("body").inner_text()).strip()
            corpo_lower = corpo.lower()
            bloqueios = (
                "não foi possível encontrar",
                "we couldn't find",
                "captcha",
                "access denied",
                "acesso negado",
            )
            if len(corpo) >= 300 and not any(t in corpo_lower for t in bloqueios):
                return f"CONTEÚDO DA VAGA:\n{corpo}"
        except Exception:
            pass

        return None
