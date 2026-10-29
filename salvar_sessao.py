"""
==========================================================
  Salvar Sessão do LinkedIn (Wrapper Amigável)
==========================================================
"""

from auth.session_manager import salvar_cookie_li_at

def main():
    print("\n" + "=" * 60)
    print("🔑 Autenticação do LinkedIn (Salvar Sessão)")
    print("=" * 60)
    print("Passo a passo rápido:")
    print("1. Abra o LinkedIn no seu navegador e aperte F12.")
    print("2. Clique na aba 'Application' (ou 'Aplicativo') -> 'Cookies' -> https://www.linkedin.com.")
    print("3. Procure a linha 'li_at', dê duplo clique no valor e copie com Ctrl+C.")
    print("=" * 60 + "\n")

    cookie = input("👉 Cole o cookie 'li_at' aqui: ").strip()
    if salvar_cookie_li_at(cookie):
        print("\n🎉 Sucesso! Arquivo 'state.json' atualizado.")
        print("Você já pode rodar: python manage.py run (ou python main.py)!\n")
    else:
        print("\n❌ Valor do cookie inválido. Tente novamente.\n")

if __name__ == "__main__":
    main()
