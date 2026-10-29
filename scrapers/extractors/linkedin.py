"""
==========================================================
  Extrator & Normalizador do LinkedIn
==========================================================
"""

from __future__ import annotations

from urllib.parse import parse_qs, urlencode, urlparse

from playwright.async_api import Page

from .base import BaseExtractor


class LinkedInExtractor(BaseExtractor):
    """Extrator especializado em páginas de vagas do LinkedIn."""

    async def _buscar_texto(
        self,
        page: Page,
        seletores: list[str],
        timeout: int = 800,
    ) -> str | None:
        """Retorna o texto do primeiro seletor visível."""

        for seletor in seletores:
            try:
                elemento = page.locator(seletor).first

                if await elemento.is_visible(timeout=timeout):
                    texto = (await elemento.inner_text()).strip()

                    if texto:
                        return texto

            except Exception:
                continue

        return None

    async def _extrair_titulo(self, page: Page) -> str | None:
        return await self._buscar_texto(
            page,
            [
                "h1.top-card-layout__title",
                "h1.t-24",
                ".job-details-jobs-unified-top-card__job-title h1",
                "h1",
            ],
            timeout=1000,
        )

    async def _extrair_empresa(self, page: Page) -> str | None:
        return await self._buscar_texto(
            page,
            [
                ".topcard__org-name-link",
                "a.topcard__org-name-link",
                ".job-details-jobs-unified-top-card__company-name a",
                "a[data-tracking-control-name*='company']",
            ],
        )

    async def _extrair_localizacao(self, page: Page) -> str | None:
        return await self._buscar_texto(
            page,
            [
                ".topcard__flavor--bullet",
                ".job-details-jobs-unified-top-card__bullet",
            ],
        )

    async def _extrair_publicacao(self, page: Page) -> str | None:
        seletores = [
            ".posted-time-ago__text",
            (
                ".job-details-jobs-unified-top-card__"
                "primary-description-container span"
            ),
            'span:has-text("há")',
            'span:has-text("ago")',
            "time",
        ]

        termos_validos = [
            "há",
            "ago",
            "hora",
            "hour",
            "minut",
            "dia",
            "day",
            "week",
            "semana",
            "mês",
            "month",
        ]

        for seletor in seletores:
            texto = await self._buscar_texto(
                page,
                [seletor],
            )

            if texto and any(
                termo in texto.lower()
                for termo in termos_validos
            ):
                return texto

        return None

    async def _abrir_descricao_completa(self, page: Page) -> None:
        seletor = (
            'button.show-more-less-html__button--more, '
            'button:has-text("ver mais"), '
            'button:has-text("Show more")'
        )

        try:
            botao = page.locator(seletor).first

            if await botao.is_visible(timeout=1000):
                await botao.click()
                await page.wait_for_timeout(400)

        except Exception:
            pass

    async def _extrair_descricao(self, page: Page) -> str | None:
        await self._abrir_descricao_completa(page)

        return await self._buscar_texto(
            page,
            [
                ".show-more-less-html__markup",
                ".description__text",
                ".jobs-description__content",
                "article.jobs-description",
                "section.description",
            ],
            timeout=1500,
        )

    async def extrair(self, page: Page) -> str | None:
        """Extrai e organiza as informações da vaga."""

        dados = [
            ("TÍTULO", await self._extrair_titulo(page)),
            ("EMPRESA", await self._extrair_empresa(page)),
            ("LOCAL", await self._extrair_localizacao(page)),
            ("PUBLICADA", await self._extrair_publicacao(page)),
            ("DESCRIÇÃO", await self._extrair_descricao(page)),
        ]

        partes = [
            f"{campo}:\n{valor}"
            if campo == "DESCRIÇÃO"
            else f"{campo}: {valor}"
            for campo, valor in dados
            if valor
        ]

        return "\n\n".join(partes) if partes else None


def normalizar_url_linkedin(url: str) -> tuple[str, list[str]]:
    """
    Normaliza a URL do LinkedIn para o formato público de busca e
    força o filtro de data para as últimas 24 horas (f_TPR=r86400).
    """

    ids_iniciais: list[str] = []

    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    if "currentJobId" in qs:
        for job_id in qs["currentJobId"]:
            if job_id.isdigit():
                ids_iniciais.append(
                    f"https://www.linkedin.com/jobs/view/{job_id}/"
                )

    novo_caminho = parsed.path

    if "search-results" in novo_caminho:
        novo_caminho = "/jobs/search/"

    # Regra de negócio: últimas 24 horas garantidas
    qs["f_TPR"] = ["r86400"]

    clean_url = (
        f"{parsed.scheme}://{parsed.netloc}"
        f"{novo_caminho}?{urlencode(qs, doseq=True)}"
    )

    return clean_url, ids_iniciais