---
name: tests-patterns
description: >
  Esta skill fornece padrões e diretrizes para a escrita de testes no projeto, garantindo consistência, qualidade e isolamento total dos testes. Inclui princípios fundamentais, estrutura de pastas, criação de fixtures, e exemplos detalhados de testes unitários, de integração e ponta a ponta.
---

## Princípios

- **Nunca mocke a SparkSession.** Use sempre o Databricks Connect via `conftest.py`. Mockar a sessão não testa nada de valor — tipos errados, comportamento Delta e otimizações do Catalyst só aparecem com sessão real.
- **Dados de teste vivem em `tests/fixtures/`.** Nunca crie dados inline nos testes. Fixtures reutilizáveis evitam duplicação e facilitam manutenção.
- **Testes validam transformações reais**, não comportamentos triviais do Spark. Nunca escreva testes genéricos que validam o que o framework já garante.
- **Isolamento total.** Nenhum teste lê ou escreve em tabelas de produção. Todo dado criado em testes usa o schema de testes configurado no `conftest.py`.
- **Padrão AAA obrigatório.** Todo teste segue Arrange → Act → Assert.
- **Testes em classes.** Cada arquivo de teste organiza seus testes em classes.
- **Todo teste documentado.** Docstring explicando o que está sendo validado.

---

## Estrutura e configuração

### Pastas

```
tests/
├── conftest.py              # SparkSession e configuração do schema de testes
├── fixtures/                # Dados de entrada e saída esperada em ndjson
│   ├── contratos/
│   │   ├── input.ndjson
│   │   └── expected.ndjson
│   └── streaming/
│       ├── destino_inicial.ndjson
│       ├── micro_batch_input.ndjson
│       └── destino_expected.ndjson
├── unit/                    # Transformações puras, sem dependência externa
│   └── test_contratos.py
├── integration/             # Leitura/escrita real no Unity Catalog
│   └── test_merge_contratos.py
└── e2e/                     # Pipeline completo de ponta a ponta
    └── test_pipeline_vendas.py
```

### conftest.py

Todos os testes usam um schema dedicado — nunca o schema de produção. O schema é informado pelo usuário e nunca gerado automaticamente. Tabelas de teste seguem o prefixo `__teste__` para fácil identificação.

```python
import json
from pathlib import Path

import pytest
from databricks.connect import DatabricksSession
from pyspark.sql import DataFrame

TEST_SCHEMA = "catalog_test.schema_testes"


@pytest.fixture(scope="session")
def spark():
    return DatabricksSession.builder.getOrCreate()


@pytest.fixture(scope="session")
def test_schema():
    return TEST_SCHEMA


def load_fixture(spark, domain: str, name: str) -> DataFrame:
    """Carrega um arquivo ndjson de fixtures como DataFrame."""
    path = Path(__file__).parent / "fixtures" / domain / f"{name}.ndjson"
    data = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return spark.createDataFrame(data)
```

---

## Unit vs Integration — quando usar cada camada

O critério é o acesso externo:

| Camada | Critério | Exemplos |
|---|---|---|
| `unit/` | Sem I/O — recebe DataFrame, devolve DataFrame | `calcular_total`, `filtrar_ativos`, condições de join |
| `integration/` | Com I/O real — lê ou escreve em tabela Delta ou Unity Catalog | `merge_micro_batch`, pipelines com `saveAsTable` |
| `e2e/` | Fluxo completo com todas as dependências reais | Pipeline de streaming com `trigger(availableNow=True)` |

**Dúvida rápida:** a função recebe um DataFrame pronto como parâmetro, ou ela mesma lê de algum lugar?
- Recebe pronto → `unit/`
- Lê por conta própria → `integration/`

---

## O que nunca testar

```python
# ❌ Valida o Spark, não o seu código
def test_filtro_funciona(spark):
    df = spark.createDataFrame([{"x": 5}, {"x": 3}])
    result = df.filter(col("x") == 5)
    assert result.filter(col("x") != 5).count() == 0

# ❌ Valida que o DataFrame não é None
def test_transformacao_retorna_dataframe(spark):
    df = calcular_total(df_input)
    assert df is not None
```

---

## Como criar uma fixture

### 1. Confirme o schema

Antes de escrever qualquer linha do ndjson, confirme nomes e tipos reais das colunas. Schema inventado gera testes que passam localmente mas falham em produção.

