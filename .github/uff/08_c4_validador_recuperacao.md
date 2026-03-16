# C4 — ValidadorRecuperacao
**Async Batch Processing Pipeline — Databricks**

---

## Diagrama de classes

```mermaid
classDiagram
  class IValidavel {
    <<interface>>
    +validar_registros(registros: List) None
  }

  class ValidadorRecuperacao {
    -_tabela: TabelaControle
    -_STATUS_ACIONAVEIS: List~str~
    -_validadores: Dict~str, IValidavel~
    -_consultar_status_adiantados() Map~str, List~
    -_resetar_para_pending(registro) None
    -_marcar_erro_global(registro) None
    +validar_status() None
  }

  class ValidadorRecuperacaoErro {
    <<exception>>
    +mensagem: str
    +tipo_erro: str
  }

  class GeradorJsonl {
    +validar_registros(registros: List) None
  }

  class EmpacotadorJsonl {
    +validar_registros(registros: List) None
  }

  class EnviadorStorage {
    +validar_registros(registros: List) None
  }

  class SolicitadorProcessamento {
    +validar_registros(registros: List) None
  }

  IValidavel <|.. GeradorJsonl : implements
  IValidavel <|.. EmpacotadorJsonl : implements
  IValidavel <|.. EnviadorStorage : implements
  IValidavel <|.. SolicitadorProcessamento : implements
  ValidadorRecuperacao ..> TabelaControle : usa
  ValidadorRecuperacao ..> ValidadorRecuperacaoErro : levanta
  ValidadorRecuperacao --> IValidavel : chama por status
```

---

## Diagrama de sequência

```mermaid
sequenceDiagram
  participant O as Orquestrador
  participant VR as ValidadorRecuperacao
  participant C as Componente (IValidavel)
  participant CT as TabelaControle

  O->>VR: validar_status()

  VR->>CT: obter() SELECT WHERE status IN (JSONL_GERADO, BATCHED, UPLOADED, PROCESSING)
  CT-->>VR: Map[status → List[registro]]

  loop para cada status encontrado
    VR->>C: validar_registros(List[registro])
    Note over C: verifica integridade no volume/API · marca INVALIDO se falhou
    C-->>VR: List[registro_invalido]
  end

  loop para cada registro inválido
    VR->>VR: status_atual > maior_status? → atualiza maior_status
    VR->>CT: obter().update SET total_tentativas = total_tentativas + 1
    CT-->>VR: ok

    alt total_tentativas >= 2 AND status_atual == maior_status
      VR->>CT: obter().update SET status=ERRO_GLOBAL · erro="Intervenção manual necessária"
      CT-->>VR: ok
    else
      VR->>CT: obter().update SET status=PENDING · maior_status=maior_status_atualizado
      CT-->>VR: ok
    end
  end

  VR-->>O: None
```

---

## Mapeamento status → componente validador

| Status | Componente validador | O que verifica |
|--------|---------------------|----------------|
| `JSONL_GERADO` | `GeradorJsonl` | .jsonl existe no volume |
| `BATCHED` | `EmpacotadorJsonl` | .xz existe no volume |
| `UPLOADED` | `EnviadorStorage` | .xz existe no Azure |
| `PROCESSING` | `SolicitadorProcessamento` | job_id existe na API |

---

## Regra de ERRO_GLOBAL

```
total_tentativas >= 2 AND status_atual == maior_status → ERRO_GLOBAL
```

---

## Decisões de design

- **Sem config** — `ValidadorRecuperacao` recebe só a `TabelaControle` e os componentes `IValidavel`
- **`IValidavel`** — cada componente conhece suas próprias regras de integridade
- **`INVALIDO` é temporário** — nunca persiste entre execuções
- **`ERRO_GLOBAL` é permanente** — requer intervenção manual
- **`maior_status` nunca regride** — garante detecção de reincidência na etapa mais avançada
- **`total_tentativas` nunca reseta** — acumula todas as falhas
