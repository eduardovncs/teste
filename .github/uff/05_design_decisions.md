# Decisões de Design
**Async Batch Processing Pipeline — Databricks**

---

## EmpacotadorJsonl separado do EnviadorStorage
Compressão e upload são responsabilidades distintas. Separar os dois permite trocar o formato de compressão (.xz → .gz) sem tocar na lógica de upload, e vice-versa.

## Poller genérico
O poller não conhece a API — recebe endpoint e parser do SolicitadorProcessamento. É chamado duas vezes com configurações diferentes: uma para aguardar o batch_id da cloud, outra para aguardar o processamento finalizar. Troca de mecanismo de polling (ex: webhook) afeta apenas o SolicitadorProcessamento.

## SolicitadorProcessamento centraliza o conhecimento da API
Apenas o SolicitadorProcessamento conhece os endpoints, formatos de resposta e critérios de sucesso da API externa. O Orquestrador e o Poller não têm dependência direta da API.

## ValidadorRecuperacao com interface IValidavel
Cada componente implementa `validar_registros()` com suas próprias regras de integridade. O `ValidadorRecuperacao` não conhece regras de nenhum componente — só orquestra a validação e decide o destino dos inválidos.

## Regra de ERRO_GLOBAL com maior_status e total_tentativas
Dois campos simples na Control Table resolvem detecção de problemas crônicos sem contadores por etapa. `maior_status` nunca regride — garante que falhas repetidas na mesma etapa mais avançada sejam detectadas mesmo com falhas intercaladas em outras etapas. `total_tentativas` nunca reseta — acumula todas as falhas.

## Status INVALIDO temporário
Usado apenas durante a execução do `ValidadorRecuperacao`. Nunca persiste entre execuções. Garante que o pipeline nunca processa registros em estado inconsistente.

## Status JSONL_GERADO separado de BATCHED
Separar os dois status permite que o `EmpacotadorJsonl` saiba exatamente quais arquivos precisa compactar, independente de registros já em BATCHED de execuções anteriores. Cada componente consulta só o seu status de entrada.

## batch_id como campo de trabalho reutilizado
O batch_id interno é limpo ao final do GeradorJsonl. O mesmo campo é reutilizado pelo batch_id da cloud quando o Poller 1 retornar. Mantém a tabela simples sem colunas extras. O mesmo princípio se aplica ao campo path.

## TabelaControle atualiza por batch_id
Registros de um mesmo batch avançam juntos. Um único `UPDATE WHERE batch_id = X` substitui N operações individuais — mais eficiente no Delta Lake.

## GeradorJsonl em duas fases
Fase 1 atribui e persiste os batch_ids materializando no Delta antes de iniciar a Fase 2. Evita problemas de lazy evaluation do Spark ao gerar os .jsonl por batch_id consultado diretamente da tabela.

## EmpacotadorJsonl consulta paths da Control Table
O empacotador não varre diretórios — opera sobre paths explícitos consultados na tabela. Isso garante que mudanças futuras (múltiplos .xz) só exijam ajuste no agrupamento, não na lógica de varredura.

## EmpacotadorJsonl valida conteúdo do .xz antes de deletar
O .xz é aberto e verificado antes de qualquer deleção. Se inválido, deleta o corrompido e tenta novamente (máximo 2 tentativas). Os .jsonl só são deletados após confirmação do .xz válido.

## Nível de compressão LZMA fixo em 1
Decisão técnica do projeto — não configurável externamente. Nível 1 oferece melhor performance para pipelines com execução diária. Implementado como constante interna `_NIVEL_COMPRESSAO = 1`.

## Compartilhado como fonte de configuração global
Paths de volume, schemas e databases são obtidos via `Compartilhado.obter()` — classe estática com métodos de acesso. Cada componente acessa diretamente e constrói seu próprio subpath. O Orquestrador não conhece detalhes de onde cada componente salva seus arquivos.

## Processamento sequencial aceito
O Poller bloqueia por até 5 horas aguardando o job finalizar. Dado que o pipeline roda uma vez por dia e o volume é compatível, paralelismo não é necessário nesta versão.

## TabelaControle como porta de entrada genérica
Centraliza criação, inicialização e updates genéricos da Control Table. O nome reflete exatamente o que é — sem padrões de design implícitos. Componentes fazem queries diretas apenas quando têm contexto específico que o TabelaControle não possui — ex: GeradorJsonl é o único que sabe o mapeamento registro → batch_id.

## Renomeação de TabelaControle para TabelaControle
TabelaControle sugeria responsabilidade limitada a status. TabelaControle reflete melhor o escopo real — criação do schema, inicialização com campos do usuário, e todos os acessos genéricos à tabela.
