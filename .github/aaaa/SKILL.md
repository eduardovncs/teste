---
name: pyspark-patterns
description: Padrões de estilo e estrutura para código PySpark no projeto.
---

## Imports

Sempre explícitos — nunca `from pyspark.sql.functions import *`.

```python
from pyspark.sql.functions import col, count, sum as spk_sum, when, lit
```

Quando uma função do PySpark conflitar com built-in do Python, use alias com prefixo `spk_`:

```python
# ❌ Sobrescreve o built-in sum do Python
from pyspark.sql.functions import sum

# ✅
from pyspark.sql.functions import sum as spk_sum, max as spk_max, min as spk_min
```

---

## Referência a colunas

Nunca use strings soltas para referenciar colunas. Use sempre `col()`.

```python
# ❌
df.select("valor", "status")
df.filter("status == true")
df.orderBy("data_nascimento")

# ✅
df.select(col("valor"), col("status"))
df.filter(col("status") == True)
df.orderBy(col("data_nascimento"))
```

---

## Nomes de variáveis

Use sempre `df_` como prefixo seguido de um nome que descreva o conteúdo.
Nunca use nomes genéricos ou sequenciais.

```python
# ❌
df1 = spark.read.table("...")
df2 = df1.filter(...)
df_aux = df2.groupBy(...)

# ✅
df_contratos_raw = spark.read.table("...")
df_contratos_ativos = df_contratos_raw.filter(...)
df_contratos_por_produto = df_contratos_ativos.groupBy(...)
```

---

## Encadeamento de operações

Cada operação em linha separada. Sempre abrir parênteses na definição
quando houver mais de uma operação encadeada.

```python
# ❌
df_resultado = spark.read.table("catalog.schema.tabela").filter(col("status") == True).groupBy(col("produto")).agg(count("*"))

# ✅
df_resultado = (
    spark.read.table("catalog.schema.tabela")
    .filter(col("status") == True)
    .groupBy(col("produto"))
    .agg(
        count("*").alias("total")
    )
)
```

---

## `select` e `agg` — sempre com parênteses abertos

Quando houver mais de uma expressão, abra parênteses e coloque cada
expressão em linha separada.

```python
# ❌
df.select(col("valor"), col("status"), col("produto"))
df.agg(count("*").alias("total"), spk_sum(col("valor")).alias("soma"))

# ✅
df.select(
    col("valor"),
    col("status"),
    col("produto"),
)

df.agg(
    count("*").alias("total"),
    spk_sum(col("valor")).alias("soma"),
)
```

---

## `withColumn` — encadeie na mesma operação

Nunca reatribua o DataFrame a cada `withColumn`. Encadeie tudo dentro
do mesmo bloco de parênteses.

```python
# ❌
df = df_contratos.withColumn("valor_total", col("valor") * col("parcelas"))
df = df.withColumn("status_label", when(col("status") == True, lit("ativo")).otherwise(lit("inativo")))
df = df.withColumn("data_referencia", current_date())

# ✅
df_contratos_enriquecido = (
    df_contratos
    .withColumn("valor_total", col("valor") * col("parcelas"))
    .withColumn("status_label", when(col("status") == True, lit("ativo")).otherwise(lit("inativo")))
    .withColumn("data_referencia", current_date())
)
```

O mesmo vale para `withColumnRenamed`:

```python
# ✅
df_contratos_renomeado = (
    df_contratos
    .withColumnRenamed("vcontr", "valor_contrato")
    .withColumnRenamed("dtvcto", "data_vencimento")
    .withColumnRenamed("cdprod", "codigo_produto")
)
```

---

## `saveAsTable` — fora dos parênteses, no final

A operação de escrita fica fora do bloco de parênteses da transformação.

```python
# ❌
(
    spark.read.table("catalog.schema.tabela_origem")
    .filter(col("status") == True)
    .write
    .mode("overwrite")
    .saveAsTable("catalog.schema.tabela_destino")
)

# ✅
(
    spark.read.table("catalog.schema.tabela_origem")
    .filter(col("status") == True)
    .write
    .mode("overwrite")
).saveAsTable("catalog.schema.tabela_destino")
```

