#!/usr/bin/env python
"""
==========================================================
  Interface de Linha de Comando (CLI / manage.py)
==========================================================
Uso:
  python manage.py run        -> Executa a varredura e triagem de vagas
  python manage.py auth       -> Conecta sua conta do LinkedIn (salva sessão)
"""

import sys
from main import main as run_pipeline
from auth.session_manager import salvar_cookie_li_at, sessao_existe


def comando_auth():
    print("\n" + "=" * 60)
    print("🔑 Autenticação do LinkedIn (Salvar Sessão)")
    print("=" * 60)
    print("Como pegar o cookie li_at em 5 segundos:")
    print("1. Abra o LinkedIn no seu navegador e aperte F12.")
    print("2. Vá na aba Application (ou Aplicativo) -> Cookies -> https://www.linkedin.com.")
    print("3. Procure a linha com o nome 'li_at', dê duplo clique no valor e copie com Ctrl+C.")
    print("=" * 60 + "\n")

    cookie = input("👉 Cole o valor do cookie 'li_at' aqui: ").strip()
    if salvar_cookie_li_at(cookie):
        print("\n🎉 Sessão configurada com sucesso!")
    else:
        print("\n❌ Valor inválido. Tente novamente.")


def main():
    args = sys.argv[1:]
    comando = args[0] if args else "run"

    if comando == "run":
        run_pipeline()
    elif comando in ["auth", "login"]:
        comando_auth()
    elif comando in ["check", "status"]:
        if sessao_existe():
            print("✔ Sessão do LinkedIn encontrada e ativa (state.json).")
        else:
            print("ℹ Nenhuma sessão salva encontrada. Execute: python manage.py auth")
    else:
        print(f"Comando desconhecido: '{comando}'")
        print("Comandos disponíveis: run, auth, check")


if __name__ == "__main__":
    main()
