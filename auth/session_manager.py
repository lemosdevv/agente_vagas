"""
==========================================================
  Gerenciador de Sessão & Cookies (Auth Module)
==========================================================
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from config.settings import STATE_FILE

log = logging.getLogger("agente_vagas.auth")


def salvar_cookie_li_at(li_at_value: str, destino: Path = STATE_FILE) -> bool:
    """Gera o state.json diretamente a partir do cookie li_at."""
    li_at_value = li_at_value.strip().strip('"').strip("'")
    if not li_at_value:
        return False

    state_data = {
        "cookies": [
            {
                "name": "li_at",
                "value": li_at_value,
                "domain": ".linkedin.com",
                "path": "/",
                "expires": int(time.time()) + (365 * 24 * 3600),
                "httpOnly": True,
                "secure": True,
                "sameSite": "None",
            },
            {
                "name": "li_theme",
                "value": "light",
                "domain": ".linkedin.com",
                "path": "/",
                "expires": int(time.time()) + (365 * 24 * 3600),
                "httpOnly": False,
                "secure": True,
                "sameSite": "Lax",
            },
        ],
        "origins": [
            {
                "origin": "https://www.linkedin.com",
                "localStorage": [],
            }
        ],
    }

    destino.write_text(json.dumps(state_data, indent=2), encoding="utf-8")
    log.info("✔ Sessão salva com sucesso em %s", destino.name)
    return True


def sessao_existe(caminho: Path = STATE_FILE) -> bool:
    """Verifica se o arquivo de sessão existe e possui dados."""
    return caminho.exists() and caminho.stat().st_size > 50
