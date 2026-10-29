"""
==========================================================
  Extrator & Normalizador do LinkedIn
==========================================================
"""

from __future__ import annotations

import re
from urllib.parse import urlparse, parse_qs, urlencode
from playwright.async_api import Page
from .base import BaseExtractor


class LinkedInExtractor(BaseExtractor):
    """Extrator especializado em páginas de vagas do LinkedIn."""

    async def extrair(self, page: Page) -> str | None:
        partes: list[str] = []

        # Título
        for sel in [
            "h1.top-card-layout__title",
            "h1.t-24",
            ".job-details-jobs-unified-top-card__job-title h1",
            "h1",
        ]:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=1000):
                    partes.append(f"TÍTULO: {(await el.inner_text()).strip()}")
                    break
            except Exception:
                pass

        # Empresa
        for sel in [
            ".topcard__org-name-link",
            "a.topcard__org-name-link",
            ".job-details-jobs-unified-top-card__company-name a",
            "a[data-tracking-control-name*='company']",
        ]:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=800):
                    partes.append(f"EMPRESA: {(await el.inner_text()).strip()}")
                    break
            except Exception:
                pass

        # Localização
        for sel in [
            ".topcard__flavor--bullet",
            ".job-details-jobs-unified-top-card__bullet",
        ]:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=800):
                    partes.append(f"LOCAL: {(await el.inner_text()).strip()}")
                    break
            except Exception:
                pass

        # Data de Publicação / Tempo decorrido (CRÍTICO para filtro 24h)
        for sel in [
            ".posted-time-ago__text",
            ".job-details-jobs-unified-top-card__primary-description-container span",
            'span:has-text("há")',
            'span:has-text("ago")',
            "time",
        ]:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=800):
                    txt = (await el.inner_text()).strip()
                    if any(x in txt.lower() for x in ["há", "ago", "hora", "minut", "dia", "day", "week", "mês"]):
                        partes.append(f"PUBLICADA: {txt}")
                        break
            except Exception:
                pass

        # Abrir texto completo da descrição
        try:
            show_more = page.locator(
                'button.show-more-less-html__button--more, button:has-text("ver mais"), button:has-text("Show more")'
            ).first
            if await show_more.is_visible(timeout=1000):
                await show_more.click()
                await page.wait_for_timeout(400)
        except Exception:
            pass

        for sel in [
            ".show-more-less-html__markup",
            ".description__text",
            ".jobs-description__content",
            "article.jobs-description",
            "section.description",
        ]:
            try:
                el = page.locator(sel).first
                if await el.is_visible(timeout=1500):
                    partes.append(f"DESCRIÇÃO:\n{(await el.inner_text()).strip()}")
                    break
            except Exception:
                pass

        return "\n\n".join(partes) if partes else None


def normalizar_url_linkedin(url: str) -> tuple[str, list[str]]:
    """
    Normaliza a URL do LinkedIn para o formato público de busca e
    FORÇA o filtro de data para as ÚLTIMAS 24 HORAS (f_TPR=r86400).
    """
    ids_iniciais: list[str] = []
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    if "currentJobId" in qs:
        for jid in qs["currentJobId"]:
            if jid.isdigit():
                ids_iniciais.append(f"https://www.linkedin.com/jobs/view/{jid}/")

    new_path = parsed.path
    if "search-results" in new_path:
        new_path = "/jobs/search/"

    # Regra de negócio: últimas 24 horas garantidas
    qs["f_TPR"] = ["r86400"]

    clean_url = f"{parsed.scheme}://{parsed.netloc}{new_path}?{urlencode(qs, doseq=True)}"
    return clean_url, ids_iniciais