---

## Joins

Prefira sempre `on=["coluna"]` para evitar duplicidade de colunas no resultado.
Use a forma explícita com `col()` apenas quando as colunas tiverem nomes
diferentes nos dois DataFrames.

```python
# ✅ Preferido — elimina coluna duplicada automaticamente
df_resultado = (
    df_contratos
    .join(df_clientes, on=["cpf_cnpj", "tipo_pessoa"], how="inner")
)

# ✅ Quando as colunas têm nomes diferentes
df_resultado = (
    df_contratos
    .join(
        df_propostas,
        on=(col("df_contratos.numero_contrato") == col("df_propostas.num_proposta")),
        how="left",
    )
)
```

Use `alias` apenas quando necessário para resolver ambiguidade em joins
com colunas de mesmo nome que não podem ser unificadas:

```python
df_resultado = (
    df_contratos.alias("contratos")
    .join(
        df_historico.alias("historico"),
        on=(col("contratos.id") == col("historico.id_contrato")),
        how="left",
    )
)
```

---

## Pruning inicial — renomeie colunas na leitura

Ao ler uma tabela, selecione apenas as colunas necessárias e renomeie
imediatamente para nomes legíveis. As colunas no Unity Catalog seguem
o padrão Thesaurus (mnêmonicos de baixa legibilidade) — o alias na leitura
resolve isso antes de qualquer transformação.

```python
# ❌ Leitura sem pruning — carrega colunas desnecessárias com nomes ilegíveis
df_contratos_raw = spark.read.table("catalog.schema.tb_contratos")

# ✅ Pruning inicial com renomeação imediata
df_contratos = (
    spark.read.table("catalog.schema.tb_contratos")
    .select(
        col("nucontr").alias("numero_contrato"),
        col("vcontr").alias("valor_contrato"),
        col("dtvcto").alias("data_vencimento"),
        col("cdprod").alias("codigo_produto"),
        col("stcontr").alias("status_contrato"),
    )
)
```

Após o pruning inicial, todas as transformações usam os nomes legíveis.
Nunca use o nome do mnêmonico fora do bloco de leitura.

---

## Docstrings — Google Style

Sempre use docstrings no estilo Google. Os tipos já aparecem no header da função,
por isso **nunca** inclua tipos na seção `Args` ou `Returns`.

### Função

Comece sempre com um verbo no imperativo. Descreva o quê a função faz em uma
linha. Se necessário, adicione detalhes em linhas vazias subsequentes.

Quando há `Args` e `Returns`, omita sempre os tipos — o header já os explícita:

```python
def validar_status_contrato(df: DataFrame, status_validos: list) -> DataFrame:
    """
    Aplica transformações básicas à tabela de contratos.
    
    Remove duplicatas, padroniza tipos de dado e adiciona coluna de tipo pessoa.
    
    Args:
        df: DataFrame com contratos carregados.
        status_validos: Lista de status que devem ser mantidos.
    
    Returns:
        DataFrame contendo apenas contratos com status na lista.
    """
    ...
```

### Class

Descreva o propósito da classe no imperativo. Sempre em uma linha.

```python
class ContratosJob:
    """Orquestra o pipeline de processamento de contratos até agregação por produto."""
    
    def __init__(self, spark: SparkSession) -> None:
        ...
```

### Método privado

Sempre documente. Siga o mesmo padrão de funções.

```python
def _enriquecer_faixa_valor(self, df: DataFrame) -> DataFrame:
    """
    Classifica contratos em faixas de valor.
    
    As faixas são: baixo (até R$ 10k), médio (até R$ 50k) e alto (acima de R$ 50k).
    
    Args:
        df: DataFrame de contratos com coluna valor_contrato.
    
    Returns:
        DataFrame com nova coluna faixa_valor.
    """
    ...
```

### Best Practices

