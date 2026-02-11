# TAREFA: {ID} — {Título da Tarefa}

## Metadados

| Campo | Valor |
|-------|-------|
| **ID** | {FEAT-XXX} |
| **Plano** | {Link para o plano: `.github/tasks/plano_{feature}.md`} |
| **Agente** | {nome-do-agente} |
| **Status** | {⬜ Pendente / 🔄 Em Progresso / ✅ Concluída / ❌ Bloqueada} |
| **Prioridade** | {DEVE / DEVERIA / PODERIA} |
| **Criada em** | {AAAA-MM-DD} |
| **Concluída em** | {AAAA-MM-DD ou —} |

---

## Objetivo

{1-2 frases: o que essa tarefa entrega e por que ela existe.}

---

## Dependências

| Tipo | Referência | Status |
|------|------------|--------|
| Bloqueia | {FEAT-YYY — tarefa que depende desta} | {Status} |
| Depende de | {FEAT-ZZZ — tarefa que precisa estar pronta} | {Status} |

> Se não houver dependências, escreva "Nenhuma".

---

## Entradas

O que o agente precisa para começar:

- [ ] {Artefato 1: ex. "Documento DEFINE aprovado"}
- [ ] {Artefato 2: ex. "Schema do banco atualizado"}
- [ ] {Artefato 3: ex. "Acesso ao ambiente de staging"}

---

## Saídas Esperadas

O que a tarefa deve produzir ao final:

- [ ] {Entregável 1: ex. "Módulo `src/core/teste.py` implementado"}
- [ ] {Entregável 2: ex. "Testes unitários cobrindo >80%"}
- [ ] {Entregável 3: ex. "Documentação da API atualizada"}

---

## Critérios de Aceite

| # | Critério | Verificado? |
|---|----------|-------------|
| 1 | {Ex: Função processa PDF sem erro} | [ ] |
| 2 | {Ex: Resposta em < 500ms para arquivos até 10MB} | [ ] |
| 3 | {Ex: Log estruturado para cada execução} | [ ] |

---

## Instruções para o Agente

> Contexto e diretrizes específicas para o agente executar esta tarefa.

### Escopo

```
- FAZER: {o que deve ser feito}
- NÃO FAZER: {o que está fora do escopo desta tarefa}
```

### Arquivos Relevantes

| Arquivo | Ação | Descrição |
|---------|------|-----------|
| {caminho/arquivo.py} | Criar / Editar | {O que fazer} |
| {caminho/outro.py} | Consultar | {Por que consultar} |

### Padrões a Seguir

- {Ex: "Usar Pydantic para validação de entrada"}
- {Ex: "Seguir convenção de logging do projeto"}
- {Ex: "Consultar `.github/base_conhecimento/dados.md` para exemplos"}

---

## Notas de Execução

> Preenchido pelo agente durante/após a execução.

### Decisões Tomadas

| Decisão | Justificativa |
|---------|---------------|
| {Ex: Usou retry com backoff exponencial} | {Chamadas à API podem falhar por timeout} |

### Problemas Encontrados

| Problema | Resolução | Impacto |
|----------|-----------|---------|
| {Ex: API retorna 429 com carga alta} | {Implementou rate limiter} | {Nenhum no prazo} |

### Observações

{Notas livres do agente sobre a execução. Se nada a registrar, escreva "—".}
