"""
==========================================================
  Módulo de Descoberta de Vagas do Dia (Discovery)
==========================================================
"""

from __future__ import annotations

import asyncio
import logging
import random
import re
from urllib.parse import urlparse, parse_qs, urlencode, urljoin
from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from config.settings import (
    PORTAL_LINKEDIN,
    PORTAL_GUPY,
    PORTAL_INDEED,
    PORTAL_INFOJOBS,
    PORTAL_CATHO,
    PORTAL_VAGAS_COM,
    PORTAL_GENERICO,
    PAGE_LOAD_TIMEOUT_MS,
    SCROLL_ROUNDS,
    USER_AGENT,
)
from core.models import VagaDescoberta
from .browser import fechar_popups
from .extractors.linkedin import normalizar_url_linkedin

log = logging.getLogger("agente_vagas.discovery")


def detectar_portal(url: str) -> str:
    """Identifica o portal de emprego com base no domínio da URL."""
    domain = urlparse(url).netloc.lower()
    if "linkedin.com" in domain:
        return PORTAL_LINKEDIN
    if "gupy.io" in domain:
        return PORTAL_GUPY
    if "indeed.com" in domain:
        return PORTAL_INDEED
    if "infojobs.com" in domain:
        return PORTAL_INFOJOBS
    if "catho.com" in domain:
        return PORTAL_CATHO
    if "vagas.com" in domain:
        return PORTAL_VAGAS_COM
    return PORTAL_GENERICO


async def scroll_incremental(page: Page, rounds: int = SCROLL_ROUNDS) -> None:
    """Scroll progressivo para carregar vagas dinâmicas na página."""
    for _ in range(rounds):
        await page.evaluate("window.scrollBy(0, window.innerHeight * 1.5)")
        await page.wait_for_timeout(random.randint(1000, 2000))

        for texto_btn in ["See more jobs", "Ver mais vagas", "Show more", "Mostrar mais"]:
            try:
                btn = page.locator(f'button:has-text("{texto_btn}")').first
                if await btn.is_visible(timeout=400):
                    await btn.click()
                    await page.wait_for_timeout(1200)
            except Exception:
                pass


async def descobrir_vagas(page: Page, url_busca: str) -> list[VagaDescoberta]:
    """
    Navega para a URL de busca aplicando o filtro das últimas 24h
    e coleta TODAS as vagas encontradas sem limite.
    """
    portal = detectar_portal(url_busca)
    url_navegacao = url_busca

    if portal == PORTAL_LINKEDIN:
        url_navegacao, _ = normalizar_url_linkedin(url_busca)

    log.info("🔍 Varrendo vagas DO DIA em [%s]: %s", portal.upper(), url_navegacao)

    try:
        log.info("   ⏳ Iniciando carregamento da página...")
        await page.goto(
            url_navegacao,
            timeout=PAGE_LOAD_TIMEOUT_MS,
            wait_until="domcontentloaded",
        )
        log.info("   ✔ Página carregada. URL atual: %s", page.url)
        await page.wait_for_timeout(2500)
        await fechar_popups(page)
    except PlaywrightTimeout:
        log.error("   ✖ Timeout ao carregar página de busca: %s", url_navegacao)
        return []
    except Exception as exc:
        log.error(
            "   ✖ Erro ao navegar para %s: %s | URL observada: %s",
            url_navegacao,
            exc,
            page.url,
        )
        return []

    descobridores = {
        PORTAL_LINKEDIN: _descobrir_linkedin,
        PORTAL_GUPY: _descobrir_gupy,
        PORTAL_INDEED: _descobrir_indeed,
        PORTAL_INFOJOBS: _descobrir_indeed,
        PORTAL_CATHO: _descobrir_generico,
        PORTAL_VAGAS_COM: _descobrir_vagas_com,
    }
    func = descobridores.get(portal, _descobrir_generico)
    urls_encontradas = await func(page, url_navegacao)

    # Deduplicação completa sem limite
    urls_unicas = list(dict.fromkeys(urls_encontradas))

    log.info(
        "   📋 %d vaga(s) do dia capturada(s) nesta busca (varredura ilimitada)",
        len(urls_unicas),
    )

    return [
        VagaDescoberta(url=u, portal=portal, url_busca_origem=url_navegacao)
        for u in urls_unicas
    ]


