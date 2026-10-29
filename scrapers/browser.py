"""
==========================================================
  Gerenciador do Navegador Playwright (Browser Manager)
==========================================================
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
)

from config.settings import (
    STATE_FILE,
    USER_AGENT,
    PAGE_LOAD_TIMEOUT_MS,
)

log = logging.getLogger("agente_vagas.scrapers")


@asynccontextmanager
async def criar_contexto_navegador() -> AsyncGenerator[BrowserContext, None]:
    """
    Cria e configura uma instância isolada do Chromium com:
      - Modo Stealth antifingerprint
      - Headers reais de usuário
      - Injeção de sessão autenticada (state.json) se existir
    """
    async with async_playwright() as pw:
        browser: Browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-infobars",
                "--window-position=0,0",
            ],
        )

        context_kwargs = {
            "user_agent": USER_AGENT,
            "locale": "pt-BR",
            "viewport": {"width": 1366, "height": 768},
            "java_script_enabled": True,
            "extra_http_headers": {
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                "Sec-Ch-Ua": '"Chromium";v="129", "Not=A?Brand";v="8"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
            },
        }

        if STATE_FILE.exists():
            log.info("🔑 Sessão salva (%s) carregada com sucesso!", STATE_FILE.name)
            context_kwargs["storage_state"] = str(STATE_FILE)

        context: BrowserContext = await browser.new_context(**context_kwargs)

        # Mascarar webdriver contra detecção de bot
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.chrome = { runtime: {} };
        """)

        try:
            yield context
        finally:
            await context.close()
            await browser.close()


async def fechar_popups(page: Page) -> None:
    """Fecha banners de cookies, modais de login e overlays."""
    seletores = [
        'button:has-text("Accept")',
        'button:has-text("Aceitar")',
        'button:has-text("Concordo")',
        'button:has-text("Aceitar cookies")',
        'button:has-text("Accept cookies")',
        'button:has-text("Aceitar todos")',
        'button[data-tracking-control-name="ga-cookie.consent.accept.v4"]',
        'button#onetrust-accept-btn-handler',
        'button.modal__dismiss',
        'button[aria-label="Dismiss"]',
        'button[aria-label="Fechar"]',
        'button[aria-label="Close"]',
        'button.artdeco-modal__dismiss',
        'button.contextual-sign-in-modal__modal-dismiss-btn',
    ]
    for sel in seletores:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=600):
                await btn.click()
                await page.wait_for_timeout(300)
        except Exception:
            pass
