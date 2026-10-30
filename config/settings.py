"""
==========================================================
  Configurações Centrais do Projeto (Settings)
==========================================================
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final
from dotenv import load_dotenv

# Diretórios base
BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent
CONFIG_DIR: Final[Path] = BASE_DIR / "config"
TEMPLATES_DIR: Final[Path] = BASE_DIR / "notifier" / "templates"
SCREENSHOTS_DIR: Final[Path] = BASE_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

STATE_FILE: Final[Path] = BASE_DIR / "state.json"
CURRICULO_FILE: Final[Path] = BASE_DIR / "curriculo.txt"
URLS_FILE: Final[Path] = BASE_DIR / "urls_alvo.txt"
ENV_FILE: Final[Path] = BASE_DIR / ".env"

# Carregar variáveis do .env
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

# Constantes de Triagem & IA
DESCARTE_SENTINELA: Final[str] = "DESCARTAR_VAGA"
GEMINI_MODEL: Final[str] = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

# Constantes de Rede e SMTP
SMTP_HOST: Final[str] = "smtp.gmail.com"
SMTP_PORT: Final[int] = 465
PAGE_LOAD_TIMEOUT_MS: Final[int] = 30_000

# Parâmetros de Scraping
DELAY_ENTRE_PAGINAS: Final[tuple[float, float]] = (1.5, 3.5)
SCROLL_ROUNDS: Final[int] = 10
MAX_VAGAS_POR_BUSCA: Final[int | None] = None  # Sem limite de vagas

USER_AGENT: Final[str] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/129.0.0.0 Safari/537.36"
)

# Portais
PORTAL_LINKEDIN: Final[str] = "linkedin"
PORTAL_GUPY: Final[str] = "gupy"
PORTAL_INDEED: Final[str] = "indeed"
PORTAL_INFOJOBS: Final[str] = "infojobs"
PORTAL_CATHO: Final[str] = "catho"
PORTAL_VAGAS_COM: Final[str] = "vagas.com"
PORTAL_GENERICO: Final[str] = "generico"


@dataclass(frozen=True)
class AppConfig:
    """Configurações validadas da aplicação."""
    email: str
    senha_app: str
    gemini_api_key: str
    curriculo: str
    urls_busca: list[str] = field(default_factory=list)


def carregar_configuracao() -> AppConfig:
    """Valida e carrega as credenciais e arquivos de entrada."""
    email = os.getenv("MEU_EMAIL", "").strip()
    senha = os.getenv("SENHA_APP", "").strip()
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not all([email, senha, api_key]):
        sys.exit(
            "[ERRO] Variáveis MEU_EMAIL, SENHA_APP e GEMINI_API_KEY "
            "devem estar preenchidas no .env"
        )

    if not CURRICULO_FILE.exists():
        sys.exit(f"[ERRO] Arquivo curriculo.txt não encontrado em: {CURRICULO_FILE}")
    curriculo = CURRICULO_FILE.read_text(encoding="utf-8")

    if not URLS_FILE.exists():
        sys.exit(f"[ERRO] Arquivo urls_alvo.txt não encontrado em: {URLS_FILE}")

    urls: list[str] = []
    for linha in URLS_FILE.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#"):
            urls.append(linha)

    if not urls:
        sys.exit("[ERRO] Nenhuma URL válida encontrada em urls_alvo.txt")

    return AppConfig(
        email=email,
        senha_app=senha,
        gemini_api_key=api_key,
        curriculo=curriculo,
        urls_busca=urls,
    )