async def _descobrir_linkedin(page: Page, url_busca: str) -> list[str]:
    """Extrai links de vagas do LinkedIn combinando DOM e paginação via API pública."""
    url_normalizada, ids_encontrados = normalizar_url_linkedin(url_busca)
    cleaned: list[str] = list(ids_encontrados)
    seen_ids: set[str] = {
        m.group(1) for u in cleaned if (m := re.search(r"/jobs/view/(\d+)", u))
    }

    await scroll_incremental(page, rounds=SCROLL_ROUNDS)

    seletores = [
        'a[href*="/jobs/view/"]',
        'a.base-card__full-link',
        'a.job-card-list__title',
        'a.job-card-container__link',
        'a[data-tracking-control-name*="job-search-card"]',
        'ul.jobs-search__results-list li a',
    ]

    for sel in seletores:
        try:
            hrefs: list[str] = await page.eval_on_selector_all(
                sel, "els => els.map(el => el.href)"
            )
            for href in hrefs:
                match = re.search(r"/jobs/view/(\d+)", href)
                if match and match.group(1) not in seen_ids:
                    seen_ids.add(match.group(1))
                    cleaned.append(f"https://www.linkedin.com/jobs/view/{match.group(1)}/")
        except Exception:
            pass

    # Regex em todo o HTML
    try:
        html = await page.content()
        for pat in [r"/jobs/view/(\d+)", r"urn:li:jobPosting:(\d+)", r"jobPosting%3A(\d+)"]:
            for jid in re.findall(pat, html):
                if jid not in seen_ids:
                    seen_ids.add(jid)
                    cleaned.append(f"https://www.linkedin.com/jobs/view/{jid}/")
    except Exception:
        pass

    # Complementar com paginação profunda via API (24h)
    api_urls = await _paginar_linkedin_api(page, url_busca)
    for u in api_urls:
        if u not in cleaned:
            cleaned.append(u)

    return cleaned


async def _paginar_linkedin_api(page: Page, url_busca: str) -> list[str]:
    """Pagina os endpoints públicos de vagas do LinkedIn de 25 em 25."""
    todos_ids: list[str] = []
    try:
        parsed = urlparse(url_busca)
        params = parse_qs(parsed.query)

        params.pop("currentJobId", None)
        params.pop("referralSearchId", None)
        params.pop("origin", None)
        params["f_TPR"] = ["r86400"]

        start = 0
        while True:
            params["start"] = [str(start)]
            query_str = urlencode(params, doseq=True)
            api_url = (
                f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
                f"?{query_str}"
            )

            response = await page.request.get(
                api_url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                    "Referer": "https://www.linkedin.com/jobs/search",
                },
            )

            if response.status != 200:
                break

            html = await response.text()
            matches = re.findall(r"/jobs/view/(\d+)", html)
            if not matches:
                matches = re.findall(r"urn:li:jobPosting:(\d+)", html)

            if not matches:
                break

            novos = [m for m in matches if m not in todos_ids]
            if not novos:
                break

            todos_ids.extend(novos)
            start += 25
            await asyncio.sleep(0.4)

            # Trava de segurança para buscas astronômicas
            if start >= 300:
                break

        if todos_ids:
            log.info("   ✔ Paginação da API capturou %d vagas recentes!", len(todos_ids))
            return [f"https://www.linkedin.com/jobs/view/{jid}/" for jid in todos_ids]
    except Exception as exc:
        log.warning("   ⚠ Erro na paginação da API: %s", exc)

    return []


async def _descobrir_gupy(page: Page, url_busca: str) -> list[str]:
    """Extrai links de vagas de portais Gupy."""
    await scroll_incremental(page, rounds=SCROLL_ROUNDS)
    hrefs: list[str] = await page.eval_on_selector_all(
        'a[href*="/job/"], a[href*="/vaga/"]',
        "els => [...new Set(els.map(el => el.href))]",
    )
    if not hrefs:
        hrefs = await page.eval_on_selector_all(
            '[class*="job"] a, [class*="Job"] a, [class*="vaga"] a',
            "els => [...new Set(els.map(el => el.href))]",
        )
    return hrefs


async def _descobrir_indeed(page: Page, url_busca: str) -> list[str]:
    """Extrai links de vagas do Indeed."""
    hrefs: list[str] = await page.eval_on_selector_all(
        'a[href*="/rc/clk/"], a[href*="/viewjob"], a.jcs-JobTitle, a[data-jk], h2.jobTitle a',
        "els => els.map(el => el.href)",
    )
    base = urlparse(url_busca)
    base_url = f"{base.scheme}://{base.netloc}"
    return list(dict.fromkeys(urljoin(base_url, h) for h in hrefs))


async def _descobrir_vagas_com(page: Page, url_busca: str) -> list[str]:
    """Extrai links de vagas do Vagas.com.br."""
    hrefs: list[str] = await page.eval_on_selector_all(
        'a[href*="/vagas/v"], a.link-detalhes-vaga, a[class*="link-vaga"]',
        "els => els.map(el => el.href)",
    )
    base = urlparse(url_busca)
    base_url = f"{base.scheme}://{base.netloc}"
    return list(dict.fromkeys(urljoin(base_url, h) for h in hrefs))


async def _descobrir_generico(page: Page, url_busca: str) -> list[str]:
    """Fallback heurístico para portais diversos."""
    await scroll_incremental(page, rounds=3)
    all_links: list[dict] = await page.eval_on_selector_all(
        "a[href]",
        "els => els.map(el => ({ href: el.href, text: (el.innerText || '').toLowerCase() }))",
    )
    keywords = ["vaga", "job", "career", "oportunidade", "/view/", "/detail/"]
    base_domain = urlparse(url_busca).netloc.lower()
    job_urls: list[str] = []

    for link in all_links:
        href = link.get("href", "")
        text = link.get("text", "")
        if base_domain not in urlparse(href).netloc.lower():
            continue
        if any(x in href.lower() for x in ["/login", "/signup", "/register", "#"]):
            continue
        combined = f"{href} {text}".lower()
        if any(kw in combined for kw in keywords):
            if href not in job_urls:
                job_urls.append(href)

    return job_urls
