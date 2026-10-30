# Agente de Vagas

> Agente em Python para buscar, filtrar e enviar por e-mail oportunidades de estágio e início de carreira em tecnologia.

O projeto consulta buscas manuais configuradas pelo usuário em portais de emprego, coleta os detalhes das vagas, aplica regras de compatibilidade com auxílio do Google Gemini e envia um relatório consolidado por e-mail.

> O agente não se candidata automaticamente às vagas e não envia currículo por conta própria.

## Funcionalidades

- Busca em Gupy, Indeed, Catho, InfoJobs e LinkedIn.
- URLs de busca definidas manualmente em `urls_alvo.txt`.
- Filtro de vagas publicadas nos últimos 7 dias.
- Triagem por localização, modalidade, senioridade, área, tecnologias e idioma.
- Aceita inglês técnico, mas descarta descrições predominantemente em inglês ou exigência de inglês avançado.
- Rejeita cargos claramente incompatíveis, como vendas, caixa, restaurante, recepção e serviços gerais.
- Evita processar links de navegação, categorias e páginas de pagamento.
- Histórico persistente para não enviar a mesma vaga novamente.
- Relatório HTML enviado por Gmail SMTP.

## Portais e buscas

As buscas são controladas manualmente pelo arquivo [`urls_alvo.txt`](urls_alvo.txt). Cada linha ativa representa uma busca; linhas iniciadas com `#` são ignoradas.

Exemplo:

```text
https://br.indeed.com/jobs?q=devops&l=Brasil&fromage=7
https://portal.gupy.io/vagas?searchTerm=backend
```

Para pausar uma busca, comente a linha:

```text
# https://br.indeed.com/jobs?q=devops&l=Brasil&fromage=7
```

O projeto inclui buscas manuais para:

- Estágio
- Desenvolvedor Júnior
- DevOps
- Backend
- Full Stack
- Analista de Sistemas

## Requisitos

- Python 3.10 ou superior
- Chromium instalado pelo Playwright
- Chave da API do Google Gemini
- Conta Gmail com senha de app para envio SMTP

## Instalação

Clone o repositório e entre na pasta do projeto:

```bash
git clone https://github.com/SEU_USUARIO/agente-vagas.git
cd agente-vagas
```

Crie um ambiente virtual:

```bash
python -m venv .venv
```

Ative o ambiente virtual no Linux ou WSL:

```bash
source .venv/bin/activate
```

No Windows PowerShell:

```powershell
.\\.venv\\Scripts\\Activate.ps1
```

Instale as dependências:

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

## Configuração

Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

No Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Preencha o `.env`:

```env
MEU_EMAIL=seu_email@gmail.com
SENHA_APP=sua_senha_de_app
GEMINI_API_KEY=sua_chave_gemini
```

`SENHA_APP` deve ser uma senha de app do Google, não a senha normal da conta Gmail.

## Execução

```bash
python agente_v1.py
```

O pipeline executa três fases:

1. Descoberta das vagas configuradas.
2. Raspagem dos detalhes e triagem técnica.
3. Consolidação e envio do relatório por e-mail.

## Histórico de vagas enviadas

Depois de um envio bem-sucedido, as URLs são registradas em:

```text
vagas_enviadas.json
```

Nas próximas execuções, essas URLs serão ignoradas para evitar duplicidade.

Esse arquivo é criado automaticamente e deve permanecer fora do controle de versão. O histórico contém apenas URLs e datas de atualização, não credenciais.

## Regras de triagem

Uma vaga só é aprovada quando atende aos critérios principais:

- Publicação nos últimos 7 dias.
- Localização no Brasil.
- São Paulo: aceita presencial, híbrida ou remota.
- Fora de São Paulo: aceita apenas se for 100% remota.
- Nível estágio ou júnior.
- Área de backend, full stack, automação, DevOps ou suporte de infraestrutura.
- Compatibilidade razoável com a stack do candidato.
- Inglês técnico permitido; inglês avançado ou fluente não aceito.

Em caso de dúvida, a vaga é descartada.

## Estrutura do projeto

```text
agente_vagas/
├── agente_v1.py                 # ponto de entrada
├── main.py                      # orquestração do pipeline
├── urls_alvo.txt                # buscas manuais
├── curriculo.txt                # contexto usado na triagem
├── requirements.txt             # dependências Python
├── .env.example                 # modelo de configuração
├── analyzer/                    # integração e prompts do Gemini
├── auth/                        # código legado de sessão do LinkedIn
├── config/                      # configurações da aplicação
├── core/                        # modelos de domínio
├── notifier/                    # geração e envio de e-mail
└── scrapers/                    # navegador, descoberta e extratores
```

## Segurança

Nunca publique:

- `.env`
- `GEMINI_API_KEY`
- Senha de app do Gmail
- Cookies de sessão
- `state.json`
- `vagas_enviadas.json`, se preferir manter seu histórico privado
- Dados pessoais do currículo

Confirme se esses arquivos estão no `.gitignore` antes de fazer o primeiro `git push`.

## Limitações conhecidas

- Portais podem alterar o HTML e quebrar seletores de extração.
- Indeed e LinkedIn podem bloquear ou limitar acessos automatizados.
- Algumas vagas exigem login ou exibem conteúdo incompleto para visitantes.
- O filtro temporal depende das informações exibidas pelo portal e pelo texto da vaga.
- O histórico evita duplicidades a partir da primeira execução que criar `vagas_enviadas.json`; links enviados antes disso precisam ser cadastrados manualmente.

## Licença

Defina a licença do projeto antes de publicar. Para um projeto pessoal, MIT é uma opção comum:

```text
MIT License
Copyright (c) Mateus Lemos do Nascimento
```