Fontes aceitas:
- `obter_metadados("catalog.schema.tabela")` — preferível
- Schema explicitamente informado pelo usuário na conversa

Se nenhum dos dois estiver disponível, não crie a fixture. Pergunte.

### 2. Verifique se já existe fixture para o domínio

Antes de criar um arquivo novo, olhe `tests/fixtures/`:
- Cobre os cenários que você precisa? → reuse sem alterar
- Existe mas falta algum caso? → adicione registros ao arquivo existente
- Não existe nada? → crie um arquivo novo

Nunca crie dois arquivos cobrindo o mesmo conjunto de dados com nomes diferentes.

### 3. Defina os cenários antes de escrever os dados

Pense nos cenários que os testes vão cobrir e só depois escreva os registros:
- Qual é o caso feliz?
- Existe um caso de borda relevante? (valor nulo, campo vazio, chave duplicada)
- O assert negativo precisa de dados próprios ou pode reaproveitar os existentes?

Uma fixture deve cobrir o mínimo necessário — não crie registros extras "por precaução".

### 4. Escreva o arquivo ndjson

Uma linha por registro. Siga os nomes e tipos confirmados no passo 1.

```
{"numero_contrato": "C001", "produto": "Consignado", "valor": 15000.0, "status": true}
{"numero_contrato": "C002", "produto": "Imobiliario", "valor": 250000.0, "status": false}
{"numero_contrato": "C003", "produto": "Consignado", "valor": 8000.0, "status": true}
```

Pontos de atenção:
- Tipos devem respeitar o schema: número sem aspas, booleano sem aspas, string com aspas
- Campos opcionais ausentes viram `null` automaticamente — não inclua a chave se quiser null
- Nomes de arquivo devem descrever o papel: `input`, `expected`, `destino_inicial`, `micro_batch_update`

**Coletando dados reais (quando autorizado pelo usuário)**

Verifique o tamanho antes de qualquer query:
```python
executar_sql("SELECT COUNT(*) FROM catalog.schema.tabela")
```
Colete sempre com filtro e limite — nunca full scan:
```python
executar_sql("SELECT * FROM catalog.schema.tabela WHERE status = 'ativo' LIMIT 10")
```
Copie os dados retornados para o ndjson. Nunca use dados de produção diretamente nos testes.

---

## Assertivas de DataFrame — use `pyspark.testing`

Para comparar DataFrames, priorize sempre funções de `pyspark.testing`:

```python
from pyspark.testing import assertDataFrameEqual, assertSchemaEqual

assertSchemaEqual(
    df_result.schema,
    df_expected.schema,
    ignoreColumnOrder=True,
)

assertDataFrameEqual(
    df_result,
    df_expected,
    ignoreColumnOrder=True,
)
```

- `assertDataFrameEqual` não é sensível à ordem das linhas por padrão
- Use `ignoreColumnOrder=True` para ignorar ordem de colunas
- Use `assert` manual apenas para casos escalares: contagem, ausência de chave, valor único

Evite:
```python
# ❌ lento e frágil — falha se a ordem mudar
result_rows = df.collect()
assert result_rows == expected_rows
```

---

## Escrevendo testes

### Unit tests

```python
from pyspark.testing import assertDataFrameEqual

from meu_projeto.transformations.contratos import calcular_total, filtrar_ativos


class TestCalcularTotal:
    """Testes para a transformação calcular_total."""

    def test_soma_parcelas_por_contrato(self, spark):
        """
        Valida que calcular_total soma corretamente o valor
        de parcelas agrupadas por numero_contrato.
        Cenário: 3 parcelas do C001 com valores 100, 200 e 300.
        Esperado: total de 600 para C001.
        """
        # Arrange
        df_input = load_fixture(spark, "contratos", "input_parcelas")
        df_expected = load_fixture(spark, "contratos", "expected_total")

        # Act
        df_result = calcular_total(df_input)

        # Assert
        assertDataFrameEqual(
            df_result,
            df_expected,
            ignoreColumnOrder=True,
        )

    def test_contrato_sem_parcelas_nao_aparece_no_resultado(self, spark):
        """
        Valida que contratos sem parcelas não geram linha no resultado.
        Cenário: C999 existe mas não tem parcelas associadas.
        Esperado: C999 ausente no resultado — join deve ser INNER.
        """
        # Arrange
        df_input = load_fixture(spark, "contratos", "input_sem_parcelas")

        # Act
        df_result = calcular_total(df_input)

        # Assert — caso específico, assert manual é adequado
        contratos = [r["numero_contrato"] for r in df_result.collect()]
        assert "C999" not in contratos, "C999 não deveria aparecer — não possui parcelas"
```

