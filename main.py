"""
==========================================================
  Orquestrador Principal do Agente de Vagas (Pipeline)
==========================================================
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from config.settings import carregar_configuracao, DELAY_ENTRE_PAGINAS, ENVIADAS_FILE
from core.models import VagaDescoberta, ResultadoTriagem
from scrapers import criar_contexto_navegador, descobrir_vagas, raspar_detalhe_vaga
from analyzer import GeminiAnalyzer
from notifier import EmailService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("agente_vagas")


def carregar_urls_enviadas() -> set[str]:
    """Carrega URLs já incluídas em e-mails enviados anteriormente."""
    if not ENVIADAS_FILE.exists():
        return set()
    try:
        dados = json.loads(ENVIADAS_FILE.read_text(encoding="utf-8"))
        if isinstance(dados, list):
            return {str(url) for url in dados}
        if isinstance(dados, dict):
            return {str(url) for url in dados.get("urls", [])}
    except (OSError, json.JSONDecodeError) as exc:
        log.warning("Não foi possível carregar o histórico de enviadas: %s", exc)
    return set()


def salvar_urls_enviadas(urls: set[str]) -> None:
    """Persiste URLs enviadas com sucesso para evitar duplicidade futura."""
    payload = {
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
        "urls": sorted(urls),
    }
    ENVIADAS_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


async def executar_pipeline() -> None:
    """Executa o ciclo: Descoberta (7 dias) → Raspagem → Triagem → Notificação."""
    log.info("=" * 60)
    log.info("  🤖 Agente Autônomo de Vagas — Varredura dos Últimos 7 Dias")
    log.info("=" * 60)

    # 1. Configurações e Serviços
    cfg = carregar_configuracao()
    analyzer = GeminiAnalyzer(api_key=cfg.gemini_api_key, curriculo=cfg.curriculo)
    notifier = EmailService(remetente=cfg.email, senha_app=cfg.senha_app)

    todas_vagas: list[VagaDescoberta] = []
    urls_ja_vistas: set[str] = set()
    urls_enviadas = carregar_urls_enviadas()

    # 2. Ciclo de Scraping & Análise
    async with criar_contexto_navegador() as context:
        # FASE 1: Descoberta de Vagas do Dia
        log.info("─" * 60)
        log.info("FASE 1: DESCOBERTA DE VAGAS (ÚLTIMOS 7 DIAS)")
        log.info("─" * 60)

        for url_busca in cfg.urls_busca:
            page = await context.new_page()
            try:
                vagas = await descobrir_vagas(page, url_busca)
                for v in vagas:
                    if v.url in urls_enviadas:
                        log.info("   ↩ Vaga já enviada anteriormente; ignorando: %s", v.url)
                        continue
                    if v.url not in urls_ja_vistas:
                        urls_ja_vistas.add(v.url)
                        todas_vagas.append(v)
            finally:
                await page.close()

            await asyncio.sleep(1.5)

        log.info(
            "\n📊 Total: %d vaga(s) única(s) encontrada(s) em %d busca(s).\n",
            len(todas_vagas),
            len(cfg.urls_busca),
        )

        if not todas_vagas:
            log.warning("Nenhuma vaga nova encontrada nos últimos 7 dias.")
            return

        # FASE 2: Raspagem de Detalhe e Triagem com IA
        log.info("─" * 60)
        log.info("FASE 2: RASPAGEM E TRIAGEM RIGOROSA (GEMINI)")
        log.info("─" * 60)

        resultados: list[ResultadoTriagem] = []

        for idx, vaga in enumerate(todas_vagas, start=1):
            log.info("[%d/%d] Processando vaga (%s)…", idx, len(todas_vagas), vaga.portal.upper())

            page = await context.new_page()
            try:
                detalhes = await raspar_detalhe_vaga(page, vaga)
            finally:
                await page.close()

            if detalhes is None:
                resultados.append(
                    ResultadoTriagem(
                        url=vaga.url,
                        aprovada=False,
                        relatorio="Falha na raspagem do detalhe da vaga.",
                    )
                )
            else:
                resultado = await analyzer.analisar(detalhes)
                resultados.append(resultado)

            # Pausa de cortesia entre vagas
            if idx < len(todas_vagas):
                await asyncio.sleep(DELAY_ENTRE_PAGINAS[0])

    # FASE 3: Consolidação e Envio de E-mail
    aprovadas = [r for r in resultados if r.aprovada]
    descartadas = len(resultados) - len(aprovadas)

    log.info("─" * 60)
    log.info("FASE 3: RESULTADO FINAL & NOTIFICAÇÃO")
    log.info("─" * 60)
    log.info(
        "📊 %d aprovada(s) | %d descartada(s) | %d total avaliada(s)",
        len(aprovadas),
        descartadas,
        len(resultados),
    )

    if aprovadas:
        email_enviado = notifier.enviar_relatorio(
            destinatario=cfg.email,
            assunto=f"🎯 Agente de Vagas — {len(aprovadas)} vaga(s) compatíveis dos últimos 7 dias",
            vagas_aprovadas=aprovadas,
        )
        if email_enviado:
            urls_enviadas.update(v.url for v in aprovadas)
            salvar_urls_enviadas(urls_enviadas)
            log.info("   💾 Histórico atualizado: %d vaga(s) registradas", len(urls_enviadas))
    else:
        log.info("📭 Nenhuma vaga compatível dos últimos 7 dias encontrada. E-mail não disparado.")

    log.info("✅ Varredura finalizada com sucesso.")


def main():
    asyncio.run(executar_pipeline())


if __name__ == "__main__":
    main()
