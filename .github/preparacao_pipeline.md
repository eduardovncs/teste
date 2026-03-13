# PreparacaoPipeline

Documentação técnica da primeira etapa do pipeline de processamento de IA em batch.

---

## Índice

1. [Visão geral](#1-visão-geral)
2. [Responsabilidades](#2-responsabilidades)
3. [Arquitetura e classes](#3-arquitetura-e-classes)
4. [Schema da tabela Delta](#4-schema-da-tabela-delta)
5. [Status do registro](#5-status-do-registro)
6. [Fluxo de execução](#6-fluxo-de-execução)
7. [Idempotência e retomada](#7-idempotência-e-retomada)
8. [Extensibilidade](#8-extensibilidade)
9. [Tratamento de erros parciais](#9-tratamento-de-erros-parciais)
10. [Exemplo de uso](#10-exemplo-de-uso)

---

## 1. Visão geral

O `PreparacaoPipeline` é a primeira etapa do pipeline de IA. Sua responsabilidade começa na leitura dos registros pendentes da tabela Delta e termina na geração de um arquivo `.xz` pronto para envio ao container.

Ele **não realiza nenhuma chamada externa** — não envia arquivos, não consulta APIs, não aguarda respostas. Tudo que ele produz é local, no Volume do Databricks.

```
Tabela Delta (registros pendentes)
        ↓
PreparacaoPipeline
        ↓
Arquivo .xz no Volume
```

As etapas seguintes (`EnvioPipeline`, `SubmissaoPipeline`, `PollingPipeline`, `ResultadoPipeline`) consomem o `.xz` produzido aqui e são responsabilidades de outros módulos.

---

## 2. Responsabilidades

O que esta etapa **faz**:

- Lê registros com `status = PENDENTE` ou `status = ERRO_BATCH` da tabela Delta
- Valida se o DataFrame possui todas as colunas obrigatórias do cenário
- Divide o DataFrame em batches de tamanho configurável
- Monta um arquivo JSONL por batch com o formato esperado pela API
- Compacta todos os JSONLs em um único arquivo `.xz` com hash único
- Atualiza o `status` de cada registro na tabela Delta ao longo do processo
- Detecta e isola falhas parciais sem interromper os demais batches

O que esta etapa **não faz**:

- Não envia o `.xz` para nenhum destino externo
- Não realiza chamadas à API de processamento
- Não aguarda respostas externas
- Não gera o `batch_id_interno` nem o `batch_id_cloud`

---

## 3. Arquitetura e classes

O pipeline é composto por 8 classes com responsabilidades bem definidas:

```
PreparacaoPipeline          ← orquestrador
├── PipelineConfig          ← configurações do cenário
├── PipelineStateManager    ← controle de estado e retomada
├── SchemaValidator         ← validação das colunas do DataFrame
├── DataExtractor           ← leitura da tabela Delta
├── BatchSplitter           ← divisão em batches
├── JsonlBuilder            ← montagem dos arquivos JSONL (extensível)
└── Compressor              ← compactação em .xz
```

---

### 3.1 PipelineConfig

Centraliza todas as configurações do cenário. É passado para todas as classes como dependência — nenhuma classe lê configurações de outras fontes.

```python
@dataclass
class PipelineConfig:
    tamanho_batch: int   # quantidade de registros por JSONL
    volume_path:   str   # caminho raiz no Volume do Databricks
```

**Responsabilidade:** guardar parâmetros. Nenhuma lógica de negócio.

---

### 3.2 PipelineStateManager

Inspeciona a tabela Delta antes de qualquer processamento e decide se o pipeline deve **iniciar do zero** ou **retomar** de onde parou.

```python
class PipelineStateManager:
    def inspecionar(self) -> InspecaoResultado
    def retomar_ou_iniciar(self) -> Caminho
    def atualizar_status(ids: List[str], status: StatusRegistro) -> None
```

**Lógica de decisão:**

```
Achou registros PREPARANDO?
└── JSONL pode estar incompleto → volta para PENDENTE e reinicia

Achou registros ENVIANDO_CONTAINER?
└── responsabilidade do EnvioPipeline → não toca

Achou registros PROCESSANDO_INTERNO ou PROCESSANDO_CLOUD?
└── responsabilidade do PollingPipeline → não toca

Achou só PENDENTE ou ERRO_BATCH?
└── inicia o PreparacaoPipeline normalmente
```

**Responsabilidade:** única classe que lê e escreve status na tabela Delta dentro desta etapa.

---

### 3.3 SchemaValidator

Valida se o DataFrame possui todas as colunas obrigatórias antes de qualquer processamento. Recebe o `schema_esperado` diretamente do `JsonlBuilder` — quem sabe quais colunas são necessárias é quem vai montar o JSONL.

```python
class SchemaValidator:
    def validar(df: DataFrame) -> bool
    def colunas_faltantes(df: DataFrame) -> List[str]
```

**Comportamento em caso de falha:**

```
Colunas faltantes encontradas
└── lança SchemaInvalidoError com lista das colunas ausentes
    → pipeline interrompido antes de qualquer processamento
    → nenhum status é alterado na tabela
```

**Responsabilidade:** garantir contrato de entrada. Falha rápido antes de processar qualquer linha.

---

### 3.4 DataExtractor

Lê a tabela Delta e retorna apenas os registros elegíveis para processamento.

```python
class DataExtractor:
    def extrair() -> DataFrame
    def filtrar_pendentes() -> DataFrame
```

**Filtro aplicado:**

```sql
SELECT * FROM tabela
WHERE status IN ('PENDENTE', 'ERRO_BATCH')
```

**Responsabilidade:** leitura e filtragem. Não altera status.

---

### 3.5 BatchSplitter

Divide o DataFrame em pedaços de tamanho `config.tamanho_batch`.

```python
class BatchSplitter:
    def dividir(df: DataFrame) -> List[DataFrame]
    def total_batches(df: DataFrame) -> int
```

**Exemplo:**

```
DataFrame com 2.500 registros + tamanho_batch = 1.000
→ batch_0: registros 0    a 999
→ batch_1: registros 1000 a 1999
→ batch_2: registros 2000 a 2499  (último batch menor)
```

**Responsabilidade:** divisão apenas. Não lê nem escreve na tabela.

---

### 3.6 JsonlBuilder

Classe abstrata que define o contrato de montagem dos arquivos JSONL. Implementa o padrão **Template Method** — o fluxo de construção é fixo, mas os pontos de extensão podem ser sobrescritos por cada cenário.

```python
class JsonlBuilder(ABC):
    schema_esperado: List[str]          # colunas obrigatórias do cenário

    def construir(batches: List[DataFrame]) -> List[Path]   # fluxo fixo — não sobrescrever
    def montar_registro(row) -> dict    # sobrescrevível — montagem do JSON de cada linha
    def validar_row(row) -> bool        # sobrescrevível — validação linha a linha
```

**Fluxo interno de `construir()`:**

```
Para cada batch:
    Para cada linha:
        1. validar_row(row)       → linha inválida? → status = DADO_INCOMPLETO, pula
        2. montar_registro(row)   → monta o dict
        3. escreve linha no JSONL
    Salva o arquivo .jsonl no Volume
Retorna lista de paths dos JSONLs gerados
```

**DefaultJsonlBuilder** — implementação padrão para a maioria dos cenários:

```python
class DefaultJsonlBuilder(JsonlBuilder):
    schema_esperado = ["prompt", "modelo", "temperature", "max_tokens", "status",
                       "batch_id_local", "atualizado_em"]

    def montar_registro(row) -> dict:
        return {
            "custom_id": row["id_registro"],   # coluna de identificação do cenário
            "body": {
                "model":       row["modelo"],
                "max_tokens":  row["max_tokens"],
                "temperature": row["temperature"],
                "messages": [
                    { "role": "user", "content": row["prompt"] }
                ]
            }
        }

    def validar_row(row) -> bool:
        return all([
            row["prompt"] is not None and len(row["prompt"]) > 0,
            row["modelo"] is not None,
            row["max_tokens"] > 0,
        ])
```

**Responsabilidade:** montagem dos arquivos JSONL. Cada arquivo corresponde a um batch.

---

### 3.7 Compressor

Recebe a lista de paths dos JSONLs, compacta tudo em um único `.xz` e remove os JSONLs originais após verificar a integridade do arquivo gerado.

```python
class Compressor:
    def compactar(paths: List[Path]) -> Path
    def verificar_integridade() -> bool
    def limpar_jsonls() -> None
    def _gerar_hash() -> str            # privado — gerado internamente
```

**Geração do nome do arquivo:**

O nome do `.xz` é gerado internamente pela classe a partir de um hash único. Nenhum código externo define ou conhece esse nome antes da compactação.

```
hash = md5(volume_path + timestamp_iso + total_arquivos)
nome = f"batch_{hash[:8]}.xz"

Exemplo: classificacao_contratos_a3f8c2d1.xz
```

**Fluxo interno:**

```
1. Compacta todos os JSONLs → arquivo .xz
2. verificar_integridade()  → consegue descompactar?
   └── falhou → lança CompactacaoError (JSONLs preservados)
   └── ok     → limpar_jsonls() → apaga os JSONLs
3. Retorna Path do .xz
```

**Responsabilidade:** empacotamento final. Os JSONLs só são removidos após confirmação de integridade.

---

### 3.8 PreparacaoPipeline

Orquestrador da etapa. Não contém lógica de negócio — apenas coordena a execução das classes na ordem correta e trata falhas parciais.

```python
class PreparacaoPipeline:
    def executar() -> Path
    def _tratar_erro_batch(ids_erro: List[str]) -> None
```

**Fluxo de `executar()`:**

```
1. PipelineStateManager.retomar_ou_iniciar()
2. DataExtractor.extrair()
3. SchemaValidator.validar(df)
4. BatchSplitter.dividir(df)
5. Para cada batch:
   a. atualizar_status(ids, PREPARANDO)
   b. JsonlBuilder.construir(batch)
      └── linha inválida  → atualizar_status(id, DADO_INCOMPLETO)
      └── sucesso         → atualizar_status(ids, BATCH_PREPARADO)
      └── falha técnica   → _tratar_erro_batch(ids_erro) → ERRO_BATCH
6. Compressor.compactar(paths_gerados)
7. Retorna Path do .xz
```

**Responsabilidade:** coordenação. Falhas em batches individuais não interrompem os demais.

---

## 4. Schema da tabela Delta

A tabela Delta que serve de origem e destino do pipeline possui duas camadas de colunas.

### Colunas base — obrigatórias em todos os cenários

| Coluna | Tipo | Descrição |
|---|---|---|
| `status` | string | Status atual do registro (`StatusRegistro`) |
| `batch_id_local` | string | ID do batch gerado internamente (ex: `batch_0003`) |
| `path_container` | string | Caminho retornado pelo endpoint de upload |
| `batch_id_interno` | string | ID retornado pelo endpoint de submissão |
| `batch_id_cloud` | string | ID retornado quando a cloud assume o processamento |
| `atualizado_em` | timestamp | Data e hora da última atualização de status |
| `erro` | string | Descrição do erro, se houver |

### Colunas de cenário — definidas por cada processo

Cada cenário estende o schema base com suas próprias colunas via `RegistroSchema`:

```python
class RegistroSchema:
    """Schema base — colunas obrigatórias em todos os cenários."""
    COLUNAS_BASE = ["status", "batch_id_local", "path_container",
                    "batch_id_interno", "batch_id_cloud",
                    "atualizado_em", "erro"]

class ContratoSchema(RegistroSchema):
    """Schema para o cenário de classificação de contratos."""
    COLUNAS_CENARIO = ["id_contrato", "prompt", "modelo", "temperature", "max_tokens"]

class AudioSchema(RegistroSchema):
    """Schema para o cenário de transcrição de áudio."""
    COLUNAS_CENARIO = ["id_audio", "prompt", "modelo", "temperature", "max_tokens", "idioma"]
```

O `SchemaValidator` valida as duas camadas — base e cenário — antes de iniciar o processamento.

---

## 5. Status do registro

Cada registro na tabela Delta possui um `status` que reflete exatamente em qual etapa do pipeline ele se encontra.

### Etapa 1 — Preparação (escopo desta documentação)

| Status | Significado |
|---|---|
| `PENDENTE` | Ainda não processado — elegível para a próxima execução |
| `PREPARANDO` | Incluído em um batch, JSONL sendo montado |
| `DADO_INCOMPLETO` | Falhou na validação linha a linha — problema no dado, não na infraestrutura |
| `BATCH_PREPARADO` | JSONL gerado com sucesso, aguarda compactação e envio |
| `ERRO_BATCH` | Falha técnica ao gerar o JSONL (ex: erro de I/O, disco, permissão) |

> **Diferença importante:** `DADO_INCOMPLETO` é problema do dado — quem criou o registro precisa corrigir na origem e voltar o status para `PENDENTE` manualmente. `ERRO_BATCH` é problema técnico — o pipeline tentará reprocessar automaticamente na próxima execução.

### Etapa 2 — Envio ao container

| Status | Significado |
|---|---|
| `ENVIANDO_CONTAINER` | Arquivo `.xz` sendo enviado |
| `CONTAINER_ENVIADO` | Upload confirmado, `path_container` salvo |
| `ERRO_ENVIO_CONTAINER` | Falha no upload — retorna para `BATCH_PREPARADO` |

### Etapas 3 e 4 — Processamento

| Status | Significado |
|---|---|
| `PROCESSANDO_INTERNO` | `batch_id_interno` recebido, aguardando processamento |
| `ERRO_PROCESSAMENTO` | Falha no processamento interno |
| `PROCESSANDO_CLOUD` | `batch_id_cloud` recebido, modelo sendo aplicado |
| `ERRO_CLOUD` | Falha no processamento cloud |

### Etapa 5 — Resultado

| Status | Significado |
|---|---|
| `CONCLUIDO` | Resultado recebido e tabela atualizada com sucesso |
| `ERRO_RESULTADO` | Falha ao buscar ou salvar o resultado |

---

## 6. Fluxo de execução

Fluxo completo de um registro desde `PENDENTE` até o `.xz` gerado:

```
Registro: CTR_001, status = PENDENTE
        │
        ▼
PipelineStateManager.inspecionar()
→ encontrou PENDENTE → inicia normalmente
        │
        ▼
DataExtractor.extrair()
→ DataFrame com todos os registros PENDENTE e ERRO_BATCH
        │
        ▼
SchemaValidator.validar(df)
→ todas as colunas presentes → ok
        │
        ▼
BatchSplitter.dividir(df)
→ CTR_001 vai para o batch_0
        │
        ▼
atualizar_status([CTR_001, ...], PREPARANDO)
→ CTR_001: status = PREPARANDO
        │
        ▼
JsonlBuilder.construir(batch_0)
→ validar_row(CTR_001) → ok
→ montar_registro(CTR_001):
  {
    "custom_id": "CTR_001",
    "body": {
      "model": "gpt-4o",
      "max_tokens": 500,
      "temperature": 0.2,
      "messages": [{"role": "user", "content": "Classifique..."}]
    }
  }
→ salvo em: /Volume/.../batches/classificacao_contratos_batch_0000.jsonl
        │
        ▼
atualizar_status([CTR_001, ...], BATCH_PREPARADO)
→ CTR_001: status = BATCH_PREPARADO
        │
        ▼
[repete para todos os batches]
        │
        ▼
Compressor.compactar([batch_0000.jsonl, ..., batch_0399.jsonl])
→ _gerar_hash() → "a3f8c2d1"
→ compacta → classificacao_contratos_a3f8c2d1.xz
→ verificar_integridade() → ok
→ limpar_jsonls() → remove os 400 JSONLs
→ retorna Path(".../classificacao_contratos_a3f8c2d1.xz")
```

---

## 7. Idempotência e retomada

O pipeline pode ser interrompido a qualquer momento e retomado com segurança. O `PipelineStateManager` garante que nenhum registro seja processado duas vezes e que nenhum trabalho seja perdido.

### Cenários de falha e comportamento na retomada

**Falha durante `PREPARANDO`:**
```
Situação:  pipeline morreu enquanto montava um JSONL
Problema:  o JSONL pode estar incompleto ou corrompido
Ação:      registros PREPARANDO → voltam para PENDENTE
           JSONL incompleto é descartado
           batch reprocessado do zero na próxima execução
```

**Falha durante compactação:**
```
Situação:  pipeline morreu enquanto compactava os JSONLs
Problema:  .xz pode estar incompleto
Ação:      registros BATCH_PREPARADO são mantidos como estão
           Compressor.verificar_integridade() detecta o .xz inválido
           compactação reiniciada com os JSONLs que ainda existem no Volume
```

**Falha em outro pipeline (ENVIANDO_CONTAINER em diante):**
```
Situação:  registro já passou desta etapa
Ação:      PreparacaoPipeline não toca nesses registros
           são responsabilidade do EnvioPipeline em diante
```

### Proteção contra reprocessamento de dados inválidos

Registros com `DADO_INCOMPLETO` **não são retornados** pelo `DataExtractor` nas execuções seguintes — o filtro busca apenas `PENDENTE` e `ERRO_BATCH`. Para reprocessar, o dado precisa ser corrigido na origem e o status voltado manualmente para `PENDENTE`.

---

## 8. Extensibilidade

O pipeline foi desenhado para funcionar com qualquer cenário de IA que siga o padrão de envio em batch. A extensão acontece em dois pontos:

### 8.1 Novo schema de colunas

```python
class AudioSchema(RegistroSchema):
    COLUNAS_CENARIO = ["id_audio", "prompt", "modelo",
                       "temperature", "max_tokens", "idioma"]
```

### 8.2 Novo formato de JSONL

Sobrescreva apenas o método que precisa mudar:

```python
class AudioJsonlBuilder(DefaultJsonlBuilder):

    schema_esperado = AudioSchema.COLUNAS_BASE + AudioSchema.COLUNAS_CENARIO

    def montar_registro(self, row) -> dict:
        base = super().montar_registro(row)  # herda o padrão
        base["body"]["language"] = row["idioma"]  # adiciona campo extra
        return base
```

### 8.3 Usando o builder customizado

```python
config = PipelineConfig(
    tamanho_batch = 500,
    volume_path   = "/Volumes/workspace/default/audios/transcricao",
)

pipeline = PreparacaoPipeline(
    config  = config,
    builder = AudioJsonlBuilder(config)   # injeta o builder do cenário
)

path_xz = pipeline.executar()
```

O orquestrador, o splitter, o compressor e o state manager **não precisam de nenhuma alteração** entre cenários.

---

## 9. Tratamento de erros parciais

Um batch pode falhar sem interromper os demais. O método `_tratar_erro_batch()` isola a falha:

```
Cenário: 400 batches, batch_0003 falhou ao gerar o JSONL

batch_0000 → BATCH_PREPARADO  ✅
batch_0001 → BATCH_PREPARADO  ✅
batch_0002 → BATCH_PREPARADO  ✅
batch_0003 → ERRO_BATCH       ❌  ← isolado, não interrompe os demais
batch_0004 → BATCH_PREPARADO  ✅
...
batch_0399 → BATCH_PREPARADO  ✅
```

Os registros do batch_0003 ficam com `status = ERRO_BATCH`. Na próxima execução do pipeline, apenas esses registros são reprocessados — os demais já estão em `BATCH_PREPARADO` e seguem para o `EnvioPipeline`.

O `.xz` é gerado com os 399 batches bem-sucedidos. O batch com erro será compactado em uma execução futura.

---

## 10. Exemplo de uso

### Cenário padrão — classificação de contratos

```python
from pipeline import (
    PipelineConfig,
    PreparacaoPipeline,
    DefaultJsonlBuilder,
)

config = PipelineConfig(
    tamanho_batch = 1000,
    volume_path   = "/Volumes/workspace/default/audios/contratos",
)

pipeline = PreparacaoPipeline(
    config  = config,
    builder = DefaultJsonlBuilder(config)
)

path_xz = pipeline.executar()
print(f"Arquivo gerado: {path_xz}")
# → /Volumes/.../contratos/batch_a3f8c2d1.xz
```

### Cenário customizado — transcrição de áudio

```python
from pipeline import PipelineConfig, PreparacaoPipeline
from meus_builders import AudioJsonlBuilder

config = PipelineConfig(
    tamanho_batch = 500,
    volume_path   = "/Volumes/workspace/default/audios/transcricao",
)

pipeline = PreparacaoPipeline(
    config  = config,
    builder = AudioJsonlBuilder(config)
)

path_xz = pipeline.executar()
```

### Verificando o estado antes de executar

```python
from pipeline import PipelineConfig, PipelineStateManager

config  = PipelineConfig(
    tamanho_batch = 1000,
    volume_path   = "/Volumes/workspace/default/audios/contratos",
)
manager = PipelineStateManager(config)

resultado = manager.inspecionar()
print(resultado)
# {
#   "pendentes":          39800,
#   "preparando":         0,
#   "dado_incompleto":    150,
#   "batch_preparado":    200,
#   "erro_batch":         1000,
#   "em_outras_etapas":   0,
# }
```

---

## 11. Casos de teste

Cobertura esperada para cada classe. Os testes seguem o padrão **Arrange / Act / Assert** e usam `pytest` com `pyspark` para os casos que envolvem DataFrame.

---

### 11.1 PipelineConfig

| # | Cenário | Entrada | Resultado esperado |
|---|---|---|---|
| 1 | Configuração válida | `tamanho_batch=1000`, `volume_path="/Volumes/..."` | Objeto criado sem erros |
| 2 | `tamanho_batch` zero | `tamanho_batch=0` | `ValidationError` |
| 3 | `tamanho_batch` negativo | `tamanho_batch=-1` | `ValidationError` |
| 4 | `volume_path` vazio | `volume_path=""` | `ValidationError` |

```python
def test_pipeline_config_valido():
    config = PipelineConfig(tamanho_batch=1000, volume_path="/Volumes/teste")
    assert config.tamanho_batch == 1000
    assert config.volume_path == "/Volumes/teste"

def test_pipeline_config_tamanho_batch_zero():
    with pytest.raises(ValidationError):
        PipelineConfig(tamanho_batch=0, volume_path="/Volumes/teste")

def test_pipeline_config_tamanho_batch_negativo():
    with pytest.raises(ValidationError):
        PipelineConfig(tamanho_batch=-1, volume_path="/Volumes/teste")

def test_pipeline_config_volume_path_vazio():
    with pytest.raises(ValidationError):
        PipelineConfig(tamanho_batch=1000, volume_path="")
```

---

### 11.2 SchemaValidator

| # | Cenário | Entrada | Resultado esperado |
|---|---|---|---|
| 1 | Todas as colunas presentes | DataFrame com todas as colunas do schema | `True` |
| 2 | Coluna obrigatória ausente | DataFrame sem a coluna `status` | `False` + lista com `"status"` |
| 3 | Múltiplas colunas ausentes | DataFrame sem `status` e `prompt` | `False` + lista com ambas |
| 4 | DataFrame vazio mas com schema correto | DataFrame vazio com colunas certas | `True` |
| 5 | Colunas extras além do schema | DataFrame com colunas a mais | `True` — colunas extras são ignoradas |

```python
def test_schema_validator_valido(spark):
    df = spark.createDataFrame([], schema="status STRING, batch_id_local STRING, prompt STRING, modelo STRING")
    validator = SchemaValidator(schema_esperado=["status", "batch_id_local", "prompt", "modelo"])
    assert validator.validar(df) is True

def test_schema_validator_coluna_ausente(spark):
    df = spark.createDataFrame([], schema="batch_id_local STRING, prompt STRING")
    validator = SchemaValidator(schema_esperado=["status", "batch_id_local", "prompt"])
    assert validator.validar(df) is False
    assert "status" in validator.colunas_faltantes(df)

def test_schema_validator_multiplas_ausentes(spark):
    df = spark.createDataFrame([], schema="batch_id_local STRING")
    validator = SchemaValidator(schema_esperado=["status", "batch_id_local", "prompt"])
    faltantes = validator.colunas_faltantes(df)
    assert "status" in faltantes
    assert "prompt" in faltantes

def test_schema_validator_colunas_extras_ignoradas(spark):
    df = spark.createDataFrame([], schema="status STRING, batch_id_local STRING, coluna_extra STRING")
    validator = SchemaValidator(schema_esperado=["status", "batch_id_local"])
    assert validator.validar(df) is True
```

---

### 11.3 DataExtractor

| # | Cenário | Entrada | Resultado esperado |
|---|---|---|---|
| 1 | Tabela com registros PENDENTE | Tabela com mix de status | Retorna apenas PENDENTE |
| 2 | Tabela com registros ERRO_BATCH | Tabela com mix de status | Retorna PENDENTE + ERRO_BATCH |
| 3 | Tabela sem registros elegíveis | Todos CONCLUIDO ou DADO_INCOMPLETO | DataFrame vazio |
| 4 | Tabela completamente vazia | Tabela sem linhas | DataFrame vazio sem erro |

```python
def test_extractor_retorna_pendentes(spark, mock_delta_table):
    mock_delta_table([
        ("CTR_001", "PENDENTE"),
        ("CTR_002", "CONCLUIDO"),
        ("CTR_003", "PENDENTE"),
    ])
    extractor = DataExtractor(config)
    df = extractor.extrair()
    ids = [row["id"] for row in df.collect()]
    assert "CTR_001" in ids
    assert "CTR_003" in ids
    assert "CTR_002" not in ids

def test_extractor_retorna_erro_batch(spark, mock_delta_table):
    mock_delta_table([
        ("CTR_001", "ERRO_BATCH"),
        ("CTR_002", "DADO_INCOMPLETO"),
    ])
    extractor = DataExtractor(config)
    df = extractor.extrair()
    ids = [row["id"] for row in df.collect()]
    assert "CTR_001" in ids
    assert "CTR_002" not in ids   # DADO_INCOMPLETO não é elegível

def test_extractor_sem_elegíveis_retorna_vazio(spark, mock_delta_table):
    mock_delta_table([("CTR_001", "CONCLUIDO"), ("CTR_002", "DADO_INCOMPLETO")])
    df = DataExtractor(config).extrair()
    assert df.count() == 0

def test_extractor_tabela_vazia(spark, mock_delta_table):
    mock_delta_table([])
    df = DataExtractor(config).extrair()
    assert df.count() == 0
```

---

### 11.4 BatchSplitter

| # | Cenário | Entrada | Resultado esperado |
|---|---|---|---|
| 1 | Total divisível exato | 3000 registros, batch=1000 | 3 batches de 1000 cada |
| 2 | Total não divisível | 2500 registros, batch=1000 | 2 batches de 1000 + 1 de 500 |
| 3 | Total menor que o batch | 300 registros, batch=1000 | 1 batch com 300 registros |
| 4 | Total exatamente 1 registro | 1 registro, batch=1000 | 1 batch com 1 registro |
| 5 | `total_batches()` correto | 2500 registros, batch=1000 | Retorna `3` |

```python
def test_splitter_divisao_exata(spark):
    df = gerar_dataframe(spark, total=3000)
    batches = BatchSplitter(config).dividir(df)
    assert len(batches) == 3
    assert all(b.count() == 1000 for b in batches)

def test_splitter_ultimo_batch_menor(spark):
    df = gerar_dataframe(spark, total=2500)
    batches = BatchSplitter(config).dividir(df)
    assert len(batches) == 3
    assert batches[2].count() == 500

def test_splitter_total_menor_que_batch(spark):
    df = gerar_dataframe(spark, total=300)
    batches = BatchSplitter(config).dividir(df)
    assert len(batches) == 1
    assert batches[0].count() == 300

def test_splitter_total_batches(spark):
    df = gerar_dataframe(spark, total=2500)
    assert BatchSplitter(config).total_batches(df) == 3
```

---

### 11.5 JsonlBuilder / DefaultJsonlBuilder

| # | Cenário | Entrada | Resultado esperado |
|---|---|---|---|
| 1 | Linha válida | Row com todos os campos preenchidos | Dict com `custom_id` e `body` corretos |
| 2 | Linha com `prompt` nulo | `prompt=None` | `validar_row` retorna `False` → status `DADO_INCOMPLETO` |
| 3 | Linha com `max_tokens` zero | `max_tokens=0` | `validar_row` retorna `False` → status `DADO_INCOMPLETO` |
| 4 | Batch com mix de linhas válidas e inválidas | 8 válidas + 2 inválidas | JSONL com 8 linhas, 2 marcados como `DADO_INCOMPLETO` |
| 5 | Batch completamente válido | 1000 linhas válidas | JSONL com 1000 linhas gerado corretamente |
| 6 | Arquivo JSONL gerado é válido | Qualquer batch válido | Cada linha é um JSON válido e parseável |
| 7 | `CustomJsonlBuilder` sobrescreve campo | Override de `montar_registro` com campo extra | Campo extra presente no dict gerado |

```python
def test_builder_monta_registro_valido():
    row = Row(id_contrato="CTR_001", prompt="Classifique...",
              modelo="gpt-4o", temperature=0.2, max_tokens=500)
    builder = DefaultJsonlBuilder(config)
    resultado = builder.montar_registro(row)
    assert resultado["custom_id"] == "CTR_001"
    assert resultado["body"]["model"] == "gpt-4o"
    assert resultado["body"]["messages"][0]["content"] == "Classifique..."

def test_builder_valida_prompt_nulo():
    row = Row(id_contrato="CTR_001", prompt=None, modelo="gpt-4o",
              temperature=0.2, max_tokens=500)
    assert DefaultJsonlBuilder(config).validar_row(row) is False

def test_builder_valida_max_tokens_zero():
    row = Row(id_contrato="CTR_001", prompt="Classifique...",
              modelo="gpt-4o", temperature=0.2, max_tokens=0)
    assert DefaultJsonlBuilder(config).validar_row(row) is False

def test_builder_linhas_invalidas_marcadas_dado_incompleto(spark, tmp_path):
    batch = gerar_batch(spark, validas=8, invalidas=2)
    builder = DefaultJsonlBuilder(config)
    paths = builder.construir([batch])
    # JSONL deve ter só 8 linhas
    with open(paths[0]) as f:
        linhas = f.readlines()
    assert len(linhas) == 8

def test_builder_jsonl_linhas_validas(spark, tmp_path):
    batch = gerar_batch(spark, validas=10, invalidas=0)
    paths = DefaultJsonlBuilder(config).construir([batch])
    with open(paths[0]) as f:
        for linha in f:
            json.loads(linha)   # não deve lançar exceção

def test_custom_builder_adiciona_campo_extra():
    class CustomBuilder(DefaultJsonlBuilder):
        def montar_registro(self, row):
            base = super().montar_registro(row)
            base["body"]["language"] = row["idioma"]
            return base

    row = Row(id_audio="AUD_001", prompt="Transcreva...", modelo="gpt-4o",
              temperature=0.0, max_tokens=1000, idioma="pt-br")
    resultado = CustomBuilder(config).montar_registro(row)
    assert resultado["body"]["language"] == "pt-br"
```

---

### 11.6 Compressor

| # | Cenário | Entrada | Resultado esperado |
|---|---|---|---|
| 1 | Compactação bem-sucedida | Lista de paths de JSONLs válidos | Arquivo `.xz` gerado no Volume |
| 2 | Hash único por execução | Duas execuções com inputs diferentes | Hashes diferentes |
| 3 | Hash consistente | Mesmos inputs | Mesmo hash |
| 4 | Integridade verificada | `.xz` gerado | `verificar_integridade()` retorna `True` |
| 5 | JSONLs removidos após compactação | Após `compactar()` bem-sucedido | JSONLs originais não existem mais no Volume |
| 6 | JSONLs preservados em caso de falha | `.xz` corrompido | JSONLs ainda existem |
| 7 | Lista de paths vazia | `paths=[]` | `CompactacaoError` |

```python
def test_compressor_gera_xz(tmp_path, jsonls_fixture):
    compressor = Compressor(config)
    path_xz = compressor.compactar(jsonls_fixture)
    assert path_xz.exists()
    assert path_xz.suffix == ".xz"

def test_compressor_hash_unico(tmp_path, jsonls_fixture_a, jsonls_fixture_b):
    hash_a = Compressor(config)._gerar_hash()
    hash_b = Compressor(config)._gerar_hash()
    assert hash_a != hash_b   # timestamp diferente garante unicidade

def test_compressor_integridade(tmp_path, jsonls_fixture):
    compressor = Compressor(config)
    compressor.compactar(jsonls_fixture)
    assert compressor.verificar_integridade() is True

def test_compressor_remove_jsonls(tmp_path, jsonls_fixture):
    paths_originais = list(jsonls_fixture)
    Compressor(config).compactar(jsonls_fixture)
    for p in paths_originais:
        assert not p.exists()

def test_compressor_preserva_jsonls_em_falha(tmp_path, jsonls_fixture, mocker):
    mocker.patch.object(Compressor, "verificar_integridade", return_value=False)
    paths_originais = list(jsonls_fixture)
    with pytest.raises(CompactacaoError):
        Compressor(config).compactar(jsonls_fixture)
    for p in paths_originais:
        assert p.exists()   # JSONLs preservados

def test_compressor_paths_vazios():
    with pytest.raises(CompactacaoError):
        Compressor(config).compactar([])
```

---

### 11.7 PipelineStateManager

| # | Cenário | Entrada | Resultado esperado |
|---|---|---|---|
| 1 | Tabela só com PENDENTE | Registros PENDENTE | `retomar_ou_iniciar()` → `INICIAR` |
| 2 | Tabela com PREPARANDO | Registros PREPARANDO | Volta para PENDENTE e retorna `INICIAR` |
| 3 | Tabela com ENVIANDO_CONTAINER | Registros nessa etapa | `retomar_ou_iniciar()` → `OUTRA_ETAPA` — não toca |
| 4 | Tabela com PROCESSANDO_CLOUD | Registros nessa etapa | `retomar_ou_iniciar()` → `OUTRA_ETAPA` — não toca |
| 5 | `inspecionar()` retorna contagens corretas | Mix de status | Contagens batem com os dados da tabela |
| 6 | `atualizar_status()` persiste na tabela | Lista de ids + novo status | Registros com status atualizado na Delta |

```python
def test_state_manager_inicia_com_pendentes(spark, mock_delta_table):
    mock_delta_table([("CTR_001", "PENDENTE"), ("CTR_002", "PENDENTE")])
    manager = PipelineStateManager(config)
    assert manager.retomar_ou_iniciar() == Caminho.INICIAR

def test_state_manager_volta_preparando_para_pendente(spark, mock_delta_table):
    mock_delta_table([("CTR_001", "PREPARANDO"), ("CTR_002", "PREPARANDO")])
    manager = PipelineStateManager(config)
    manager.retomar_ou_iniciar()
    df = spark.read.table("tabela")
    status = [row["status"] for row in df.collect()]
    assert all(s == "PENDENTE" for s in status)

def test_state_manager_nao_toca_outras_etapas(spark, mock_delta_table):
    mock_delta_table([("CTR_001", "ENVIANDO_CONTAINER")])
    manager = PipelineStateManager(config)
    assert manager.retomar_ou_iniciar() == Caminho.OUTRA_ETAPA

def test_state_manager_inspecionar_contagens(spark, mock_delta_table):
    mock_delta_table([
        ("CTR_001", "PENDENTE"),
        ("CTR_002", "PENDENTE"),
        ("CTR_003", "ERRO_BATCH"),
        ("CTR_004", "DADO_INCOMPLETO"),
    ])
    resultado = PipelineStateManager(config).inspecionar()
    assert resultado["pendentes"] == 2
    assert resultado["erro_batch"] == 1
    assert resultado["dado_incompleto"] == 1

def test_state_manager_atualizar_status(spark, mock_delta_table):
    mock_delta_table([("CTR_001", "PENDENTE"), ("CTR_002", "PENDENTE")])
    manager = PipelineStateManager(config)
    manager.atualizar_status(["CTR_001"], StatusRegistro.PREPARANDO)
    df = spark.read.table("tabela")
    row = df.filter("id = 'CTR_001'").collect()[0]
    assert row["status"] == "PREPARANDO"
```

---

### 11.8 PreparacaoPipeline — integração

Os testes de integração cobrem o pipeline completo de ponta a ponta, verificando a interação entre todas as classes.

| # | Cenário | Entrada | Resultado esperado |
|---|---|---|---|
| 1 | Fluxo feliz completo | 100 registros válidos | `.xz` gerado, todos os registros em `BATCH_PREPARADO` |
| 2 | Schema inválido | DataFrame sem coluna obrigatória | `SchemaInvalidoError` antes de qualquer processamento — status inalterado |
| 3 | Batch com dados inválidos | Mix de linhas válidas e inválidas | Linhas inválidas em `DADO_INCOMPLETO`, válidas em `BATCH_PREPARADO` |
| 4 | Falha técnica em um batch | Simula erro de I/O no batch 2 | Batch 2 em `ERRO_BATCH`, demais em `BATCH_PREPARADO`, `.xz` gerado sem o batch 2 |
| 5 | Retomada após PREPARANDO | Registros travados em PREPARANDO | Voltam para PENDENTE e são reprocessados corretamente |
| 6 | Tabela sem elegíveis | Todos CONCLUIDO | Pipeline encerra sem processar nada, sem erro |

```python
def test_pipeline_fluxo_feliz(spark, tmp_path, mock_delta_table):
    mock_delta_table(gerar_registros(100, status="PENDENTE"))
    pipeline = PreparacaoPipeline(
        config  = PipelineConfig(tamanho_batch=50, volume_path=str(tmp_path)),
        builder = DefaultJsonlBuilder(config)
    )
    path_xz = pipeline.executar()
    assert path_xz.exists()
    df = spark.read.table("tabela")
    assert df.filter("status = 'BATCH_PREPARADO'").count() == 100

def test_pipeline_schema_invalido_nao_altera_status(spark, tmp_path, mock_delta_table):
    mock_delta_table(gerar_registros(10, status="PENDENTE", omitir_coluna="prompt"))
    pipeline = PreparacaoPipeline(config=config, builder=DefaultJsonlBuilder(config))
    with pytest.raises(SchemaInvalidoError):
        pipeline.executar()
    df = spark.read.table("tabela")
    assert df.filter("status = 'PENDENTE'").count() == 10   # status inalterado

def test_pipeline_dados_invalidos_marcados(spark, tmp_path, mock_delta_table):
    mock_delta_table(
        gerar_registros(8, status="PENDENTE") +
        gerar_registros(2, status="PENDENTE", prompt=None)
    )
    pipeline = PreparacaoPipeline(config=config, builder=DefaultJsonlBuilder(config))
    pipeline.executar()
    df = spark.read.table("tabela")
    assert df.filter("status = 'BATCH_PREPARADO'").count() == 8
    assert df.filter("status = 'DADO_INCOMPLETO'").count() == 2

def test_pipeline_falha_tecnica_isola_batch(spark, tmp_path, mock_delta_table, mocker):
    mock_delta_table(gerar_registros(100, status="PENDENTE"))
    # Simula falha de I/O no segundo batch
    mocker.patch.object(DefaultJsonlBuilder, "construir",
                        side_effect=lambda b: _falha_no_batch(b, indice=1))
    pipeline = PreparacaoPipeline(
        config  = PipelineConfig(tamanho_batch=50, volume_path=str(tmp_path)),
        builder = DefaultJsonlBuilder(config)
    )
    path_xz = pipeline.executar()
    df = spark.read.table("tabela")
    assert df.filter("status = 'BATCH_PREPARADO'").count() == 50
    assert df.filter("status = 'ERRO_BATCH'").count() == 50
    assert path_xz.exists()   # .xz gerado com o batch que funcionou

def test_pipeline_retomada_apos_preparando(spark, tmp_path, mock_delta_table):
    mock_delta_table(gerar_registros(10, status="PREPARANDO"))
    pipeline = PreparacaoPipeline(config=config, builder=DefaultJsonlBuilder(config))
    path_xz = pipeline.executar()
    assert path_xz.exists()
    df = spark.read.table("tabela")
    assert df.filter("status = 'BATCH_PREPARADO'").count() == 10

def test_pipeline_sem_elegiveis_encerra_sem_erro(spark, tmp_path, mock_delta_table):
    mock_delta_table(gerar_registros(10, status="CONCLUIDO"))
    pipeline = PreparacaoPipeline(config=config, builder=DefaultJsonlBuilder(config))
    resultado = pipeline.executar()
    assert resultado is None   # nada a processar, sem erro
```

---



Após a execução do `PreparacaoPipeline`, o arquivo `.xz` está disponível no Volume e os registros estão com `status = BATCH_PREPARADO`. A continuidade do fluxo é responsabilidade do `EnvioPipeline`, documentado separadamente.

```
PreparacaoPipeline  →  .xz no Volume + registros BATCH_PREPARADO
EnvioPipeline       →  path_container salvo + registros CONTAINER_ENVIADO
SubmissaoPipeline   →  batch_id_interno salvo + registros PROCESSANDO_INTERNO
PollingPipeline     →  batch_id_cloud salvo + registros PROCESSANDO_CLOUD
ResultadoPipeline   →  resultado salvo + registros CONCLUIDO
```
