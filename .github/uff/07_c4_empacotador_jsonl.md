# C4 — EmpacotadorJsonl
**Async Batch Processing Pipeline — Databricks**

---

## Diagrama de classes

```mermaid
classDiagram
  class IEmpacotadorJsonl {
    <<interface>>
    +empacotar() None
  }

  class IValidavel {
    <<interface>>
    +validar_registros(registros: List) None
  }

  class EmpacotadorJsonl {
    -_tabela: TabelaControle
    -_NIVEL_COMPRESSAO: int = 1
    -_MAX_TENTATIVAS: int = 2
    -_consultar_paths_jsonl() List~str~
    -_gerar_nome_xz() str
    -_compactar(paths: List~str~, path_xz: str) None
    -_validar_xz(path_xz: str, paths_esperados: List~str~) bool
    -_deletar_jsonl(paths: List~str~) None
    +empacotar() None
    +validar_registros(registros: List) None
  }

  class EmpacotadorJsonlErro {
    <<exception>>
    +mensagem: str
    +tipo_erro: str
  }

  class Compartilhado {
    <<static>>
    +obter(chave: str) str
  }

  IEmpacotadorJsonl <|.. EmpacotadorJsonl : implements
  IValidavel <|.. EmpacotadorJsonl : implements
  EmpacotadorJsonl ..> TabelaControle : usa
  EmpacotadorJsonl ..> EmpacotadorJsonlErro : levanta
  EmpacotadorJsonl ..> Compartilhado : acessa
```

---

## Diagrama de sequência — empacotar()

```mermaid
sequenceDiagram
  participant O as Orquestrador
  participant EJ as EmpacotadorJsonl
  participant CT as TabelaControle
  participant V as Volume

  O->>EJ: empacotar()

  EJ->>CT: obter() SELECT path WHERE status = JSONL_GERADO
  CT-->>EJ: List[path_jsonl]

  EJ->>EJ: _gerar_nome_xz()
  Note over EJ: md5(timestamp + hash) → nome.xz

  loop máximo 2 tentativas
    EJ->>V: compacta List[path_jsonl] → xz/nome.xz
    Note over EJ: lzma preset = _NIVEL_COMPRESSAO (1)
    V-->>EJ: path_xz

    EJ->>EJ: _validar_xz()
    Note over EJ: abre .xz · verifica se todos os path_jsonl estão dentro

    alt .xz inválido
      EJ->>V: deleta .xz corrompido
      V-->>EJ: ok
      Note over EJ: próxima tentativa ou levanta EmpacotadorJsonlErro(RETRIAVEL)
    end
  end

  Note over EJ,CT: .xz válido — atualiza tabela e deleta .jsonl
  EJ->>CT: obter().update SET path = path_xz · status = BATCHED WHERE status = JSONL_GERADO
  CT-->>EJ: ok

  EJ->>V: deleta List[path_jsonl] em paralelo
  Note over EJ: ThreadPoolExecutor
  V-->>EJ: ok

  EJ-->>O: None
```

---

## Diagrama de sequência — validar_registros()

```mermaid
sequenceDiagram
  participant VR as ValidadorRecuperacao
  participant EJ as EmpacotadorJsonl
  participant CT as TabelaControle
  participant V as Volume

  VR->>EJ: validar_registros(List[registro])

  loop para cada registro
    EJ->>V: verifica se volume_ia/xz/{path} existe
    V-->>EJ: existe / não existe

    alt não existe
      EJ->>CT: obter().update SET status = INVALIDO WHERE id = registro.id
      CT-->>EJ: ok
    end
  end

  EJ-->>VR: List[registro_invalido]
```

---

## Decisões de design

- **Sem config** — `EmpacotadorJsonl` não tem `EmpacotadorJsonlConfig`. Recebe só a `TabelaControle`
- **Consulta `JSONL_GERADO`** — lê registros que o `GeradorJsonl` terminou de processar
- **Status atualizado pelo próprio componente** — atualiza para `BATCHED` ao final, pois é o único com contexto do `.xz`
- **`_NIVEL_COMPRESSAO = 1`** — constante interna. Nível 1 do LZMA para melhor performance
- **`_MAX_TENTATIVAS = 2`** — constante interna. Falha duas vezes indica problema estrutural
- **Validação do conteúdo do .xz** — abre e verifica se todos os path_jsonl esperados estão presentes
- **Deleção só após .xz validado** — .jsonl permanecem intactos até confirmação
- **Deleção em paralelo** — `ThreadPoolExecutor`
- **Implementa `IValidavel`** — verifica se `.xz` existe no volume para cada registro em `BATCHED`