- **Imperativo**: sempre use "Retorna", "Calcula", "Filtra", "Aplica", nunca "Retorna o" ou "Este método retorna"
- **Sem tipos**: tipos estão no header com type hints
- **Conciso**: máximo 2-3 linhas para função simples; uma linha está ótimo
- **Ativo**: preferir "Remove duplicatas" ao invés de "Duplicatas são removidas"
- **Contexto Databricks**: mencione colunas específicas quando relevante, ex: "Filtra carteiras ("AA", "BB")"

---

## Estrutura de um job — Pipeline Pattern

Organize cada job como uma classe. O método `executar` define a sequência
de etapas e sempre retorna o DataFrame final — quem chama decide se salva
ou usa o resultado em outro contexto.

Os métodos privados devem aparecer no arquivo **na mesma ordem em que são
invocados** pelo `executar`. Isso garante que a leitura do código espelha
a ordem de execução.

Todo método privado deve ter docstring descrevendo o que faz.

```python
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, count, lit, sum as spk_sum, when


class ContratosJob:

    def __init__(self, spark: SparkSession) -> None:
        self.spark = spark

    def executar(self) -> DataFrame:
        """Executa o pipeline completo e retorna o DataFrame resultante."""
        df = self._ler_contratos()
        df = self._filtrar_ativos(df)
        df = self._enriquecer_faixa_valor(df)
        df = self._agregar_por_produto(df)
        return df

    def _ler_contratos(self) -> DataFrame:
        """
        Lê a tabela de contratos aplicando pruning inicial.
        Renomeia as colunas do padrão Thesaurus para nomes legíveis.
        """
        return (
            self.spark.read.table("catalog.schema.tb_contratos")
            .select(
                col("nucontr").alias("numero_contrato"),
                col("vcontr").alias("valor_contrato"),
                col("cdprod").alias("codigo_produto"),
                col("stcontr").alias("status_contrato"),
                col("cpfcnpj").alias("cpf_cnpj"),
                col("tppess").alias("tipo_pessoa"),
            )
        )

    def _filtrar_ativos(self, df: DataFrame) -> DataFrame:
        """Mantém apenas contratos com status ativo."""
        return df.filter(col("status_contrato") == True)

    def _enriquecer_faixa_valor(self, df: DataFrame) -> DataFrame:
        """
        Classifica o contrato em faixas de valor:
        - baixo: até R$ 10.000
        - medio: até R$ 50.000
        - alto: acima de R$ 50.000
        """
        return (
            df
            .withColumn(
                "faixa_valor",
                when(col("valor_contrato") < 10000, lit("baixo"))
                .when(col("valor_contrato") < 50000, lit("medio"))
                .otherwise(lit("alto"))
            )
        )

    def _agregar_por_produto(self, df: DataFrame) -> DataFrame:
        """Agrega total de contratos e valor total agrupados por produto e faixa."""
        return (
            df
            .groupBy(col("codigo_produto"), col("faixa_valor"))
            .agg(
                count("*").alias("total_contratos"),
                spk_sum(col("valor_contrato")).alias("valor_total"),
            )
        )
```

### Salvando o resultado

A escrita fica fora da classe — no entrypoint do job:

```python
if __name__ == "__main__":
    from databricks.connect import DatabricksSession

    spark = DatabricksSession.builder.getOrCreate()

    df_resultado = ContratosJob(spark).executar()

    (
        df_resultado
        .write
        .mode("overwrite")
    ).saveAsTable("catalog.schema.tb_resumo_contratos")
```

### Testando a classe

Cada método privado é testável isoladamente passando um DataFrame de fixture:

```python
def test_filtrar_ativos_remove_inativos(spark):
    job = ContratosJob(spark)
    df_input = load_fixture(spark, "contratos", "input")
    df_expected = load_fixture(spark, "contratos", "expected_ativos")

    df_result = job._filtrar_ativos(df_input)

    assertDataFrameEqual(
        df_result,
        df_expected,
        ignoreColumnOrder=True,
    )
```