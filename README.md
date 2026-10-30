# 🤖 Agente Autônomo de Vagas v1.0 — Varredura Ilimitada do Dia

Agente de IA em Python que realiza **varreduras diárias completas e sem limites** em portais de emprego, descobrindo **todas** as oportunidades publicadas no dia (últimas 24 horas), filtrando por IA e enviando um relatório consolidado.

## 🎯 Regras de Negócio da Varredura (v1.0)

1. **Sem Limite de Quantidade:**
   - Coleta e analisa **todas** as vagas retornadas nas buscas do dia (sem teto de 15 ou 20 vagas).
   - Paginação automática até esgotar todos os lotes de vagas recentes.
2. **Filtro Temporal Estrito (Últimas 24h):**
   - No LinkedIn, aplica automaticamente `f_TPR=r86400` (últimas 24h).
   - O Gemini descarta qualquer vaga postada há 2 dias, 1 semana ou mais.
3. **Geolocalização & Modalidade:**
   - Apenas vagas no **Brasil** (gringas descartadas).
   - **São Paulo (SP):** Aceita Remota, Híbrida ou Presencial.
   - **Fora de SP:** Aceita **apenas se for 100% Remota**.
4. **Nível:** Estágio e Júnior.
5. **Áreas:** Backend, Full Stack, Automação de Dados, DevOps, Suporte Infra.
6. **Idioma:** Descarta vagas com descrição predominantemente em inglês ou exigência de inglês avançado/fluente. Aceita inglês técnico para leitura de documentação e termos da área.
7. **Relatório Consolidado por E-mail:**
   - Todas as vagas aprovadas do dia enviadas via Gmail SSL com botão direto de 1 clique para candidatura.

---

## ⚡ Como Executar

No seu terminal do WSL (`lemos@mateus:...`):

```bash
python agente_v1.py
```