### Integration tests

```python
from pyspark.testing import assertDataFrameEqual

from meu_projeto.streaming.pipeline import merge_micro_batch


class TestMergeMicroBatch:
    """Testes de integração para merge_micro_batch com Delta real."""

    def test_atualiza_registro_existente(self, spark, test_schema):
        """
        Valida que um registro existente é atualizado pelo merge.
        Cenário: target tem C001 com valor=100, micro-lote traz C001 com valor=200.
        Esperado: C001 no target com valor=200 após o merge.
        """
        # Arrange
        tabela = f"{test_schema}.__teste__tabela_destino"
        load_fixture(spark, "streaming", "destino_inicial") \
            .write.format("delta").mode("overwrite").saveAsTable(tabela)
        df_micro_batch = load_fixture(spark, "streaming", "micro_batch_update")

        # Act
        merge_micro_batch(df_micro_batch, batchId=0, target_table=tabela)

        # Assert
        df_result = spark.read.table(tabela)
        df_expected = load_fixture(spark, "streaming", "destino_expected_update")
        assertDataFrameEqual(
            df_result,
            df_expected,
            ignoreColumnOrder=True,
        )

    def test_insere_registro_novo(self, spark, test_schema):
        """
        Valida que um registro com chave nova é inserido no target.
        Cenário: target tem C001, micro-lote traz C002 (chave nova).
        Esperado: target com C001 e C002 após o merge.
        """
        # Arrange
        tabela = f"{test_schema}.__teste__tabela_destino"
        load_fixture(spark, "streaming", "destino_inicial") \
            .write.format("delta").mode("overwrite").saveAsTable(tabela)
        df_micro_batch = load_fixture(spark, "streaming", "micro_batch_insert")

        # Act
        merge_micro_batch(df_micro_batch, batchId=0, target_table=tabela)

        # Assert
        df_result = spark.read.table(tabela)
        df_expected = load_fixture(spark, "streaming", "destino_expected_insert")
        assertDataFrameEqual(
            df_result,
            df_expected,
            ignoreColumnOrder=True,
        )

    def test_nao_duplica_registro_existente(self, spark, test_schema):
        """
        Valida que o merge não duplica registros com chave existente.
        Cenário: target tem C001, micro-lote traz C001 com mesmos dados.
        Esperado: target ainda com 1 linha após o merge.
        """
        # Arrange
        tabela = f"{test_schema}.__teste__tabela_destino"
        load_fixture(spark, "streaming", "destino_inicial") \
            .write.format("delta").mode("overwrite").saveAsTable(tabela)

        # Act
        merge_micro_batch(
            load_fixture(spark, "streaming", "destino_inicial"),
            batchId=0,
            target_table=tabela,
        )

        # Assert — caso de contagem, assert manual é adequado
        total = spark.read.table(tabela).count()
        assert total == 1, f"Esperada 1 linha após merge sem novidade, obtidas {total}"
```

---

## Testabilidade — observe antes de testar

Se identificar dificuldades, aponte como observação — nunca refatore por conta própria.

**Dependência hardcoded de tabela**
```python
def merge_micro_batch(df, batchId):
    delta_target = DeltaTable.forName(spark, "catalog.schema.tabela_final")
```
Observação: o nome da tabela fixo impede isolar qual tabela o teste vai usar. Receber `target_table` como parâmetro tornaria essa função testável em `integration/`.

**SparkSession global ou implícita**
```python
def transformar(df):
    return spark.sql("SELECT ...")
```
Observação: `spark` vindo de escopo global impede controle da sessão no teste. Receber `spark` como parâmetro resolveria.

**Pipeline de streaming sem retorno da query**
```python
def iniciar_pipeline():
    spark.readStream.table("...").writeStream.start()
```
Observação: sem acesso à `StreamingQuery`, não é possível aguardar a conclusão nem inspecionar o resultado no teste.

---

## Testes de streaming

### O que testar

| O que | Camada | Faz sentido? |
|---|---|---|
| `foreachBatch` / merge | `integration/` | ✅ |
| Condições de join com casos limite | `unit/` | ✅ |
| Fontes são stream ou batch | `unit/` | ✅ |
| Pipeline completo com `trigger(availableNow=True)` | `e2e/` | ✅ |
| Watermark expirando estado | — | ❌ responsabilidade do Spark |
| Pipeline rodando continuamente | — | ❌ não automatize |

