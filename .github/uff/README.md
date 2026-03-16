# Async Batch Processing Pipeline — Databricks
Documentação de arquitetura seguindo o modelo C4.

---

## Estrutura dos documentos

| Arquivo | Conteúdo |
|---------|----------|
| `01_context.md` | C1 e C2 — visão geral do sistema e containers |
| `02_components.md` | C3 — componentes, responsabilidades e sequência geral |
| `03_flow.md` | Fluxos de execução, recuperação e erros |
| `04_control_table.md` | Campos, status e ciclo de vida da Control Table |
| `05_design_decisions.md` | Decisões de design e justificativas |
| `06_c4_gerador_jsonl.md` | C4 — GeradorJsonl (classes + sequência) |
| `07_c4_empacotador_jsonl.md` | C4 — EmpacotadorJsonl (classes + sequência) |
| `08_c4_validador_recuperacao.md` | C4 — ValidadorRecuperacao (classes + sequência) |
| `09_c4_tabela_controle.md` | C4 — TabelaControle (classes + sequência) |

---

## Componentes documentados

- [x] TabelaControle
- [x] GeradorJsonl
- [x] EmpacotadorJsonl
- [x] ValidadorRecuperacao
- [ ] EnviadorStorage
- [ ] SolicitadorProcessamento
- [ ] Poller
- [ ] ColetorResultados
- [ ] MonitorMLflow
- [ ] Orquestrador
