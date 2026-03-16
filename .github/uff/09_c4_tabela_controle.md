# C4 — TabelaControle
**Async Batch Processing Pipeline — Databricks**

---

## Diagrama de classes

```mermaid
classDiagram
  class ITabelaControle {
    <<interface>>
    +inicializar(campos_usuario: List~str~) None
    +ingerir(fonte: str, chave: str) None
    +obter() DeltaTable
  }

  class TabelaControle {
    -config: TabelaControleConfig
    -_delta: DeltaTable
    -_campos_usuario: List~str~
    -_CAMPOS_CONTROLE: List~str~
    -_tabela_existe() bool
    -_criar_tabela(schema: StructType) None
    -_montar_schema(campos_usuario: List~str~) StructType
    -_merge_batch(batch_df: DataFrame, batch_id: int) None
    +inicializar(campos_usuario: List~str~) None
    +ingerir(fonte: str, chave: str) None
    +obter() DeltaTable
  }

  class TabelaControleConfig {
    <<dataclass>>
    +nome_tabela: str
  }

  class TabelaControleErro {
    <<exception>>
    +mensagem: str
    +tipo_erro: str
  }

  class Compartilhado {
    <<static>>
    +obter(chave: str) str
  }

  ITabelaControle <|.. TabelaControle : implements
  TabelaControle ..> TabelaControleConfig : usa
  TabelaControle ..> TabelaControleErro : levanta
  TabelaControle ..> Compartilhado : acessa
```

---

## Diagrama de sequência — inicializar()

```mermaid
sequenceDiagram
  participant O as Orquestrador
  participant TC as TabelaControle
  participant DB as Delta Lake

  O->>TC: inicializar(campos_usuario)

  TC->>TC: _tabela_existe()
  TC->>DB: SHOW TABLES LIKE nome_tabela
  DB-->>TC: existe / não existe

  alt tabela não existe
    TC->>TC: _montar_schema(campos_usuario)
    Note over TC: campos_usuario + _CAMPOS_CONTROLE
    Note over TC: status · batch_id · path · data_atualizacao
    Note over TC: erro · total_tentativas · maior_status
    TC->>DB: CREATE TABLE nome_tabela schema USING DELTA
    DB-->>TC: ok
  end

  TC-->>O: None
```

---

## Diagrama de sequência — ingerir()

```mermaid
sequenceDiagram
  participant O as Orquestrador
  participant TC as TabelaControle
  participant F as Tabela Fonte
  participant DB as Control Table

  O->>TC: ingerir(fonte, chave)

  TC->>F: readStream.format("delta").table(fonte)
  F-->>TC: stream

  TC->>TC: writeStream.foreachBatch(_merge_batch)
  Note over TC: trigger(availableNow=True)
  Note over TC: awaitTermination()

  loop para cada micro-batch
    TC->>DB: merge ON controle.{chave} = novos.{chave}
    Note over DB: whenNotMatched → INSERT
    Note over DB: status=PENDING · batch_id=null · path=null
    Note over DB: data_atualizacao=now() · erro=null
    Note over DB: total_tentativas=0 · maior_status=null
    Note over DB: whenMatched → ignorar
    DB-->>TC: ok
  end

  TC-->>O: None
```

---

## Campos de controle obrigatórios

Adicionados automaticamente pelo `inicializar()` independente dos campos do usuário:

| Campo | Tipo | Default | Descrição |
|-------|------|---------|-----------|
| `status` | string | `PENDING` | Etapa atual do registro |
| `batch_id` | string | null | Campo de trabalho — ID do batch |
| `path` | string | null | Campo de trabalho — path do arquivo atual |
| `data_atualizacao` | timestamp | now() | Timestamp da última atualização |
| `erro` | string | null | Motivo do erro se houver |
| `total_tentativas` | int | 0 | Contador acumulado de falhas de recuperação |
| `maior_status` | string | null | Status mais avançado já atingido |

---

## Decisões de design

- **`inicializar()` é idempotente** — verifica se tabela existe antes de criar. Pode ser chamado múltiplas vezes sem efeito colateral
- **`ingerir()` usa `trigger(availableNow=True)`** — processa todos os registros novos disponíveis e encerra. Adequado para pipelines com execução diária
- **`ingerir()` usa merge com `whenNotMatched`** — registros já existentes são ignorados, nunca duplicados
- **`obter()` retorna a instância `DeltaTable`** — componentes usam para fazer seus próprios updates com contexto específico
- **`nome_tabela` só em `TabelaControleConfig`** — nenhum outro componente conhece o nome da tabela
- **`_CAMPOS_CONTROLE` como constante interna** — lista de campos obrigatórios não é configurável
- **`schema_wks` via `Compartilhado`** — obtido de `Compartilhado.obter("schema_wks")`, não hardcoded