### Garantindo tipos de fonte

```python
class TestFontesDoPipeline:
    """Valida que as fontes usam o tipo correto de leitura."""

    def test_fontes_de_streaming_usam_readstream(self, spark):
        """
        Valida que as tabelas de streaming usam readStream e não read.
        Trocar readStream por read remove o comportamento stateful
        silenciosamente — este teste detecta isso em CI.
        """
        # Arrange / Act
        stream_base = spark.readStream.table("catalog.schema.tabela_streaming_base")
        stream_inner = spark.readStream.table("catalog.schema.tabela_streaming_inner")
        stream_left = spark.readStream.table("catalog.schema.tabela_streaming_left")

        # Assert
        assert stream_base.isStreaming, "tabela_streaming_base deve ser readStream"
        assert stream_inner.isStreaming, "tabela_streaming_inner deve ser readStream"
        assert stream_left.isStreaming, "tabela_streaming_left deve ser readStream"

    def test_fonte_estatica_usa_read(self, spark):
        """
        Valida que a tabela estática usa read e não readStream.
        Uma tabela estática lida como readStream muda o plano de execução
        e pode causar comportamentos inesperados no join encadeado.
        """
        # Arrange / Act
        static_inner = spark.read.table("catalog.schema.tabela_estatica")

        # Assert
        assert not static_inner.isStreaming, "tabela_estatica deve ser read, não readStream"
```

### Condições de join

```python
class TestCondicoesDeJoin:
    """Testes das condições de join do pipeline."""

    def test_inner_join_inclui_evento_dentro_do_intervalo(self, spark):
        """
        Valida que eventos dentro de 1 hora entram no inner join.
        Cenário: evento inner com 30min de diferença do base.
        Esperado: 1 linha no resultado.
        """
        # Arrange
        df_base = load_fixture(spark, "streaming", "base_input")
        df_inner = load_fixture(spark, "streaming", "inner_dentro_intervalo")
        condicao = expr("""
            stream_base.id = stream_inner.id AND
            stream_inner.event_time_inner BETWEEN
                stream_base.event_time_base AND
                stream_base.event_time_base + INTERVAL 1 HOUR
        """)

        # Act
        df_result = df_base.alias("stream_base").join(
            df_inner.alias("stream_inner"), condicao, "inner"
        )

        # Assert
        assert df_result.count() == 1, "Evento dentro do intervalo de 1h deveria entrar no join"

    def test_inner_join_exclui_evento_fora_do_intervalo(self, spark):
        """
        Valida que eventos fora de 1 hora não entram no inner join.
        Cenário: evento inner com 2h de diferença do base.
        Esperado: resultado vazio.
        """
        # Arrange
        df_base = load_fixture(spark, "streaming", "base_input")
        df_inner = load_fixture(spark, "streaming", "inner_fora_intervalo")
        condicao = expr("""
            stream_base.id = stream_inner.id AND
            stream_inner.event_time_inner BETWEEN
                stream_base.event_time_base AND
                stream_base.event_time_base + INTERVAL 1 HOUR
        """)

        # Act
        df_result = df_base.alias("stream_base").join(
            df_inner.alias("stream_inner"), condicao, "inner"
        )

        # Assert
        assert df_result.count() == 0, "Evento fora do intervalo de 1h não deveria entrar no join"

    def test_left_join_preserva_linha_sem_match(self, spark):
        """
        Valida que o left join preserva linhas sem correspondência no lado direito.
        Cenário: nenhum evento left dentro do intervalo de 2h.
        Esperado: linha preservada com nulos no lado direito.
        """
        # Arrange
        df_joined_2 = load_fixture(spark, "streaming", "joined_2_input")
        df_left = load_fixture(spark, "streaming", "left_sem_match")
        condicao = expr("""
            joined_2.id_left = stream_left.id AND
            stream_left.event_time_left BETWEEN
                joined_2.event_time_base AND
                joined_2.event_time_base + INTERVAL 2 HOURS
        """)

        # Act
        df_result = df_joined_2.alias("joined_2").join(
            df_left.alias("stream_left"), condicao, "left"
        )

        # Assert
        nulos = df_result.filter(F.col("stream_left.id").isNull()).count()
        assert nulos == df_joined_2.count(), (
            "Todas as linhas sem match devem ter nulos no lado direito"
        )
```