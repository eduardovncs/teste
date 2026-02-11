# PLANO: {Nome da Feature}

> Descrição em uma frase do que será construído.

## Metadados

| Campo | Valor |
|-------|-------|
| **Feature** | {NOME_DA_FEATURE} |
| **Data** | {AAAA-MM-DD} |
| **Status** | {Rascunho / Em Análise / Aprovado / Em Execução / Concluído} |
| **Clareza** | {X}/15 |

---

## Problema

{1-2 frases descrevendo a dor que estamos resolvendo. Seja específico sobre quem tem o problema e qual o impacto.}

---

## Critérios de Sucesso

- [ ] {Métrica 1: ex. "Processar 1000 requisições por minuto"}
- [ ] {Métrica 2: ex. "Atingir 99,9% de uptime"}
- [ ] {Métrica 3: ex. "Tempo de resposta abaixo de 200ms"}

---

## Fora do Escopo

- {Item 1: O que NÃO faremos}
- {Item 2: O que fica para o futuro}
- {Item 3: O que está explicitamente excluído}

---

## Restrições

| Tipo | Restrição | Impacto |
|------|-----------|---------|
| Técnica | {ex. "Usar schema de banco existente"} | {Como afeta o design} |
| Prazo | {ex. "Entregar até Q1"} | {Como afeta o escopo} |
| Recurso | {ex. "Sem budget extra de infra"} | {Como afeta a abordagem} |

---

## Contexto Técnico

| Aspecto | Valor | Notas |
|---------|-------|-------|
| **Local de Deploy** | {src/ \| functions/ \| gen/ \| deploy/ \| outro} | {Por quê} |
| **Domínios Base conhecimento** | {pydantic, gcp, gemini, langfuse, terraform, crewai, openrouter} | {Quais padrões consultar} |
| **Impacto IaC** | {Novos recursos \| Modificar existentes \| Nenhum \| A definir} | {Mudanças em Terraform/Terragrunt} |

---

## Premissas

| ID | Premissa | Se errada, impacto | Validada? |
|----|----------|---------------------|-----------|
| P-001 | {ex. "Banco aguenta a carga esperada"} | {Precisaria de cache} | [ ] |
| P-002 | {ex. "Volume < 1000 req/hora"} | {Precisaria de rate limiting} | [ ] |

---

## Tarefas do Plano

> Cada tarefa referencia um agente responsável. Veja detalhes completos em `.github/tasks/`.

| # | Tarefa | Agente | Dependência | Status |
|---|--------|--------|-------------|--------|
| 1 | {Ex: Levantar e validar requisitos} | `define-agent` | — | ⬜ Pendente |
| 2 | {Ex: Projetar arquitetura} | `design-agent` | 1 | ⬜ Pendente |
| 3 | {Ex: Implementar módulo X} | `dev-agent` | 2 | ⬜ Pendente |
| 4 | {Ex: Implementar módulo Y} | `dev-agent` | 2 | ⬜ Pendente |
| 5 | {Ex: Escrever testes} | `test-agent` | 3, 4 | ⬜ Pendente |
| 6 | {Ex: Provisionar infra} | `infra-agent`  | 2 | ⬜ Pendente |
| 7 | {Ex: Deploy e validação} | `deploy-agent` | 5, 6 | ⬜ Pendente |

**Legenda de Status:** ⬜ Pendente · 🔄 Em Progresso · ✅ Concluída · ❌ Bloqueada

---

## Pontuação de Clareza

| Elemento | Nota (0-3) | Observação |
|----------|------------|------------|
| Problema | {0-3} | {Justificativa} |
| Restrições | {0-3} | {Justificativa} |
| Tarefas | {0-3} | {Justificativa} |
| Escopo | {0-3} | {Justificativa} |
| **Total** | **{X}/12** | |

> 0 = Ausente · 1 = Vago · 2 = Claro, faltam detalhes · 3 = Cristalino e acionável
>
> **Mínimo para prosseguir: 10/12**

---

## Perguntas em Aberto

{Liste dúvidas pendentes antes de iniciar a execução. Se não houver, escreva "Nenhuma — pronto para execução."}

---

## Próximo Passo

**Pronto para:** Gerar tarefas detalhadas em `.github/tasks/TAREFA_{NOME_DA_FEATURE}_XXX.md`
