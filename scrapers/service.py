"""
==========================================================
  Serviço Unificado de Raspagem de Vagas
==========================================================
"""

from __future__ import annotations

import logging
import random
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from config.settings import (
    PORTAL_LINKEDIN,
    PORTAL_GUPY,
    PORTAL_INDEED,
    PORTAL_INFOJOBS,
    PORTAL_CATHO,
    PORTAL_VAGAS_COM,
    PAGE_LOAD_TIMEOUT_MS,
)
from core.models import VagaDescoberta, DetalhesVaga
from .browser import fechar_popups
from .extractors import (
    LinkedInExtractor,
    GupyExtractor,
    IndeedExtractor,
    GenericExtractor,
)

log = logging.getLogger("agente_vagas.scrapers")

_EXTRATORES = {
    PORTAL_LINKEDIN: LinkedInExtractor(),
    PORTAL_GUPY: GupyExtractor(),
    PORTAL_INDEED: IndeedExtractor(),
    PORTAL_INFOJOBS: IndeedExtractor(),
    PORTAL_CATHO: GenericExtractor(),
    PORTAL_VAGAS_COM: GenericExtractor(),
}
_EXTRATOR_DEFAULT = GenericExtractor()


async def raspar_detalhe_vaga(page: Page, vaga: VagaDescoberta) -> DetalhesVaga | None:
    """
    Navega para a página individual da vaga e extrai seu conteúdo completo.
    """
    log.info("   🌐 Raspando detalhe: %s", vaga.url)

    try:
        await page.goto(
            vaga.url,
            timeout=PAGE_LOAD_TIMEOUT_MS,
            wait_until="domcontentloaded",
        )
        await page.wait_for_timeout(random.randint(1800, 2800))
        await fechar_popups(page)
    except PlaywrightTimeout:
        log.warning("      ⚠ Timeout ao carregar: %s", vaga.url)
        return None
    except Exception as exc:
        log.error("      ✖ Erro ao navegar para %s: %s", vaga.url, exc)
        return None

    extrator = _EXTRATORES.get(vaga.portal, _EXTRATOR_DEFAULT)
    texto = await extrator.extrair(page)

    if not texto or len(texto.strip()) < 50:
        log.warning("      ⚠ Conteúdo insuficiente extraído (%s) — ignorando", vaga.url)
        return None

    log.info("      ✔ %d caracteres extraídos com sucesso!", len(texto))
    return DetalhesVaga(
        url=vaga.url,
        portal=vaga.portal,
        texto_completo=texto,
    )
