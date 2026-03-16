# C4 — GeradorJsonl
**Async Batch Processing Pipeline — Databricks**

---

## Diagrama de classes

```mermaid
classDiagram
  class IGeradorJsonl {
    <<interface>>
    +preparar() None
  }

  class IValidavel {
    <<interface>>
    +validar_registros(registros: List) None
  }

  class GeradorJsonl {
    -config: GeradorJsonlConfig
    -_tabela: TabelaControle
    -_consultar_pendentes() DataFrame
    -_atribuir_batch_ids(df: DataFrame) None
    -_obter_batch_ids() List~str~
    -_consultar_por_batch_id(batch_id: str) DataFrame
    -_remover_campos_controle(df: DataFrame) DataFrame
    -_gerar_jsonl(df: DataFrame, batch_id: str) None
    -_limpar_batch_ids() None
    +preparar() None
    +validar_registros(registros: List) None
  }

  class GeradorJsonlConfig {
    <<dataclass>>
    +tamanho_batch: int = 40000
  }

  class GeradorJsonlErro {
    <<exception>>
    +mensagem: str
    +tipo_erro: str
  }

  class Compartilhado {
    <<static>>
    +obter(chave: str) str
  }

  IGeradorJsonl <|.. GeradorJsonl : implements
  IValidavel <|.. GeradorJsonl : implements
  GeradorJsonl ..> GeradorJsonlConfig : usa
  GeradorJsonl ..> TabelaControle : usa
  GeradorJsonl ..> GeradorJsonlErro : levanta
  GeradorJsonl ..> Compartilhado : acessa
```

---

## Diagrama de sequência — preparar()

```mermaid
sequenceDiagram
  participant O as Orquestrador
  participant GJ as GeradorJsonl
  participant CT as TabelaControle
  participant V as Volume

  O->>GJ: preparar()

  Note over GJ,CT: fase 1 — atribuição de batch_ids
  GJ->>CT: obter().alias("t").update WHERE status = PENDING
  Note over GJ: batch_id por faixa de N · md5(timestamp + índice)
  CT-->>GJ: ok · dados materializados
  GJ->>CT: obter() SELECT DISTINCT batch_id WHERE status = PENDING
  CT-->>GJ: List[batch_id]

  Note over GJ,V: fase 2 — geração dos .jsonl
  loop para cada batch_id
    GJ->>CT: obter() SELECT WHERE batch_id = X
    CT-->>GJ: DataFrame do batch
    GJ->>GJ: _remover_campos_controle()
    GJ->>V: df.write.json(volume_ia/jsonl/batch_id)
    V-->>GJ: path_jsonl
    GJ->>CT: obter().update SET path = path_jsonl WHERE batch_id = X
    CT-->>GJ: ok
  end

  Note over GJ,CT: limpeza e status
  GJ->>CT: obter().update SET batch_id = null · status = JSONL_GERADO WHERE status = PENDING
  CT-->>GJ: ok

  GJ-->>O: None
```

---

## Diagrama de sequência — validar_registros()

```mermaid
sequenceDiagram
  participant VR as ValidadorRecuperacao
  participant GJ as GeradorJsonl
  participant CT as TabelaControle
  participant V as Volume

  VR->>GJ: validar_registros(List[registro])

  loop para cada registro
    GJ->>V: verifica se volume_ia/jsonl/{batch_id}/data.jsonl existe
    V-->>GJ: existe / não existe

    alt não existe
      GJ->>CT: obter().update SET status = INVALIDO WHERE id = registro.id
      CT-->>GJ: ok
    end
  end

  GJ-->>VR: List[registro_invalido]
```

---

## Decisões de design

- **Sem `collect()`** — todas as operações são distribuídas via Spark
- **Duas fases separadas** — fase 1 materializa os batch_ids antes da fase 2 iniciar, evitando lazy evaluation do Spark
- **`batch_id` limpo ao finalizar** — campo de trabalho temporário, null após `preparar()` concluir
- **Status atualizado pelo próprio componente** — `GeradorJsonl` atualiza para `JSONL_GERADO` ao final, pois é o único com contexto completo
- **`caminho_volume` via `Compartilhado.obter("volume_ia")`** — subpath `/jsonl/{batch_id}`
- **Sem `nome_tabela` na config** — acessa a tabela via `TabelaControle` injetada no construtor
- **Implementa `IValidavel`** — verifica se `.jsonl` existe no volume para cada registro em `JSONL_GERADO`
